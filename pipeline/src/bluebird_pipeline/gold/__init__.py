"""Gold layer: KPI probabilities per station and day (``Aggregator*`` classes)."""

from .base import (
    AGGREGATORS,
    Aggregator,
    AggregatorParams,
    KpiResult,
    confidence_level,
    register_aggregator,
)

__all__ = [
    "AGGREGATORS",
    "Aggregator",
    "AggregatorParams",
    "KpiResult",
    "confidence_level",
    "register_aggregator",
]
