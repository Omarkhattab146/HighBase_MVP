from datetime import date,timedelta
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import random
from app.models import DataStore
def generate(seed=42):
    r=random.Random(seed); cats={"Beverages":["Water","Juice","Coffee"],"Snacks":["Chips","Biscuits","Chocolate"],"Dairy":["Milk","Cheese"],"Pantry":["Rice","Pasta","Cooking Oil"]}; products=[]; pid=1001
    for cat,subs in cats.items():
        for sub in subs:
            for n in range(2):
                products.append({"product_id":f"P{pid}","name":f"Highbase {sub} {n+1}","category":cat,"subcategory":sub,"brand":r.choice(["FreshDay","Gulf Choice","Highbase Select"]),"price":round(r.uniform(1,18),2),"currency":"BHD","availability":"Out of Stock" if pid in (1004,1017) else "In Stock","product_url":f"https://highbase.example/products/P{pid}"}); pid+=1
    types=["Restaurant","Cafe","Mini Market","Catering","Hotel"]; customers=[{"customer_id":f"C{i:03}","shop_name":f"{t} {i:02}","business_type":t,"city":r.choice(["Manama","Riffa","Muharraq"]),"business_size":r.choice(["Small","Medium","Large"]),"customer_since":"2026-01-01"} for i,t in enumerate(types*4,1)]
    bias={"Restaurant":["Beverages","Pantry","Dairy"],"Cafe":["Beverages","Dairy","Snacks"],"Mini Market":["Beverages","Snacks","Pantry"],"Catering":["Pantry","Beverages","Dairy"],"Hotel":["Beverages","Dairy","Pantry"]}; orders=[]; items=[]; oid=5001; start=date(2026,1,1)
    for day in range(150):
        for c in r.sample(customers,r.randint(2,7)):
            if r.random()>.55: continue
            cat=r.choice(bias[c["business_type"]]); chosen=r.sample([p for p in products if p["category"]==cat],2); order_id=f"O{oid}"; oid+=1; total=0
            for p in chosen:
                qty=r.randint(3,15); line=round(qty*p["price"],2); total+=line; items.append({"order_id":order_id,"product_id":p["product_id"],"quantity":qty,"unit_price":p["price"],"total_price":line})
            orders.append({"order_id":order_id,"customer_id":c["customer_id"],"order_date":str(start+timedelta(days=day)),"order_status":"Completed","order_total":round(total,2)})
    inventory=[{"product_id":p["product_id"],"stock_quantity":0 if p["availability"]=="Out of Stock" else r.randint(20,200),"reorder_level":30,"availability":p["availability"],"snapshot_date":"2026-06-01"} for p in products]
    products.append(products[0].copy()); products[1]["price"]=None; products[2]["category"]=" Beverages "; products[3]["price"]=999.99
    return DataStore({"products":products,"customers":customers,"orders":orders,"order_items":items,"inventory":inventory})
if __name__=="__main__":
    from app.data import write_store
    write_store(generate()); print("Generated data/ JSON collections")
