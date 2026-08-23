from datetime import datetime, timedelta, timezone
from uuid import uuid4

class SessionStore:
    def __init__(self, ttl_seconds=1800, max_history=12):
        self.ttl=timedelta(seconds=ttl_seconds); self.max_history=max_history; self._sessions={}
    def create(self):
        sid=str(uuid4()); self._sessions[sid] = (datetime.now(timezone.utc), []); return sid
    def history(self, sid):
        self._purge(); return list(self._sessions.get(sid, (None, []))[1])
    def append(self, sid, *messages):
        self._purge(); stamp, history=self._sessions.setdefault(sid, (datetime.now(timezone.utc), []))
        history.extend(messages); self._sessions[sid]=(datetime.now(timezone.utc), history[-self.max_history:])
    def delete(self, sid): return self._sessions.pop(sid, None) is not None
    def _purge(self):
        now=datetime.now(timezone.utc)
        for sid,(stamp,_) in list(self._sessions.items()):
            if now-stamp > self.ttl: self._sessions.pop(sid, None)
