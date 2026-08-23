from ..prompts import CHAT_SYSTEM_PROMPT

class ChatOrchestrator:
    def __init__(self, client, registry, sessions, fallback=None):
        self.client=client; self.registry=registry; self.sessions=sessions; self.fallback_handler=fallback
    def respond(self, message, session_id=None):
        sid=session_id or self.sessions.create(); history=self.sessions.history(sid); used=[]
        messages=[{'role':'system','content':CHAT_SYSTEM_PROMPT},*history,{'role':'user','content':message}]
        if not self.client: return sid, self._fallback(message), used
        try:
            for _ in range(3):
                reply=self.client.chat(messages,self.registry.definitions()); calls=reply.get('tool_calls') or []
                messages.append(reply)
                if not calls: answer=reply.get('content') or self._fallback(message); break
                for call in calls:
                    name=call['function']['name']; used.append(name)
                    try: result=self.registry.call(name,call['function'].get('arguments','{}'))
                    except Exception as exc: result={'error':str(exc)}
                    messages.append({'role':'tool','tool_call_id':call.get('id',''),'name':name,'content':self._json(result)})
            else: answer='I could not complete that data lookup. Please try a more specific question.'
        except Exception: answer=self._fallback(message)
        self.sessions.append(sid,{'role':'user','content':message},{'role':'assistant','content':answer})
        return sid, answer, used
    @staticmethod
    def _json(value):
        import json; return json.dumps(value,default=str)
    def _fallback(self, message):
        if self.fallback_handler: return self.fallback_handler(message)
        return "I’m here to help with HIGHBASE products, inventory, sales, and business data. What would you like to check?"
