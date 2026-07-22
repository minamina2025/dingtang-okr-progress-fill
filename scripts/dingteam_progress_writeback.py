#!/usr/bin/env python3
"""Guarded Dingteam OKR progress writeback helper.

This helper deliberately defaults to dry-run. It validates a progress plan and
prints one safe action per KR. Real writeback must be performed by a verified
browser/API implementation in the current environment and only after the user
approves the exact plan.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

TOOLKIT_PATH = Path(__file__).resolve().parent / "okr_progress_toolkit.py"
spec = importlib.util.spec_from_file_location("okr_progress_toolkit", TOOLKIT_PATH)
toolkit = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(toolkit)


def load_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, help="progress plan JSON")
    parser.add_argument("--okr", help="live OKR JSON for krId validation")
    parser.add_argument("--execute", action="store_true", help="refuse unless implementation is verified")
    args = parser.parse_args()

    plan = toolkit.sanitize_obj(load_json(args.plan))
    okr = load_json(args.okr) if args.okr else None
    validation = toolkit.validate_plan(plan, okr)
    print(json.dumps(validation, ensure_ascii=False, indent=2))
    if not validation["ok"]:
        return 1

    print("\nPlanned KR updates:")
    for item in plan.get("updates", []):
        label = item.get("label") or item.get("krTitle") or item.get("krId")
        print(f"- {label}: {item.get('progress')}% / {item.get('krId')}")

    if args.execute:
        print(
            "\nRefusing execute: no verified Dingteam writeback implementation is bundled yet. "
            "Use this dry-run output with a separately verified UI/API path.",
            file=sys.stderr,
        )
        return 2

    print("\nDry-run only. No Dingteam data was changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
