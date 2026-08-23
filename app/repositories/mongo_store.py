"""MongoDB adapter implementing the same store boundary as the JSON adapter.

The client is created lazily by the application container, so importing the
module never requires a running MongoDB instance.
"""
from ..models import DataStore

COLLECTIONS=("products","customers","orders","order_items","inventory")

class MongoStoreRepository:
    def __init__(self, uri, database):
        from pymongo import MongoClient
        self.client=MongoClient(uri, serverSelectionTimeoutMS=2000)
        self.database=self.client[database]
    def ping(self):
        try: self.client.admin.command("ping"); return True
        except Exception: return False
    def load(self):
        return DataStore({name:list(self.database[name].find({}, {"_id":0})) for name in COLLECTIONS})
    def save(self, store):
        for name in COLLECTIONS:
            collection=self.database[name]; collection.delete_many({})
            rows=store.collections.get(name,[])
            if rows: collection.insert_many(rows)
    def ensure_indexes(self):
        keys={"products":"product_id","customers":"customer_id","orders":"order_id"}
        for collection,field in keys.items(): self.database[collection].create_index(field, unique=True)
    def business_overview(self):
        return {name: self.database[name].estimated_document_count() for name in COLLECTIONS}
