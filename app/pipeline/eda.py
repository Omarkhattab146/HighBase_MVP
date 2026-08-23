"""Read-only exploratory data analysis for raw MVP collections."""
from collections import Counter
from numbers import Number

def _profile(rows):
    fields=sorted({key for row in rows for key in row})
    missing={field:sum(row.get(field) is None or row.get(field)=="" for row in rows) for field in fields}
    categorical={}; numeric={}
    for field in fields:
        values=[row.get(field) for row in rows if row.get(field) is not None]
        if values and all(isinstance(value,Number) and not isinstance(value,bool) for value in values):
            numeric[field]={"min":min(values),"max":max(values),"mean":round(sum(values)/len(values),2)}
        elif values:
            categorical[field]=dict(Counter(map(str,values)).most_common(10))
    return {"rows":len(rows),"fields":fields,"missing_by_field":missing,"numeric":numeric,"categorical":categorical}

def explore(store):
    """Profile raw data without mutating the store."""
    collections={name:_profile(rows) for name,rows in store.collections.items()}
    products=store.collections.get("products",[]); product_ids=[p.get("product_id") for p in products]
    duplicates=[pid for pid,count in Counter(product_ids).items() if pid is not None and count>1]
    outliers=[p.get("product_id") for p in products if isinstance(p.get("price"),Number) and (p["price"]<0 or p["price"]>100)]
    known_products=set(product_ids); order_ids={o.get("order_id") for o in store.collections.get("orders",[])}
    orphan_items=sum(1 for item in store.collections.get("order_items",[]) if item.get("order_id") not in order_ids or item.get("product_id") not in known_products)
    prices=[p.get("price") for p in products if isinstance(p.get("price"),Number)]
    return {"collections":collections,"quality":{"duplicate_product_ids":duplicates,"price_outlier_product_ids":outliers,"orphan_order_items":orphan_items},"numeric_ranges":{"product_price":{"min":min(prices) if prices else None,"max":max(prices) if prices else None}}}
