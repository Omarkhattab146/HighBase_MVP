import re
from dataclasses import dataclass

@dataclass(frozen=True)
class ParsedIntent:
    kind: str
    query: str = ""
    product_terms: tuple[str, ...] = ()
    category: str | None = None
    max_price: float | None = None
    limit: int = 5

PRODUCT_TERMS=("water","juice","coffee","milk","cheese","rice","pasta","oil","snacks","biscuits","chocolate","chips")
CATEGORIES=("beverages","snacks","dairy","pantry")

def parse_intent(message: str) -> ParsedIntent:
    text=message.lower().strip()
    words=lambda value: bool(re.search(rf"\b{re.escape(value)}\b", text))
    if text in {"hi","hello","hey","hiya","good morning","good afternoon","good evening","thanks","thank you","bye","goodbye"}:
        return ParsedIntent("conversation")
    terms=tuple(term for term in PRODUCT_TERMS if words(term))
    category=next((item.title() for item in CATEGORIES if words(item)),None)
    budget_match=re.search(r"(?:under|below|max(?:imum)?|budget)\s*(?:bhd\s*)?(\d+(?:\.\d+)?)\s*(?:bhd)?",text)
    budget=float(budget_match.group(1)) if budget_match else None
    has_offers=any(words(x) for x in ("offer","offers","discount"))
    has_trends=any(words(x) for x in ("trend","trending","trendy","popular"))
    if has_offers and has_trends: kind="offers_and_trends"
    elif has_offers: kind="offers"
    elif has_trends: kind="trends"
    elif any(words(x) for x in ("price","cost","costs")): kind="price_lookup"
    elif any(words(x) for x in ("available","availability","stock","in stock")): kind="availability_lookup"
    elif any(words(x) for x in ("recommend","recommendation","suggest","buy")): kind="recommendation"
    elif any(words(x) for x in ("order","orders","sales","revenue","database","category","categories")): kind="analytics"
    elif terms or category or words("product") or words("products") or words("catalog"): kind="product_information"
    elif any(words(x) for x in ("who","what","when","where","why","how")): kind="out_of_scope"
    else: kind="clarification"
    return ParsedIntent(kind," ".join(terms),terms,category,budget,5)
