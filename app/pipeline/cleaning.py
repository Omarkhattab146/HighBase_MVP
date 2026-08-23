"""Ordered product cleaning pipeline.

The stages are deliberately explicit so each transformation can be inspected:
deduplicate → remove price outliers → handle missing values → encode categories.
"""
import re
from numbers import Number
from statistics import median
from ..models import QualityReport

def _outlier_ids(rows):
    values=[row.get("price") for row in rows if isinstance(row.get("price"),Number)]
    if len(values)<4: return set()
    ordered=sorted(values); q1=ordered[len(ordered)//4]; q3=ordered[(len(ordered)*3)//4]; iqr=q3-q1; lower=q1-1.5*iqr; upper=q3+1.5*iqr
    return {row.get("product_id") for row in rows if isinstance(row.get("price"),Number) and (row["price"]<lower or row["price"]>upper or row["price"]<0 or row["price"]>100)}

def _slug(value):
    return re.sub(r"[^a-z0-9]+","_",str(value).lower()).strip("_")

def _encode_categories(rows):
    fields=("category","subcategory","brand"); maps={field:{value:index for index,value in enumerate(sorted({str(row.get(field,"Unknown")) for row in rows}),1)} for field in fields}
    for row in rows:
        row["category_code"]=maps["category"][str(row["category"])]
        row["subcategory_code"]=maps["subcategory"][str(row["subcategory"])]
        row["brand_code"]=maps["brand"][str(row["brand"])]
        row["category_one_hot"]={f"category_{_slug(value)}":int(value==row["category"]) for value in maps["category"]}
    return maps

def clean_products(store):
    rows=store.collections["products"]; report=QualityReport(processed=len(rows))
    # Stage 1: remove duplicate business keys before calculating distributions.
    unique=[]; seen=set(); duplicate_ids=[]
    for raw in rows:
        pid=raw.get("product_id")
        if not pid or pid in seen: report.duplicates+=1; duplicate_ids.append(str(pid)); continue
        seen.add(pid); unique.append(dict(raw))
    # Stage 2: remove records with invalid/extreme prices. This is intentional
    # deletion for the MVP because recommendations must not use bad prices.
    outlier_ids=_outlier_ids(unique); filtered=[row for row in unique if row.get("product_id") not in outlier_ids]; report.outliers=len(outlier_ids)
    # Stage 3: normalize values and impute missing prices with the clean median.
    prices=[row["price"] for row in filtered if isinstance(row.get("price"),Number) and 0<=row["price"]<=100]; fallback=float(median(prices)) if prices else 0.0
    cleaned=[]
    for product in filtered:
        product["name"]=(product.get("name") or "Unknown product").strip(); product["category"]=(product.get("category") or "Unknown").strip().title(); product["subcategory"]=(product.get("subcategory") or "Unknown").strip().title(); product["brand"]=(product.get("brand") or "Unknown").strip(); product["quality_flags"]=[]
        if product.get("price") is None: report.missing+=1; product["price"]=fallback; product["quality_flags"].append("missing_price_imputed_median")
        cleaned.append(product)
    # Stage 4: encode categorical features for downstream analytics/ML.
    maps=_encode_categories(cleaned) if cleaned else {}
    # Referential-integrity stage: deleting a product must not leave order
    # items pointing at a product that no longer exists in the clean dataset.
    valid_product_ids={product["product_id"] for product in cleaned}
    before_items=len(store.collections.get("order_items",[]))
    store.collections["order_items"]=[item for item in store.collections.get("order_items",[]) if item.get("product_id") in valid_product_ids]
    store.metadata["category_encoding_maps"]=maps
    store.metadata["rejected_ids"]=duplicate_ids+sorted(str(pid) for pid in outlier_ids)
    store.metadata["cleaning"]={"orphan_order_items_removed":before_items-len(store.collections["order_items"]),"outliers_deleted":report.outliers,"duplicates_removed":report.duplicates}
    store.collections["products"]=cleaned; report.cleaned=len(cleaned); report.rejected=report.duplicates+report.outliers
    return report
