import re
import httpx
from .prompts import SYSTEM_PROMPT, USER_PROMPT, INTENT_PROMPT, ANALYTICS_PROMPT

class OpenAICompatibleClient:
    """Small optional client for Ollama/OpenAI-compatible chat endpoints."""
    def __init__(self, api_key, base_url, model, timeout=10.0):
        self.api_key=api_key; self.base_url=base_url.rstrip("/"); self.model=model; self.timeout=timeout
    def complete(self, prompt):
        response=httpx.post(f"{self.base_url}/chat/completions",headers={"Authorization":f"Bearer {self.api_key}","Content-Type":"application/json"},json={"model":self.model,"temperature":0,"messages":[{"role":"user","content":prompt}]},timeout=self.timeout)
        response.raise_for_status(); return response.json()["choices"][0]["message"]["content"]
    def chat(self, messages, tools=None):
        payload={"model":self.model,"temperature":0,"messages":messages}
        if tools: payload["tools"]=tools; payload["tool_choice"]="auto"
        response=httpx.post(f"{self.base_url}/chat/completions",headers={"Authorization":f"Bearer {self.api_key or 'ollama'}","Content-Type":"application/json"},json=payload,timeout=self.timeout)
        response.raise_for_status(); return response.json()["choices"][0]["message"]

class RecommendationAgent:
    """Grounded MVP agent. LLM integration can be added behind this boundary later."""
    def __init__(self, llm_client=None): self.llm_client=llm_client
    def respond(self, message, recommendations, business_type=""):
        if not message.strip():
            return "What type of business do you run, and which products are you looking for?"
        if not recommendations:
            return "I could not find available products matching that request. Try another category or remove the price limit."
        if self.llm_client:
            try:
                candidate=self.llm_client.complete(self.prompt(message,recommendations,business_type))
                if self._is_grounded(candidate,recommendations): return candidate
            except Exception:
                pass
        lines=["Based on the synthetic HIGHBASE sales data, I recommend:"]
        for item in recommendations:
            lines.append(f"- {item.name} ({item.price:.2f} {item.currency}) — {'; '.join(item.reasons)}. {item.product_url}")
        return "\n".join(lines)

    def _is_grounded(self, text, recommendations):
        allowed_urls={item.product_url for item in recommendations}; allowed_names={item.name.lower() for item in recommendations}
        if any(url in text and url not in allowed_urls for url in re.findall(r"https?://\S+",text)): return False
        mentioned_names=[name for name in allowed_names if name in text.lower()]
        return bool(mentioned_names) and "synthetic" in text.lower()

    def extract_intent(self, message, business_type=None):
        """Small deterministic intent parser used before recommendation retrieval."""
        text=message.lower(); known=["restaurant","cafe","mini market","catering","hotel"]
        detected=business_type or next((x.title() for x in known if x in text), None)
        terms=[x for x in ("water","juice","coffee","milk","cheese","rice","pasta","oil","snacks","biscuits","chocolate") if re.search(rf"\b{re.escape(x)}\b",text)]
        budget=re.search(r"(?:under|below|max(?:imum)?|budget)\s*(?:bhd)?\s*(\d+(?:\.\d+)?)",text)
        return {"business_type":detected,"product_terms":terms,"budget":float(budget.group(1)) if budget else None,"quantity":None,"needs_clarification":not bool(detected or terms)}

    @staticmethod
    def is_small_talk(message):
        """Return true for messages that should not trigger product retrieval."""
        normalized=re.sub(r"[^a-z ]", "", message.lower()).strip()
        return normalized in {"hi", "hello", "hey", "hiya", "good morning", "good afternoon", "good evening", "thanks", "thank you", "bye", "goodbye"}

    @staticmethod
    def is_highbase_question(message):
        """Conservative scope check for questions answerable by the business dataset."""
        text=message.lower()
        terms=("highbase", "product", "catalog", "category", "inventory", "stock", "price", "sales", "sold", "order", "revenue", "trend", "popular", "recommend", "available", "database", "coffee", "milk", "water", "cheese", "rice", "pasta", "oil", "juice", "snack", "biscuit", "chocolate")
        return any(term in text for term in terms)

    @staticmethod
    def needs_recommendations(message):
        text=message.lower()
        return any(term in text for term in ("recommend", "suggest", "which should", "what should", "buy", "looking for", "in stock", "available", "find", "products", "coffee", "milk", "water", "cheese", "rice", "pasta", "oil", "juice", "snack", "biscuit", "chocolate"))

    def fallback_scope_response(self, message):
        if self.is_small_talk(message):
            normalized=re.sub(r"[^a-z ]", "", message.lower()).strip()
            if normalized in {"thanks", "thank you"}: return "You’re welcome! I’m happy to help with HIGHBASE whenever you need."
            if normalized in {"bye", "goodbye"}: return "Goodbye! Come back anytime you want to check HIGHBASE data."
            return "Hello! How can I help you with HIGHBASE products, inventory, or sales today?"
        return "I can only help with HIGHBASE products, inventory, sales, and business data. What would you like to check?"

    def build_context(self, recommendations, analytics=None):
        return {"recommendations":[r.model_dump() if hasattr(r,"model_dump") else r.dict() for r in recommendations],"analytics":analytics or {}}

    def prompt(self, message, recommendations, business_type="", analytics=""):
        items=[r.model_dump() if hasattr(r,"model_dump") else r.dict() for r in recommendations]
        return SYSTEM_PROMPT+"\n\n"+USER_PROMPT.format(message=message,business_type=business_type,recommendations=items,analytics=analytics)

    def langchain_chain(self, llm):
        """Return the reference notebook's reusable prompt | model | parser chain.
        LangChain stays optional; callers can use this only when installed/configured.
        """
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        template=ChatPromptTemplate.from_messages([("system",SYSTEM_PROMPT),("human",USER_PROMPT)])
        return template | llm | StrOutputParser()
