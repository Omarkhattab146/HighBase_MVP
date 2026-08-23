from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4
from .eda import explore
from .cleaning import clean_products
from ..models import PipelineRun

class DataPipeline:
    """Versioned, repeatable EDA/cleaning runner with raw/clean separation."""
    def __init__(self, store, pipeline_version="2026.08.1"):
        self.store=store; self.pipeline_version=pipeline_version; self.raw_store=None; self.cleaned_store=None; self.last_run=None
    def eda(self): return explore(self.store)
    def clean(self): return clean_products(self.store)
    def run_cleaning(self):
        started=datetime.now(timezone.utc); run=PipelineRun(run_id=str(uuid4()),pipeline_version=self.pipeline_version,status="running",started_at=started,source_counts={n:len(v) for n,v in self.store.collections.items()})
        self.raw_store=deepcopy(self.store); self.cleaned_store=deepcopy(self.store); quality=clean_products(self.cleaned_store); self.cleaned_store.metadata["pipeline_run_id"]=run.run_id
        run.status="completed"; run.completed_at=datetime.now(timezone.utc); run.cleaned_counts={n:len(v) for n,v in self.cleaned_store.collections.items()}; run.stage_counts={"duplicates_removed":quality.duplicates,"outliers_deleted":quality.outliers,"missing_values_handled":quality.missing,"records_rejected":quality.rejected,"orphan_items_removed":self.cleaned_store.metadata.get("cleaning",{}).get("orphan_order_items_removed",0)}; run.warnings=["Synthetic/demo data"]
        run.rejected_ids=list(self.cleaned_store.metadata.get("rejected_ids",[])); self.last_run=run
        return self.cleaned_store, quality, run
