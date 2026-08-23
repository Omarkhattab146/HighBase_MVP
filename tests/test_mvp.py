from scripts.generate_dummy_data import generate
from app.models import RecommendationRequest,DataStore
from app.services import clean,recommend,feature_engineer
from app.pipeline.eda import explore
from app.agent import RecommendationAgent
from app.pipeline.runner import DataPipeline
def test_generation_is_deterministic(): assert generate().collections==generate().collections
def test_cleaning_flags_quality_issues():
    s=generate(); report=clean(s); assert report.duplicates and report.missing and report.outliers; assert all(p["price"]<=100 for p in s.collections["products"]); assert all("category_code" in p for p in s.collections["products"])
def test_eda_is_read_only_and_profiles_raw_data():
    s=generate(); before=list(s.collections["products"]); report=explore(s); assert report["collections"]["products"]["rows"]==len(before); assert report["quality"]["duplicate_product_ids"]; assert s.collections["products"]==before
def test_cleaning_preserves_referential_integrity_after_outlier_deletion():
    s=generate(); clean(s); product_ids={p["product_id"] for p in s.collections["products"]}; assert all(item["product_id"] in product_ids for item in s.collections["order_items"]); assert s.metadata["cleaning"]["orphan_order_items_removed"]>0
def test_recommendations_exclude_unavailable():
    s=generate(); clean(s); rows=recommend(s,RecommendationRequest(business_type="Cafe",query="coffee")); assert rows and all(r.availability=="In Stock" for r in rows)
def test_feature_engineering_adds_rankable_features():
    s=generate(); clean(s); features=feature_engineer(s); assert features["sales"] and all("features" in p for p in s.collections["products"])
def test_agent_is_grounded_and_mentions_demo_data():
    s=generate(); clean(s); rows=recommend(s,RecommendationRequest(business_type="Cafe",query="coffee",limit=1)); text=RecommendationAgent().respond("coffee",rows,"Cafe"); assert rows[0].name in text and "synthetic" in text.lower()
def test_agent_extracts_intent_and_budget():
    intent=RecommendationAgent().extract_intent("I run a cafe and need coffee under 5 BHD")
    assert intent["business_type"]=="Cafe" and intent["product_terms"]==["coffee"] and intent["budget"]==5
def test_pipeline_run_keeps_raw_and_clean_snapshots():
    s=generate(); pipeline=DataPipeline(s); cleaned,quality,run=pipeline.run_cleaning()
    assert run.status=="completed" and run.run_id and pipeline.raw_store is not pipeline.cleaned_store
    assert run.stage_counts["outliers_deleted"]==1 and len(pipeline.raw_store.collections["products"])>len(cleaned.collections["products"])
def test_analytics_exposes_trends_rfm_and_co_purchase_metrics():
    s=generate(); clean(s); from app.analytics.service import build_analytics
    result=build_analytics(s); assert "trends" in result and "rfm" in result and "co_purchase_metrics" in result
def test_recommendations_include_evidence():
    s=generate(); clean(s); rows=recommend(s,RecommendationRequest(business_type="Cafe",query="coffee",limit=1)); assert rows[0].evidence["availability"]==1.0
