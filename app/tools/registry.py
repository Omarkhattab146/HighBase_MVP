import json
class ToolRegistry:
    def __init__(self, tools): self.tools=tools
    def definitions(self):
        schemas={'search_products':{'query':{'type':'string'},'category':{'type':'string'},'max_price':{'type':'number'},'limit':{'type':'integer'}},'check_inventory':{'product_ids':{'type':'array','items':{'type':'string'}},'query':{'type':'string'}},'get_product_details':{'product_id':{'type':'string'}},'get_analytics_summary':{'category':{'type':'string'},'product':{'type':'string'}},'get_offers':{'query':{'type':'string'},'category':{'type':'string'},'limit':{'type':'integer'}},'get_trending_products':{'category':{'type':'string'},'limit':{'type':'integer'}},'get_database_overview':{}}
        return [{'type':'function','function':{'name':n,'description':f'Read-only {n} business data','parameters':{'type':'object','properties':p,'additionalProperties':False}}} for n,p in schemas.items()]
    def call(self,name,args):
        fn=getattr(self.tools,name,None)
        if not fn or name.startswith('_'): raise ValueError('Unsupported read-only tool')
        return fn(**json.loads(args) if isinstance(args,str) else args)
