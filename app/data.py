from .repositories.json_store import JsonStoreRepository
def load_store(path="data"):
    return JsonStoreRepository(path).load()
def write_store(store, path="data"):
    JsonStoreRepository(path).save(store)
def seed_store(path="data"):
    from scripts.generate_dummy_data import generate
    s=generate(); write_store(s,path); return s
