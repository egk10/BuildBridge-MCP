#!/usr/bin/env python3
"""Aggregate key project metrics from normalized manifest caches."""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from normalizers.project_metrics import (
    DEFAULT_CACHE_DIR,
    DEFAULT_OUTPUT_PATH,
    write_project_metrics_summary,
)


def main() -> None:
    cache_dir = DEFAULT_CACHE_DIR
    output_path = DEFAULT_OUTPUT_PATH
    cache_dir.mkdir(parents=True, exist_ok=True)
    write_project_metrics_summary(cache_dir, output_path)


if __name__ == "__main__":
    main()
