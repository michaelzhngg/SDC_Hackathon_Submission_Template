import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from discrepancy_engine import compare_records
from workflow import OrderGuardService


class TestTrustGate(unittest.TestCase):
    def test_unit_ambiguity_is_blocked_by_trust_gate(self):
        result = compare_records(
            {"item": "Rice", "quantity": 10, "unit": "kg", "unit_price": 4},
            {"item": "Rice", "quantity": 2, "unit": "bags"},
            {"item": "Rice", "quantity": 10, "unit": "kg", "unit_price": 4},
        )
        self.assertEqual(result["trust_gate"]["level"], "BLOCKED")
        self.assertFalse(result["trust_gate"]["approval_allowed"])

    def test_human_clarification_recomputes_and_unlocks_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = OrderGuardService(str(Path(tmp) / "db.sqlite"))
            case_id = service.create_case(
                "Delivered two bags rice.",
                {"item": "Rice", "quantity": 10, "unit": "kg", "unit_price": 4},
                {"item": "Rice", "quantity": 2, "unit": "bags"},
                {"item": "Rice", "quantity": 10, "unit": "kg", "unit_price": 4},
                "staff-demo",
            )
            self.assertEqual(service.get_case(case_id)["status"], "NEEDS_CLARIFICATION")
            with self.assertRaises(ValueError):
                service.approve_case(case_id, "owner-demo", "owner")

            service.clarify_case(
                case_id,
                actor="owner-demo",
                received_quantity=8,
                received_unit="kg",
            )
            updated = service.get_case(case_id)
            self.assertEqual(updated["status"], "PENDING_APPROVAL")
            self.assertTrue(updated["comparison"]["trust_gate"]["approval_allowed"])
            actions = [item["action"] for item in service.get_activity(case_id)]
            self.assertIn("CLARIFICATION_CONFIRMED", actions)


if __name__ == "__main__":
    unittest.main()
