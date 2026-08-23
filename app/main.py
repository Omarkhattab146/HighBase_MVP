from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .agent import RecommendationAgent
from .config import get_settings
from .container import ApplicationContainer
from .models import (
    ChatRequest,
    ChatResponse,
    DatabaseOverview,
    QualityReport,
    RecommendationRequest,
    RecommendationResponse,
    SessionResponse,
)
from .pipeline.runner import DataPipeline
from .services import analytics, recommend

app=FastAPI(title="HIGHBASE Customer Recommendation AI",version="0.2.0")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
settings=get_settings(); container=ApplicationContainer(settings); store=container.store; agent=container.agent; last_pipeline_run=None

def get_current_store(): return store
def get_current_agent(): return agent

def _health(): return {"status":"ok","data_loaded":bool(store.collections.get("products"))}
@app.get("/health")
def health(): return _health()
@app.get("/api/v1/health")
def versioned_health(): return {**_health(),"storage_backend":settings.storage_backend,"pipeline_version":settings.pipeline_version,"storage_reachable":container.repository.ping()}

def _seed():
    global store
    store=container.seed()
    if hasattr(container.repository,"save_snapshot"): container.repository.save_snapshot(store,"raw")
    return {n:len(v) for n,v in store.collections.items()}
@app.post("/data/seed")
@app.post("/api/v1/data/seed")
def seed(): return _seed()

@app.get("/data/eda")
@app.get("/api/v1/data/eda")
def eda(current_store=Depends(get_current_store)): return DataPipeline(current_store,settings.pipeline_version).eda()

def _clean():
    global store,last_pipeline_run
    pipeline=DataPipeline(store,settings.pipeline_version); cleaned,quality,run=pipeline.run_cleaning(); store=cleaned; container.store=cleaned; container.tools.store=cleaned; last_pipeline_run=run
    if hasattr(container.repository,"save_snapshot"):
        container.repository.save_snapshot(pipeline.raw_store,"raw"); container.repository.save_snapshot(cleaned,"clean")
    return quality
@app.post("/data/clean",response_model=QualityReport)
@app.post("/api/v1/data/clean",response_model=QualityReport)
def cleaning(): return _clean()

@app.get("/data/pipeline/latest")
@app.get("/api/v1/data/pipeline/latest")
def latest_pipeline(): return last_pipeline_run or {"status":"not_run"}

def _summary():
    a=analytics(store); return {"product_sales":dict(a["product_sales"]),"category_sales":dict(a["category_sales"]),"top_products":a["product_sales"].most_common(10),"co_purchases":a["co_purchase_metrics"],"trends":a["trends"],"rfm":a["rfm"]}
@app.get("/analytics/summary")
@app.get("/api/v1/analytics/summary")
def summary(): return _summary()

def _recommendations(req): return RecommendationResponse(recommendations=recommend(store,req))
@app.post("/recommendations",response_model=RecommendationResponse)
@app.post("/api/v1/recommendations",response_model=RecommendationResponse)
def recommendations(req:RecommendationRequest): return _recommendations(req)

def _chat(req):
    container.store=store
    container.tools.store=store
    query=req.message or req.query
    req.query=query
    result=container.assistant.handle(query,req.session_id,req)
    products=result["products"]
    return ChatResponse(recommendations=result["recommendations"],response=result["response"],request_id=str(uuid4()),session_id=result["session_id"],tools_used=result["tools_used"],intent=result["intent"],products=products,offers=[x for x in products if x.get('offer')],trends=[x for x in products if x.get('trend_growth') is not None],needs_clarification=result["needs_clarification"])
@app.post("/chat",response_model=ChatResponse)
@app.post("/api/v1/chat",response_model=ChatResponse)
def chat(req:ChatRequest): return _chat(req)

@app.get('/ui', include_in_schema=False)
def ui(): return FileResponse('app/static/index.html')

@app.post('/api/v1/chat/session', response_model=SessionResponse)
@app.post('/chat/session', response_model=SessionResponse)
def create_session(): return SessionResponse(session_id=container.sessions.create())

@app.delete('/api/v1/chat/session/{session_id}')
@app.delete('/chat/session/{session_id}')
def delete_session(session_id: str):
    if not container.sessions.delete(session_id): raise HTTPException(404,'Session not found')
    return {'deleted':True}

@app.get('/api/v1/db/overview', response_model=DatabaseOverview)
@app.get('/db/overview', response_model=DatabaseOverview)
def database_overview():
    return DatabaseOverview(collections=container.repository.business_overview(),storage_backend=settings.storage_backend)
