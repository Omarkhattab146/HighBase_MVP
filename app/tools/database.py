from datetime import date
from ..analytics.service import build_analytics

class DatabaseTools:
    def __init__(self, store, repository=None): self.store=store; self.repository=repository
    def search_products(self, query="", category=None, max_price=None, limit=10):
        query=(query or '').lower(); limit=max(1,min(int(limit or 10),20)); rows=[]
        inventory={x.get('product_id'):x for x in self.store.collections.get('inventory',[])}
        for p in self.store.collections.get('products',[]):
            if query and query not in f"{p.get('name','')} {p.get('category','')}".lower(): continue
            if category and p.get('category','').lower()!=category.lower(): continue
            if max_price is not None and float(p.get('price') or 0)>float(max_price): continue
            stock=inventory.get(p.get('product_id'),{}); rows.append(self._product(p,stock))
        return rows[:limit]
    def check_inventory(self, product_ids=None, query=""):
        ids=set(product_ids or []); products={p.get('product_id'):p for p in self.store.collections.get('products',[])}; rows=[]
        for stock in self.store.collections.get('inventory',[]):
            if ids and stock.get('product_id') not in ids: continue
            p=products.get(stock.get('product_id'),{}); text=f"{p.get('name','')} {p.get('category','')}".lower()
            if query and query.lower() not in text: continue
            rows.append({'product_id':stock.get('product_id'),'name':p.get('name'),'availability':stock.get('availability'),'stock_quantity':stock.get('stock_quantity')})
        return rows[:20]
    def get_product_details(self, product_id): return next((x for x in self.search_products(limit=20) if x['product_id']==product_id), None)
    def get_analytics_summary(self, category=None, product=None):
        a=build_analytics(self.store); result={'top_products':a['product_sales'].most_common(10),'category_sales':dict(a['category_sales']),'trends':a['trends']}
        if category: result['category_sales']={category:a['category_sales'].get(category,0)}
        if product: result['product_sales']={product:a['product_sales'].get(product,0)}
        return result
    def get_offers(self, query="", category=None, limit=10):
        # Fetch a wider candidate set before filtering; an offer may not be in the
        # first ``limit`` catalog rows.
        candidates=self.search_products(query, category, limit=20)
        return [row for row in candidates if row.get('offer')][:max(1,min(int(limit or 10),20))]
    def get_trending_products(self, category=None, limit=10):
        rows=self.search_products(category=category, limit=20)
        return sorted([row for row in rows if row.get('trend_growth') is not None], key=lambda x:x['trend_growth'], reverse=True)[:max(1,min(int(limit or 10),20))]
    def get_database_overview(self):
        counts=self.repository.business_overview() if self.repository else {k:len(v) for k,v in self.store.collections.items()}
        return {'collections':counts}
    def _product(self,p,stock):
        analytics=build_analytics(self.store); pid=p.get('product_id'); growth=analytics['trends']['products'].get(pid,{}).get('growth')
        price=p.get('price'); offer=None
        if isinstance(price,(int,float)) and pid and int(pid[1:]) % 5 == 0:
            offer={'offer_price':round(price*.9,2),'discount_percent':10.0,'valid_until':'2026-12-31','eligibility':'public','description':'10% off selected HIGHBASE products'}
        availability=stock.get('availability') or 'Unknown'
        if stock.get('stock_quantity') is not None and stock.get('stock_quantity') <= 0: availability='Out of Stock'
        return {'product_id':pid,'name':p.get('name'),'category':p.get('category'),'price':price,'currency':p.get('currency','BHD'),'availability':availability,'stock_quantity':stock.get('stock_quantity'),'product_url':p.get('product_url'),'offer':offer,'trend_growth':growth,'trend_label':'Trending' if growth and growth>0 else None,'data_freshness':stock.get('snapshot_date')}
