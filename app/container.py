"""Application composition and dependency boundary."""
from .agent import OpenAICompatibleClient, RecommendationAgent
from .config import Settings, get_settings
from .data import seed_store
from .repositories.json_store import JsonStoreRepository
from .repositories.mongo_store import MongoStoreRepository
from .chat import SessionStore, ChatOrchestrator
from .tools import DatabaseTools, ToolRegistry
from .chat.assistant import CustomerAssistant
from .recommendations.service import rank_products

class ApplicationContainer:
    def __init__(self, settings: Settings | None=None):
        self.settings=settings or get_settings()
        self.agent=self._agent()
        self.repository=self._repository()
        self.store=self.repository.load()
        self.sessions=SessionStore(self.settings.chat_session_ttl_seconds, self.settings.chat_max_history)
        self.tools=DatabaseTools(self.store, self.repository)
        self.chat=ChatOrchestrator(self.agent.llm_client, ToolRegistry(self.tools), self.sessions, self.agent.fallback_scope_response)
        self.assistant=CustomerAssistant(self.tools,self.sessions,self._recommend,self.chat)
    def _agent(self):
        if self.settings.llm_model:
            return RecommendationAgent(OpenAICompatibleClient(self.settings.llm_api_key or 'ollama',self.settings.llm_base_url,self.settings.llm_model,self.settings.llm_timeout_seconds))
        return RecommendationAgent()
    def _repository(self):
        if self.settings.storage_backend.lower()=="mongo": return MongoStoreRepository(self.settings.mongo_uri,self.settings.mongodb_database)
        return JsonStoreRepository(self.settings.data_path)
    def seed(self):
        self.store=seed_store(self.settings.data_path) if self.settings.storage_backend.lower()=="json" else __import__("scripts.generate_dummy_data",fromlist=["generate"]).generate()
        self.repository.save(self.store)
        self.tools.store=self.store
        return self.store
    def _recommend(self, request):
        return rank_products(self.store, request)
    def health(self): return {"storage_backend":self.settings.storage_backend,"storage_reachable":self.repository.ping(),"data_loaded":bool(self.store.collections.get("products"))}
