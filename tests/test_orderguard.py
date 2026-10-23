import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from discrepancy_engine import compare_records
from workflow import OrderGuardService


class TestDiscrepancyEngine(unittest.TestCase):
    def test_matching_records_have_no_discrepancies(self):
        result = compare_records(
            {"item": "Chicken", "quantity": 10, "unit": "kg", "unit_price": 12},
            {"item": "Chicken", "quantity": 10, "unit": "kg"},
            {"item": "Chicken", "quantity": 10, "unit": "kg", "unit_price": 12},
        )
        self.assertEqual(result["status"], "MATCH")
        self.assertEqual(result["discrepancies"], [])

    def test_quantity_and_price_mismatches_are_explained(self):
        result = compare_records(
            {"item": "Chicken", "quantity": 10, "unit": "kg", "unit_price": 12},
            {"item": "Chicken", "quantity": 8, "unit": "kg"},
            {"item": "Chicken", "quantity": 10, "unit": "kg", "unit_price": 13},
        )
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        kinds = {d["type"] for d in result["discrepancies"]}
        self.assertEqual(kinds, {"QUANTITY_MISMATCH", "PRICE_MISMATCH"})
        self.assertEqual(result["comparison_amount"], 96.0)
        self.assertEqual(result["invoice_amount"], 130.0)
        self.assertEqual(result["difference"], 34.0)

    def test_incompatible_units_require_human_clarification(self):
        result = compare_records(
            {"item": "Rice", "quantity": 10, "unit": "kg", "unit_price": 4},
            {"item": "Rice", "quantity": 2, "unit": "bags"},
            {"item": "Rice", "quantity": 10, "unit": "kg", "unit_price": 4},
        )
        self.assertEqual(result["status"], "NEEDS_CLARIFICATION")
        self.assertEqual(result["discrepancies"][0]["type"], "UNIT_CLARIFICATION")


class TestApprovalWorkflow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "orderguard.db")
        self.service = OrderGuardService(self.db_path)
        self.case_id = self.service.create_case(
            supplier_message="Delivered 8 kg chicken. Invoice 10 kg at RM13/kg.",
            purchase_order={"item": "Chicken", "quantity": 10, "unit": "kg", "unit_price": 12},
            received={"item": "Chicken", "quantity": 8, "unit": "kg"},
            invoice={"item": "Chicken", "quantity": 10, "unit": "kg", "unit_price": 13},
            submitted_by="staff-demo",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_staff_cannot_approve_consequential_action(self):
        with self.assertRaises(PermissionError):
            self.service.approve_case(self.case_id, actor="staff-demo", role="staff")

    def test_owner_approval_creates_one_outbox_entry(self):
        self.service.approve_case(self.case_id, actor="owner-demo", role="owner")
        self.assertEqual(len(self.service.get_outbox()), 1)
        case = self.service.get_case(self.case_id)
        self.assertEqual(case["status"], "APPROVED")

    def test_repeated_approval_is_idempotent(self):
        self.service.approve_case(self.case_id, actor="owner-demo", role="owner")
        self.service.approve_case(self.case_id, actor="owner-demo", role="owner")
        self.assertEqual(len(self.service.get_outbox()), 1)

    def test_rejection_creates_no_outbox_entry(self):
        self.service.reject_case(self.case_id, actor="owner-demo", role="owner", reason="Need supplier call")
        self.assertEqual(self.service.get_outbox(), [])
        self.assertEqual(self.service.get_case(self.case_id)["status"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
