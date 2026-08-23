"""Backward-compatible service facade.

New code should import from ``app.pipeline``, ``app.analytics``, or
``app.recommendations`` directly. Existing callers can keep using these MVP
function names while the implementation remains modular.
"""
from .pipeline.cleaning import clean_products
from .pipeline.features import build_features
from .analytics.service import build_analytics
from .recommendations.service import rank_products

clean=clean_products
feature_engineer=build_features
analytics=build_analytics
recommend=rank_products
