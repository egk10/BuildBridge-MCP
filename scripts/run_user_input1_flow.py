#!/usr/bin/env python3
"""Replay the five-step User Input 1 scenario against the BuildBridge API."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import requests

PROMPTS = [
    {
        "label": "User Input 1",
        "query": (
            "Hi BuildBridge! I need to analyze cost data across my three active projects: "
            "72 Perth, 17175 Yonge St, and Azure Road. Can you show me a summary of all three projects first?"
        ),
    },
    {
        "label": "User Input 2",
        "query": (
            "Perfect! Now I need to compare the cost per square foot for similar items across all three projects. "
            "Can you analyze concrete, steel, and electrical costs per sq ft? I suspect there are some pricing inconsistencies."
        ),
    },
    {
        "label": "User Input 3",
        "query": (
            "That's exactly what I suspected! Now can you help me identify any quantity takeoff errors? I want to "
            "compare actual quantities per sq ft between projects. Check concrete volume, steel tonnage, and electrical fixture counts relative to GCA."
        ),
    },
    {
        "label": "User Input 4",
        "query": (
            "Excellent analysis! Now I need a what-if scenario. What would happen to the Yonge Street project budget "
            "if we reduce the steel tonnage to industry standard and optimize the electrical fixture count? Also, show me the cascade effects on other costs."
        ),
    },
    {
        "label": "User Input 5",
        "query": (
            "Fantastic! This is exactly the kind of analysis I need. Can you now generate a comprehensive cost comparison "
            "report that I can present to the project managers? Include all the discrepancies we found and recommendations for each project."
        ),
    },
]


def _post_query(session: requests.Session, url: str, query: str, timeout: float) -> requests.Response:
    payload = {
        "query": query,
        "type": "ai_query",
        "parameters": {
            "include_data_context": True,
        },
    }
    response = session.post(url, json=payload, timeout=timeout)
    return response


def run_flow(base_url: str, endpoint: str, timeout: float) -> List[Dict[str, object]]:
    session = requests.Session()
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    results: List[Dict[str, object]] = []

    for prompt in PROMPTS:
        label = prompt["label"]
        query = prompt["query"]
        try:
            response = _post_query(session, url, query, timeout)
            parsed = response.json() if response.headers.get("Content-Type", "").startswith("application/json") else response.text
            results.append(
                {
                    "label": label,
                    "status_code": response.status_code,
                    "response": parsed,
                }
            )
            print(f"[{label}] HTTP {response.status_code}")
        except requests.exceptions.RequestException as exc:
            print(f"[{label}] Request failed: {exc}")
            results.append(
                {
                    "label": label,
                    "status_code": None,
                    "error": str(exc),
                }
            )
            break
        except json.JSONDecodeError:
            print(f"[{label}] Received non-JSON response")
            results.append(
                {
                    "label": label,
                    "status_code": response.status_code,
                    "response": response.text,
                    "warning": "Non-JSON response",
                }
            )
    return results


def save_results(path: Path, results: List[Dict[str, object]]) -> None:
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "results": results,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    print(f"💾 Saved transcript to {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for the BuildBridge API (default: http://localhost:8000)")
    parser.add_argument("--endpoint", default="/query", help="API endpoint to call (default: /query)")
    parser.add_argument("--timeout", type=float, default=120.0, help="Request timeout in seconds (default: 120)")
    parser.add_argument("--save", type=Path, help="Optional path to write the JSON transcript (e.g., docs/reports/user_input1_replay.json)")
    args = parser.parse_args()

    results = run_flow(args.base_url, args.endpoint, args.timeout)

    print("\n=== Replay Summary ===")
    for entry in results:
        label = entry["label"]
        status = entry.get("status_code")
        print(f"- {label}: HTTP {status if status is not None else 'N/A'}")
        if "error" in entry:
            print(f"  Error: {entry['error']}")

    if args.save:
        save_results(args.save, results)
    else:
        print("\nUse --save <path> to persist the transcript.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(130)