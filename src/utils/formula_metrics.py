"""Prometheus metrics helpers for formula awareness pipelines."""

from __future__ import annotations

import logging
from typing import Optional

try:
    from prometheus_client import Gauge, Histogram
except ModuleNotFoundError:  # pragma: no cover - fallback when prometheus_client missing
    Gauge = None  # type: ignore
    Histogram = None  # type: ignore


LOGGER = logging.getLogger(__name__)


class FormulaMetricsRecorder:
    """Lightweight recorder encapsulating Prometheus metrics updates."""

    def __init__(self) -> None:
        self._enabled = Gauge is not None and Histogram is not None

        if not self._enabled:
            LOGGER.warning(
                "prometheus_client not available; formula metrics will be disabled"
            )
            return

        # 1 if last extraction succeeded, 0 otherwise.
        self._success_gauge = Gauge(
            "formula_extraction_success_rate",
            "Indicator for most recent formula extraction run",
        )
        self._duration_hist = Histogram(
            "formula_extraction_duration_seconds",
            "Wall-clock duration of formula extraction runs",
            buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, float("inf")),
        )
        self._formula_cells = Gauge(
            "formula_cells_processed_total",
            "Number of formula cells processed in most recent extraction",
        )
        self._total_cells = Gauge(
            "formula_cells_total_examined",
            "Total cells examined in most recent extraction",
        )
        self._missing_dependencies = Gauge(
            "formula_missing_dependencies_total",
            "Missing dependency references in most recent extraction",
        )

    @property
    def enabled(self) -> bool:
        return self._enabled

    def record(
        self,
        *,
        success: bool,
        duration_seconds: float,
        total_cells: int,
        formula_cells: int,
        missing_dependencies: int,
    ) -> None:
        """Update metrics for a completed extraction run."""

        if not self._enabled:
            return

        self._success_gauge.set(1.0 if success else 0.0)
        self._duration_hist.observe(max(duration_seconds, 0.0))
        self._formula_cells.set(formula_cells)
        self._total_cells.set(total_cells)
        self._missing_dependencies.set(missing_dependencies)


_default_recorder: Optional[FormulaMetricsRecorder] = None


def get_formula_metrics_recorder() -> FormulaMetricsRecorder:
    """Return a singleton recorder instance."""

    global _default_recorder
    if _default_recorder is None:
        _default_recorder = FormulaMetricsRecorder()
    return _default_recorder
