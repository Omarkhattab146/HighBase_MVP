from .intent import ParsedIntent, parse_intent
from .resolver import ProductResolver

class CustomerAssistant:
    """Deterministic customer-facing chat service; facts always come from tools."""
    def __init__(self, tools, sessions, recommender, orchestrator=None):
        self.tools=tools; self.sessions=sessions; self.recommender=recommender; self.orchestrator=orchestrator; self.resolver=ProductResolver(tools)

    def handle(self, message, session_id=None, request=None):
        sid=session_id or self.sessions.create(); history=self.sessions.history(sid); intent=parse_intent(message); tools_used=[]; products=[]; recommendations=[]; needs=False
        if intent.kind=="conversation": answer=self._conversation(message)
        elif intent.kind=="out_of_scope": answer="I can only help with HIGHBASE products, inventory, sales, offers, and business data. What would you like to check?"
        elif intent.kind in {"product_information","price_lookup","availability_lookup"}:
            if intent.max_price is not None or intent.category:
                products=self.tools.search_products(query=intent.query,category=intent.category,max_price=intent.max_price,limit=intent.limit); status="exact" if products else "missing"
            else:
                status,products=self.resolver.resolve(message,history)
            tools_used=["search_products"]
            if status=="ambiguous":
                names=", ".join(row["name"] for row in products[:5]); answer=f"I found a few matching products: {names}. Which one would you like to know more about?"; needs=True
            elif status=="missing": answer="I couldn’t find that product in the HIGHBASE catalog. Could you check the product name or category?"
            elif intent.kind=="product_information" and len(products)>1: answer=self._catalog_answer(products)
            else: answer=self._product_answer(products[0],intent.kind)
        elif intent.kind=="recommendation":
            recommendations=self.recommender(request); tools_used=["search_products"]; answer=self._recommendation_answer(recommendations)
        elif intent.kind=="offers":
            products=self.tools.get_offers(query=intent.query,category=intent.category,limit=intent.limit); tools_used=["get_offers"]; answer=self._offers_answer(products)
        elif intent.kind=="trends":
            products=self.tools.get_trending_products(category=intent.category,limit=intent.limit); tools_used=["get_trending_products"]; answer=self._trends_answer(products)
        elif intent.kind=="analytics":
            data=self.tools.get_analytics_summary(category=intent.category); tools_used=["get_analytics_summary"]; answer=self._analytics_answer(data)
        elif intent.kind=="offers_and_trends":
            offers=self.tools.get_offers(query=intent.query,category=intent.category,limit=intent.limit)
            trends=self.tools.get_trending_products(category=intent.category,limit=intent.limit)
            products=list({row["product_id"]:row for row in offers+trends}.values()); tools_used=["get_offers","get_trending_products"]
            answer=self._combined_answer(offers,trends)
        else:
            answer="What would you like to check in HIGHBASE—products, prices, stock, offers, trends, or sales?"; needs=True
        self.sessions.append(sid,{"role":"user","content":message},{"role":"assistant","content":answer})
        return {"session_id":sid,"response":answer,"intent":("clarification" if needs else intent.kind),"products":products,"recommendations":recommendations,"tools_used":tools_used,"needs_clarification":needs}

    @staticmethod
    def _conversation(message):
        text=message.lower().strip()
        if text in {"thanks","thank you"}: return "You’re welcome! I’m happy to help with HIGHBASE."
        if text in {"bye","goodbye"}: return "Goodbye! Come back anytime you want to check HIGHBASE data."
        return "Hello! I can help with HIGHBASE products, prices, stock, offers, trends, and sales. What would you like to check?"
    @staticmethod
    def _product_answer(product,kind):
        name=product.get("name"); price=product.get("price"); availability=product.get("availability","availability unknown")
        if kind=="price_lookup": return f"{name} costs {price} {product.get('currency','BHD')}." if price is not None else f"The price for {name} is currently unavailable."
        if kind=="availability_lookup": return f"{name} is currently {availability.lower()}."
        price_text=f"{price} {product.get('currency','BHD')}" if price is not None else "an unknown price"
        offer=product.get("offer"); offer_text=f" It has a {offer['discount_percent']:.0f}% offer at {offer['offer_price']} {product.get('currency','BHD')} until {offer['valid_until']}." if offer else ""
        return f"{name} is a {product.get('category','HIGHBASE')} product priced at {price_text} and is currently {availability.lower()}.{offer_text}"
    @staticmethod
    def _recommendation_answer(rows):
        if not rows:return "I couldn’t find a matching in-stock recommendation. Try another product, category, or budget."
        return "Here are a few HIGHBASE options that match your request:\n"+"\n".join(f"- {r.name} — {r.price:.2f} {r.currency}; {'; '.join(r.reasons)}." for r in rows)
    @staticmethod
    def _catalog_answer(rows):
        return "I found these HIGHBASE products:\n"+"\n".join(f"- {row['name']}: {row['price']} {row['currency']} — {row['availability']}." for row in rows)
    @staticmethod
    def _combined_answer(offers,trends):
        sections=[]
        if offers: sections.append("Offers:\n"+"\n".join(f"- {r['name']}: {r['offer']['offer_price']} {r['currency']} ({r['offer']['discount_percent']:.0f}% off)." for r in offers))
        if trends: sections.append("Trending:\n"+"\n".join(f"- {r['name']} ({r['trend_growth']:.1%} growth)." for r in trends))
        return "\n\n".join(sections) if sections else "I couldn’t find current offers or enough sales data for trends."
    @staticmethod
    def _offers_answer(rows):
        if not rows:return "There are no matching HIGHBASE offers right now."
        return "Here are the available HIGHBASE offers:\n"+"\n".join(f"- {r['name']}: {r['offer']['offer_price']} {r['currency']} ({r['offer']['discount_percent']:.0f}% off until {r['offer']['valid_until']})." for r in rows)
    @staticmethod
    def _trends_answer(rows):
        if not rows:return "I don’t have enough recent sales data to identify a trend."
        return "These products are trending in recent sales:\n"+"\n".join(f"- {r['name']} ({r['trend_growth']:.1%} growth)." for r in rows)
    @staticmethod
    def _analytics_answer(data):
        top=data.get("top_products",[])
        return "The latest HIGHBASE sales summary is available. Top products: "+", ".join(str(pid) for pid,_ in top[:5])+"." if top else "I don’t have enough sales data for a summary yet."
