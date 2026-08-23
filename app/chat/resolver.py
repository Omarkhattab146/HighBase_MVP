import re

class ProductResolver:
    def __init__(self, tools): self.tools=tools
    def resolve(self, query, history=None):
        text=query.lower().strip()
        if history and any(token in text for token in ("first one","second one","third one","that one","it")):
            previous=self._previous_products(history)
            ordinal=next((i for i,name in enumerate(("first one","second one","third one")) if name in text),None)
            if ordinal is not None and ordinal < len(previous):
                rows=self.tools.search_products(query=previous[ordinal],limit=20)
                return ("exact",rows[:1]) if rows else ("missing",[])
            if previous and any(token in text for token in ("that one","it")):
                rows=self.tools.search_products(query=previous[-1],limit=20)
                return ("exact",rows[:1]) if rows else ("missing",[])
        explicit=re.search(r"(?:product|named|called)\s+([a-z0-9 ]+)",text)
        search=(explicit.group(1).strip() if explicit else text)
        for prefix in ("tell me about ","what is the price of ","what is the cost of ","is ","do we have "):
            search=search.removeprefix(prefix).strip(" ?")
        if not search and history:
            search=self._last_product(history) or ""
        rows=self.tools.search_products(query=search,limit=20) if search else []
        unique={row.get("product_id"):row for row in rows if row.get("product_id")}
        rows=list(unique.values())
        if len(rows)==1: return "exact",rows
        if len(rows)>1: return "ambiguous",rows
        return "missing",[]
    @staticmethod
    def _last_product(history):
        for message in reversed(history or []):
            match=re.search(r"Highbase\s+[A-Za-z]+\s+\d+",message.get("content", ""),re.I)
            if match:return match.group(0)
        return None
    @staticmethod
    def _previous_products(history):
        names=[]
        for message in reversed(history or []):
            names.extend(re.findall(r"Highbase\s+[A-Za-z]+\s+\d+",message.get("content", ""),re.I))
            if names: break
        return list(dict.fromkeys(names))
