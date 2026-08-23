from collections import Counter,defaultdict
from datetime import date
from ..pipeline.features import build_features

def _day(value):
    try: return date.fromisoformat(str(value)[:10])
    except (TypeError,ValueError): return None

def _trends(store, products, orders, items):
    dates=[_day(o.get("order_date")) for o in orders.values()]; dates=[d for d in dates if d]
    if not dates: return {"reference_date":None,"products":{},"categories":{}}
    reference=max(dates); windows={"recent_30":(reference,30),"previous_30":(reference,60)}; product_period=defaultdict(Counter); category_period=defaultdict(Counter)
    for item in items:
        order=orders.get(item.get("order_id")); product=products.get(item.get("product_id")); order_date=_day(order.get("order_date")) if order else None
        if not product or not order_date: continue
        age=(reference-order_date).days; period="recent_30" if 0<=age<30 else "previous_30" if 30<=age<60 else "older"
        qty=float(item.get("quantity",0)); product_period[product["product_id"]][period]+=qty; category_period[product["category"]][period]+=qty
    def growth(counter):
        recent=counter.get("recent_30",0); previous=counter.get("previous_30",0); return round((recent-previous)/previous,3) if previous else (1.0 if recent else 0.0)
    return {"reference_date":str(reference),"products":{pid:{**dict(values),"growth":growth(values)} for pid,values in product_period.items()},"categories":{cat:{**dict(values),"growth":growth(values)} for cat,values in category_period.items()}}

def _rfm(store, orders):
    dates=[_day(o.get("order_date")) for o in orders.values()]; dates=[d for d in dates if d]; reference=max(dates) if dates else None; grouped=defaultdict(lambda:{"dates":[] ,"orders":0,"monetary":0.0})
    for order in orders.values():
        if order.get("order_status") and order["order_status"]!="Completed": continue
        customer=grouped[order.get("customer_id")]; order_date=_day(order.get("order_date"));
        if order_date: customer["dates"].append(order_date)
        customer["orders"]+=1; customer["monetary"]+=float(order.get("order_total",0))
    return {cid:{"recency_days":(reference-max(v["dates"])).days if reference and v["dates"] else None,"frequency":v["orders"],"monetary":round(v["monetary"],2)} for cid,v in grouped.items()}

def _co_purchase_metrics(features, orders):
    order_count=max(len(orders),1); product_orders=Counter();
    for ids in features.get("order_products",{}).values():
        for pid in set(ids): product_orders[pid]+=1
    metrics={}
    for (left,right),count in features["co_purchases"].items():
        metrics[f"{left}+{right}"]={"count":count,"support":round(count/order_count,4),"confidence_left":round(count/max(product_orders[left],1),4),"confidence_right":round(count/max(product_orders[right],1),4)}
    return metrics

def build_analytics(store):
    features=build_features(store); products={p["product_id"]:p for p in store.collections["products"]}; orders={o["order_id"]:o for o in store.collections["orders"]}; categories=Counter(); customer_categories=defaultdict(Counter)
    for item in store.collections["order_items"]:
        pid=item.get("product_id"); oid=item.get("order_id")
        if pid not in products or oid not in orders: continue
        category=products[pid]["category"]; qty=item.get("quantity",0); categories[category]+=qty; customer_categories[orders[oid]["customer_id"]][category]+=qty
    return {"product_sales":features["sales"],"product_revenue":features["revenue"],"category_sales":categories,"customer_categories":customer_categories,"customer_products":features["customer_products"],"co_purchases":features["co_purchases"],"co_purchase_metrics":_co_purchase_metrics(features,orders),"trends":_trends(store,products,orders,store.collections["order_items"]),"rfm":_rfm(store,orders),"inventory":store.collections["inventory"]}
