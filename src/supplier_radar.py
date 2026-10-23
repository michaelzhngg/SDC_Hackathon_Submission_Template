from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List


OPEN_RISK_STATUSES = {"PENDING_APPROVAL", "NEEDS_CLARIFICATION"}


def build_supplier_radar(
    cases: List[Dict[str, Any]],
    insight_lookup: Callable[[int], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Aggregate supplier exceptions without making an automated supplier judgment."""
    grouped: Dict[str, Dict[str, Any]] = {}

    for case in cases:
        supplier = (case.get("supplier_name") or "Demo Supplier").strip() or "Demo Supplier"
        bucket = grouped.setdefault(
            supplier,
            {
                "supplier_name": supplier,
                "total_cases": 0,
                "exception_cases": 0,
                "repeat_cases": 0,
                "money_at_risk": 0.0,
                "issue_counts": Counter(),
            },
        )
        bucket["total_cases"] += 1
        discrepancies = case.get("comparison", {}).get("discrepancies", [])
        if discrepancies:
            bucket["exception_cases"] += 1
            bucket["issue_counts"].update(item["type"] for item in discrepancies)
        if insight_lookup(int(case["id"])).get("repeat_issue", False):
            bucket["repeat_cases"] += 1
        difference = case.get("comparison", {}).get("difference")
        if case.get("status") in OPEN_RISK_STATUSES and difference is not None:
            bucket["money_at_risk"] += abs(float(difference))

    radar: List[Dict[str, Any]] = []
    for bucket in grouped.values():
        top_issue = None
        if bucket["issue_counts"]:
            top_issue = bucket["issue_counts"].most_common(1)[0][0]
        radar.append(
            {
                "supplier_name": bucket["supplier_name"],
                "total_cases": bucket["total_cases"],
                "exception_cases": bucket["exception_cases"],
                "repeat_cases": bucket["repeat_cases"],
                "money_at_risk": round(bucket["money_at_risk"], 2),
                "top_issue": top_issue,
            }
        )

    radar.sort(
        key=lambda item: (item["money_at_risk"], item["repeat_cases"], item["exception_cases"]),
        reverse=True,
    )
    max_risk = max((item["money_at_risk"] for item in radar), default=0.0)
    for item in radar:
        item["risk_percent"] = round((item["money_at_risk"] / max_risk) * 100) if max_risk else 0
    return radar
