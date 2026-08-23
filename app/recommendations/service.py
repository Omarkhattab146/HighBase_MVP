from dataclasses import dataclass
from ..models import Recommendation
from ..analytics.service import build_analytics

BUSINESS_CATEGORIES={"restaurant":"beverages pantry dairy","cafe":"beverages dairy snacks","mini market":"beverages snacks pantry","catering":"pantry beverages dairy","hotel":"beverages dairy pantry"}

@dataclass(frozen=True)
class RankingConfig:
    sales_weight: float=0.10
    business_affinity_weight: float=4.0
    query_match_weight: float=6.0
    trend_weight: float=2.0
    customer_history_weight: float=3.0

def rank_products(store, request, config=RankingConfig()):
    analytics=build_analytics(store); customers={c["customer_id"]:c for c in store.collections["customers"]}; customer=customers.get(request.customer_id,{})
    inventory={item.get("product_id"):item for item in store.collections.get("inventory",[])}; business=(request.business_type or customer.get("business_type") or "").lower(); query=request.query.lower(); preferred=BUSINESS_CATEGORIES.get(business,""); ranked=[]
    history=analytics["customer_products"].get(request.customer_id,{}) if request.customer_id else {}
    seen_products=set()
    for product in store.collections["products"]:
        if product.get("product_id") in seen_products:
            continue
        seen_products.add(product.get("product_id"))
        stock=inventory.get(product.get("product_id"),{}); available=product.get("availability")=="In Stock" and stock.get("availability","In Stock")!="Out of Stock" and stock.get("stock_quantity",1)>0
        if not available or not isinstance(product.get("price"),(int,float)) or (request.max_price and product["price"]>request.max_price): continue
        pid=product["product_id"]; category=product["category"].lower(); sales=float(analytics["product_sales"].get(pid,0)); trend=analytics["trends"]["products"].get(pid,{}).get("growth",0.0); score=sales*config.sales_weight; reasons=[]; evidence={"historical_units":sales,"trend_growth":trend,"availability":1.0}
        if category in preferred: score+=config.business_affinity_weight; reasons.append(f"popular for {business}s"); evidence["business_affinity"]=1.0
        if pid in history: score+=config.customer_history_weight; reasons.append("purchased by this customer before"); evidence["customer_history_units"]=float(history[pid])
        if query and any(term in query for term in (category,product["subcategory"].lower(),product["name"].lower())): score+=config.query_match_weight; reasons.append("matches your request"); evidence["query_match"]=1.0
        if trend>0: score+=min(trend,2)*config.trend_weight; reasons.append("trending in recent sales"); evidence["trend_bonus"]=round(min(trend,2)*config.trend_weight,2)
        reasons.append("available now")
        ranked.append(Recommendation(product_id=pid,name=product["name"],category=product["category"],price=product["price"],currency=product["currency"],availability="In Stock",product_url=product["product_url"],score=round(score,2),reasons=reasons,evidence=evidence))
    return sorted(ranked,key=lambda item:(item.score,item.product_id),reverse=True)[:request.limit]
