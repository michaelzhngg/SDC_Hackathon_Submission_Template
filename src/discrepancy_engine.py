from __future__ import annotations

from typing import Any, Dict, List


def _norm_unit(unit: str) -> str:
    return (unit or "").strip().lower()


def _trust_gate(status: str, discrepancies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a deterministic, explainable safety gate for consequential actions."""
    if status == "NEEDS_CLARIFICATION":
        return {
            "score": 20,
            "level": "BLOCKED",
            "approval_allowed": False,
            "reasons": ["Missing or incompatible units require human clarification."],
        }
    if status == "MATCH":
        return {
            "score": 100,
            "level": "CLEAR",
            "approval_allowed": False,
            "reasons": ["All connected records match; no consequential action is needed."],
        }

    weights = {
        "QUANTITY_MISMATCH": 20,
        "PRICE_MISMATCH": 20,
        "INVOICE_QUANTITY_MISMATCH": 15,
    }
    penalty = sum(weights.get(item["type"], 10) for item in discrepancies)
    score = max(45, 90 - penalty)
    return {
        "score": score,
        "level": "REVIEW",
        "approval_allowed": True,
        "reasons": [
            "Records are comparable, but one or more discrepancies require owner review.",
            "The score is a transparent rules-based heuristic, not an AI probability.",
        ],
    }


def compare_records(
    purchase_order: Dict[str, Any],
    received: Dict[str, Any],
    invoice: Dict[str, Any],
) -> Dict[str, Any]:
    po_unit = _norm_unit(purchase_order.get("unit", ""))
    received_unit = _norm_unit(received.get("unit", ""))
    invoice_unit = _norm_unit(invoice.get("unit", ""))

    if not po_unit or not received_unit or not invoice_unit or len({po_unit, received_unit, invoice_unit}) > 1:
        discrepancies = [
            {
                "type": "UNIT_CLARIFICATION",
                "message": "Units do not match. A person must confirm the conversion before comparison.",
                "evidence": {
                    "purchase_order_unit": purchase_order.get("unit"),
                    "received_unit": received.get("unit"),
                    "invoice_unit": invoice.get("unit"),
                },
            }
        ]
        status = "NEEDS_CLARIFICATION"
        return {
            "status": status,
            "discrepancies": discrepancies,
            "comparison_amount": None,
            "invoice_amount": None,
            "difference": None,
            "trust_gate": _trust_gate(status, discrepancies),
        }

    po_qty = float(purchase_order["quantity"])
    received_qty = float(received["quantity"])
    invoice_qty = float(invoice["quantity"])
    po_price = float(purchase_order["unit_price"])
    invoice_price = float(invoice["unit_price"])

    discrepancies: List[Dict[str, Any]] = []
    if received_qty != po_qty:
        discrepancies.append(
            {
                "type": "QUANTITY_MISMATCH",
                "message": f"Ordered {po_qty:g} {po_unit}, received {received_qty:g} {po_unit}.",
                "evidence": {"ordered": po_qty, "received": received_qty, "unit": po_unit},
            }
        )

    if invoice_price != po_price:
        discrepancies.append(
            {
                "type": "PRICE_MISMATCH",
                "message": f"Agreed RM{po_price:.2f}/{po_unit}, invoiced RM{invoice_price:.2f}/{po_unit}.",
                "evidence": {
                    "agreed_unit_price": po_price,
                    "invoice_unit_price": invoice_price,
                    "unit": po_unit,
                },
            }
        )

    if invoice_qty != po_qty:
        discrepancies.append(
            {
                "type": "INVOICE_QUANTITY_MISMATCH",
                "message": f"Purchase order quantity is {po_qty:g} {po_unit}, invoice quantity is {invoice_qty:g} {po_unit}.",
                "evidence": {"ordered": po_qty, "invoiced": invoice_qty, "unit": po_unit},
            }
        )

    comparison_amount = round(received_qty * po_price, 2)
    invoice_amount = round(invoice_qty * invoice_price, 2)
    difference = round(invoice_amount - comparison_amount, 2)
    status = "MATCH" if not discrepancies else "REVIEW_REQUIRED"

    return {
        "status": status,
        "discrepancies": discrepancies,
        "comparison_amount": comparison_amount,
        "invoice_amount": invoice_amount,
        "difference": difference,
        "trust_gate": _trust_gate(status, discrepancies),
    }
