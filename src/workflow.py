from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List

from discrepancy_engine import compare_records


class OrderGuardService:
    def __init__(self, db_path: str = "orderguard.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._db() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_name TEXT NOT NULL DEFAULT 'Demo Supplier',
                    supplier_message TEXT NOT NULL,
                    purchase_order TEXT NOT NULL,
                    received TEXT NOT NULL,
                    invoice TEXT NOT NULL,
                    comparison TEXT NOT NULL,
                    proposed_action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    submitted_by TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id INTEGER NOT NULL,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS outbox (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id INTEGER NOT NULL UNIQUE,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(cases)").fetchall()}
            if "supplier_name" not in columns:
                conn.execute(
                    "ALTER TABLE cases ADD COLUMN supplier_name TEXT NOT NULL DEFAULT 'Demo Supplier'"
                )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _log(
        self,
        conn: sqlite3.Connection,
        case_id: int,
        actor: str,
        action: str,
        details: str,
    ) -> None:
        conn.execute(
            "INSERT INTO activity_log(case_id, actor, action, details, created_at) VALUES (?, ?, ?, ?, ?)",
            (case_id, actor, action, details, self._now()),
        )

    @staticmethod
    def _status_for(comparison: Dict[str, Any]) -> str:
        return {
            "MATCH": "MATCHED",
            "NEEDS_CLARIFICATION": "NEEDS_CLARIFICATION",
            "REVIEW_REQUIRED": "PENDING_APPROVAL",
        }[comparison["status"]]

    @staticmethod
    def _propose_action(comparison: Dict[str, Any]) -> str:
        if comparison["status"] == "MATCH":
            return "No supplier clarification is required."
        if comparison["status"] == "NEEDS_CLARIFICATION":
            return "Confirm the unit or missing information before any supplier action."
        labels = [
            discrepancy["type"].replace("_", " ").title()
            for discrepancy in comparison["discrepancies"]
        ]
        return "Please verify the following discrepancy/discrepancies: " + ", ".join(labels) + "."

    def create_case(
        self,
        supplier_message: str,
        purchase_order: Dict[str, Any],
        received: Dict[str, Any],
        invoice: Dict[str, Any],
        submitted_by: str,
        supplier_name: str = "Demo Supplier",
    ) -> int:
        comparison = compare_records(purchase_order, received, invoice)
        proposed_action = self._propose_action(comparison)
        supplier_name = supplier_name.strip() or "Demo Supplier"

        with self._db() as conn:
            cur = conn.execute(
                """INSERT INTO cases
                (supplier_name, supplier_message, purchase_order, received, invoice, comparison,
                 proposed_action, status, submitted_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    supplier_name,
                    supplier_message,
                    json.dumps(purchase_order),
                    json.dumps(received),
                    json.dumps(invoice),
                    json.dumps(comparison),
                    proposed_action,
                    self._status_for(comparison),
                    submitted_by,
                    self._now(),
                ),
            )
            case_id = int(cur.lastrowid)
            self._log(
                conn,
                case_id,
                submitted_by,
                "CASE_SUBMITTED",
                f"Records submitted for comparison for supplier {supplier_name}",
            )
            self._log(conn, case_id, "system", "COMPARISON_COMPLETED", comparison["status"])
            if comparison["status"] == "NEEDS_CLARIFICATION":
                self._log(
                    conn,
                    case_id,
                    "system",
                    "TRUST_GATE_BLOCKED",
                    "Approval blocked until a human confirms ambiguous data",
                )
        return case_id

    def get_case(self, case_id: int) -> Dict[str, Any]:
        with self._db() as conn:
            row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
        if row is None:
            raise KeyError(f"Case {case_id} not found")
        result = dict(row)
        for field in ("purchase_order", "received", "invoice", "comparison"):
            result[field] = json.loads(result[field])
        return result

    def list_cases(self) -> List[Dict[str, Any]]:
        with self._db() as conn:
            rows = conn.execute(
                """SELECT id, supplier_name, status, submitted_by, created_at,
                proposed_action, comparison FROM cases ORDER BY id DESC"""
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["comparison"] = json.loads(item["comparison"])
            result.append(item)
        return result

    def clarify_case(
        self,
        case_id: int,
        actor: str,
        received_quantity: float,
        received_unit: str,
    ) -> None:
        with self._db() as conn:
            row = conn.execute(
                "SELECT status, purchase_order, received, invoice FROM cases WHERE id = ?",
                (case_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Case {case_id} not found")
            if row["status"] != "NEEDS_CLARIFICATION":
                raise ValueError(f"Case cannot be clarified from status {row['status']}")

            purchase_order = json.loads(row["purchase_order"])
            received = json.loads(row["received"])
            invoice = json.loads(row["invoice"])
            received["quantity"] = float(received_quantity)
            received["unit"] = received_unit.strip()

            comparison = compare_records(purchase_order, received, invoice)
            proposed_action = self._propose_action(comparison)
            conn.execute(
                "UPDATE cases SET received = ?, comparison = ?, proposed_action = ?, status = ? WHERE id = ?",
                (
                    json.dumps(received),
                    json.dumps(comparison),
                    proposed_action,
                    self._status_for(comparison),
                    case_id,
                ),
            )
            self._log(
                conn,
                case_id,
                actor,
                "CLARIFICATION_CONFIRMED",
                f"Human confirmed receiving record as {float(received_quantity):g} {received_unit.strip()}.",
            )
            self._log(conn, case_id, "system", "COMPARISON_RECALCULATED", comparison["status"])

    def approve_case(self, case_id: int, actor: str, role: str) -> None:
        if role != "owner":
            raise PermissionError("Only an owner may approve a consequential action")
        with self._db() as conn:
            row = conn.execute(
                "SELECT status, proposed_action, comparison FROM cases WHERE id = ?",
                (case_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Case {case_id} not found")
            if row["status"] == "APPROVED":
                return
            comparison = json.loads(row["comparison"])
            if not comparison.get("trust_gate", {}).get("approval_allowed", False):
                raise ValueError("Trust Gate blocks approval until the case is safe to review")
            if row["status"] != "PENDING_APPROVAL":
                raise ValueError(f"Case cannot be approved from status {row['status']}")
            conn.execute("UPDATE cases SET status = 'APPROVED' WHERE id = ?", (case_id,))
            conn.execute(
                "INSERT OR IGNORE INTO outbox(case_id, message, created_at) VALUES (?, ?, ?)",
                (case_id, row["proposed_action"], self._now()),
            )
            self._log(conn, case_id, actor, "APPROVED", "Owner approved the proposed clarification")
            self._log(
                conn,
                case_id,
                "system",
                "OUTBOX_CREATED",
                "Simulated supplier message added to outbox",
            )

    def reject_case(self, case_id: int, actor: str, role: str, reason: str) -> None:
        if role != "owner":
            raise PermissionError("Only an owner may reject a consequential action")
        with self._db() as conn:
            row = conn.execute("SELECT status FROM cases WHERE id = ?", (case_id,)).fetchone()
            if row is None:
                raise KeyError(f"Case {case_id} not found")
            if row["status"] != "PENDING_APPROVAL":
                raise ValueError(f"Case cannot be rejected from status {row['status']}")
            conn.execute("UPDATE cases SET status = 'REJECTED' WHERE id = ?", (case_id,))
            self._log(conn, case_id, actor, "REJECTED", reason or "No reason provided")

    def get_outbox(self) -> List[Dict[str, Any]]:
        with self._db() as conn:
            rows = conn.execute(
                "SELECT id, case_id, message, created_at FROM outbox ORDER BY id DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def get_activity(self, case_id: int) -> List[Dict[str, Any]]:
        with self._db() as conn:
            rows = conn.execute(
                "SELECT actor, action, details, created_at FROM activity_log WHERE case_id = ? ORDER BY id ASC",
                (case_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_supplier_insight(self, case_id: int) -> Dict[str, Any]:
        """Explain repeat exceptions without making an automated supplier judgment."""
        current = self.get_case(case_id)
        supplier_name = current.get("supplier_name") or "Demo Supplier"
        item = str(current["purchase_order"].get("item", "")).strip().lower()
        current_types = {
            discrepancy["type"]
            for discrepancy in current["comparison"].get("discrepancies", [])
        }

        previous_exception_cases = 0
        prior_types = set()
        with self._db() as conn:
            rows = conn.execute(
                """SELECT id, purchase_order, comparison FROM cases
                WHERE id <> ? AND lower(supplier_name) = lower(?) ORDER BY id ASC""",
                (case_id, supplier_name),
            ).fetchall()

        for row in rows:
            purchase_order = json.loads(row["purchase_order"])
            if str(purchase_order.get("item", "")).strip().lower() != item:
                continue
            comparison = json.loads(row["comparison"])
            if comparison.get("status") != "MATCH":
                previous_exception_cases += 1
                prior_types.update(
                    discrepancy["type"]
                    for discrepancy in comparison.get("discrepancies", [])
                )

        recurring_types = sorted(current_types & prior_types)
        repeat_issue = previous_exception_cases > 0 and bool(recurring_types)
        difference = current["comparison"].get("difference")
        money_at_risk = round(abs(float(difference)), 2) if difference is not None else 0.0

        if repeat_issue:
            playbook = [
                "Review the current evidence before contacting the supplier.",
                "Reference the recurring discrepancy type in the clarification.",
                "Keep the final action owner-approved and logged for follow-up.",
            ]
        elif current["comparison"].get("status") == "REVIEW_REQUIRED":
            playbook = [
                "Review the quantity and price evidence.",
                "Approve or reject the proposed clarification before any supplier action.",
            ]
        elif current["comparison"].get("status") == "NEEDS_CLARIFICATION":
            playbook = ["Confirm the ambiguous unit or missing value before continuing."]
        else:
            playbook = ["No supplier action is required because the records match."]

        return {
            "supplier_name": supplier_name,
            "item": current["purchase_order"].get("item", ""),
            "previous_exception_cases": previous_exception_cases,
            "repeat_issue": repeat_issue,
            "recurring_types": recurring_types,
            "money_at_risk": money_at_risk,
            "playbook": playbook,
        }

    def get_dashboard_summary(self) -> Dict[str, Any]:
        cases = self.list_cases()
        status_counts: Dict[str, int] = {}
        discrepancy_counts: Dict[str, int] = {}
        money_at_risk = 0.0
        repeat_cases = 0

        for case in cases:
            status_counts[case["status"]] = status_counts.get(case["status"], 0) + 1
            if (
                case["status"] in ("PENDING_APPROVAL", "NEEDS_CLARIFICATION")
                and case["comparison"].get("difference") is not None
            ):
                money_at_risk += abs(float(case["comparison"]["difference"]))
            if self.get_supplier_insight(case["id"])["repeat_issue"]:
                repeat_cases += 1
            for discrepancy in case["comparison"].get("discrepancies", []):
                name = discrepancy["type"]
                discrepancy_counts[name] = discrepancy_counts.get(name, 0) + 1

        return {
            "total": len(cases),
            "pending": status_counts.get("PENDING_APPROVAL", 0),
            "blocked": status_counts.get("NEEDS_CLARIFICATION", 0),
            "approved": status_counts.get("APPROVED", 0),
            "matched": status_counts.get("MATCHED", 0),
            "discrepancies": discrepancy_counts,
            "money_at_risk": round(money_at_risk, 2),
            "repeat_cases": repeat_cases,
        }
