from app.chat.session import SessionStore
from app.tools.registry import ToolRegistry
from app.tools.database import DatabaseTools
from app.chat.orchestrator import ChatOrchestrator
from scripts.generate_dummy_data import generate

def test_sessions_are_bounded_and_deletable():
    sessions=SessionStore(max_history=2); sid=sessions.create()
    sessions.append(sid, {'role':'user','content':'a'}, {'role':'assistant','content':'b'}, {'role':'user','content':'c'})
    assert len(sessions.history(sid))==2
    assert sessions.delete(sid) and sessions.history(sid)==[]

def test_registry_rejects_unknown_tools():
    registry=ToolRegistry(DatabaseTools(generate()))
    try: registry.call('drop_database', {})
    except ValueError: pass
    else: assert False, 'write/unknown tool must be rejected'


class FakeClient:
    def __init__(self, replies): self.replies=iter(replies); self.calls=[]
    def chat(self, messages, tools=None):
        self.calls.append((messages, tools))
        return next(self.replies)


def test_orchestrator_returns_casual_model_reply_without_tools():
    client=FakeClient([{'role':'assistant','content':'Hello! How can I help with HIGHBASE today?'}])
    sessions=SessionStore(); orchestrator=ChatOrchestrator(client, ToolRegistry(DatabaseTools(generate())), sessions)

    sid, answer, used=orchestrator.respond('hi')

    assert sid and answer.startswith('Hello') and used==[]
    assert len(client.calls)==1


def test_orchestrator_executes_product_tool_then_returns_model_reply():
    client=FakeClient([
        {'role':'assistant','content':None,'tool_calls':[{'id':'call-1','type':'function','function':{'name':'search_products','arguments':'{"query":"coffee","limit":1}'}}]},
        {'role':'assistant','content':'I found a coffee product in the HIGHBASE catalog.'},
    ])
    orchestrator=ChatOrchestrator(client, ToolRegistry(DatabaseTools(generate())), SessionStore())

    _, answer, used=orchestrator.respond('Which coffee products do you have?')

    assert answer.startswith('I found')
    assert used==['search_products']
    assert len(client.calls)==2
    assert any(message['role']=='tool' for message in client.calls[1][0])


def test_orchestrator_uses_friendly_fallback_for_empty_model_reply():
    client=FakeClient([{'role':'assistant','content':''}])
    fallback=lambda message: 'I can help with HIGHBASE data. What would you like to check?'
    orchestrator=ChatOrchestrator(client, ToolRegistry(DatabaseTools(generate())), SessionStore(), fallback)

    _, answer, used=orchestrator.respond('something unclear')

    assert answer.startswith('I can help') and used==[]
