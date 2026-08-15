"""Local run evidence storage and compatible comparison queries."""

from .comparison import (
    DimensionComparison,
    IdentityDifference,
    MetricDelta,
    RunComparison,
    RunComparisonService,
    compare_runs,
)
from .sqlite import (
    ImmutableRunConflictError,
    InvalidRunBundleError,
    InvalidRunStateError,
    RunNotFoundError,
    RunStoreError,
    SQLiteRunStore,
)

__all__ = [
    "DimensionComparison",
    "IdentityDifference",
    "ImmutableRunConflictError",
    "InvalidRunBundleError",
    "InvalidRunStateError",
    "MetricDelta",
    "RunComparison",
    "RunComparisonService",
    "RunNotFoundError",
    "RunStoreError",
    "SQLiteRunStore",
    "compare_runs",
]
