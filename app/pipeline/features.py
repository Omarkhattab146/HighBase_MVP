from collections import Counter,defaultdict

def build_features(store):
    products={p["product_id"]:p for p in store.collections["products"]}; orders={o["order_id"]:o for o in store.collections["orders"]}; sales=Counter(); revenue=Counter(); customer_products=defaultdict(Counter); pairs=Counter(); orders_to_products=defaultdict(list)
    for item in store.collections["order_items"]:
        pid=item.get("product_id"); oid=item.get("order_id")
        if pid not in products or oid not in orders: continue
        qty=float(item.get("quantity",0)); sales[pid]+=qty; revenue[pid]+=float(item.get("total_price",0)); customer_products[orders[oid]["customer_id"]][pid]+=qty; orders_to_products[oid].append(pid)
    for ids in orders_to_products.values():
        unique=list(dict.fromkeys(ids))
        for i,left in enumerate(unique):
            for right in unique[i+1:]: pairs[tuple(sorted((left,right)))]+=1
    total=max(sum(sales.values()),1)
    for product in store.collections["products"]:
        pid=product["product_id"]; product["features"]={"units_sold":sales[pid],"revenue":round(revenue[pid],2),"sales_share":round(sales[pid]/total,4),"co_purchase_count":sum(v for pair,v in pairs.items() if pid in pair),"available":product.get("availability")=="In Stock","price_band":"budget" if (product.get("price") or 0)<=5 else "standard"}
    return {"sales":sales,"revenue":revenue,"customer_products":customer_products,"co_purchases":pairs,"order_products":orders_to_products}
