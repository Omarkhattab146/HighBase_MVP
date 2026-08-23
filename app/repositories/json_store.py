import json
from pathlib import Path
from ..models import DataStore

COLLECTIONS=["products","customers","orders","order_items","inventory"]

class JsonStoreRepository:
    def __init__(self,path="data"): self.path=Path(path)
    def load(self):
        return DataStore({name:json.loads((self.path/f"{name}.json").read_text()) if (self.path/f"{name}.json").exists() else [] for name in COLLECTIONS})
    def save(self,store):
        self.path.mkdir(parents=True,exist_ok=True)
        for name,rows in store.collections.items(): (self.path/f"{name}.json").write_text(json.dumps(rows,indent=2))
    def save_snapshot(self,store,name):
        JsonStoreRepository(self.path/name).save(store)
    def ping(self):
        return self.path.exists() or self.path.mkdir(parents=True,exist_ok=True) is None
    def business_overview(self):
        return {name: len(rows) for name, rows in self.load().collections.items()}
