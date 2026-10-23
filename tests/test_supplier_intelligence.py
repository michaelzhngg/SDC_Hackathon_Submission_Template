import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from workflow import OrderGuardService


class TestSupplierIntelligence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.service = OrderGuardService(str(Path(self.tmp.name) / "db.sqlite"))

    def tearDown(self):
        self.tmp.cleanup()

    def _case(self, supplier="FreshFarm", received=8, invoice_price=13):
        return self.service.create_case(
            "Delivered chicken.",
            {"item": "Chicken", "quantity": 10, "unit": "kg", "unit_price": 12},
            {"item": "Chicken", "quantity": received, "unit": "kg"},
            {"item": "Chicken", "quantity": 10, "unit": "kg", "unit_price": invoice_price},
            "staff-demo",
            supplier_name=supplier,
        )

    def test_repeat_issue_memory_detects_prior_exception_for_same_supplier_and_item(self):
        self._case()
        current = self._case()
        insight = self.service.get_supplier_insight(current)
        self.assertTrue(insight["repeat_issue"])
        self.assertEqual(insight["previous_exception_cases"], 1)
        self.assertIn("QUANTITY_MISMATCH", insight["recurring_types"])
        self.assertIn("PRICE_MISMATCH", insight["recurring_types"])

    def test_different_supplier_is_not_counted_as_repeat(self):
        self._case("FreshFarm")
        current = self._case("OtherFoods")
        insight = self.service.get_supplier_insight(current)
        self.assertFalse(insight["repeat_issue"])
        self.assertEqual(insight["previous_exception_cases"], 0)

    def test_dashboard_reports_open_money_at_risk(self):
        self._case()
        self._case()
        summary = self.service.get_dashboard_summary()
        self.assertEqual(summary["money_at_risk"], 68.0)


if __name__ == "__main__":
    unittest.main()
