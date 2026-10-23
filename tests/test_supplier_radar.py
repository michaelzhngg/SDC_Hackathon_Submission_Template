import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from supplier_radar import build_supplier_radar


class TestSupplierRadar(unittest.TestCase):
    def test_groups_supplier_exceptions_and_open_risk(self):
        cases = [
            {
                "id": 1,
                "supplier_name": "FreshFarm Foods",
                "status": "PENDING_APPROVAL",
                "comparison": {
                    "difference": 34.0,
                    "discrepancies": [
                        {"type": "QUANTITY_MISMATCH"},
                        {"type": "PRICE_MISMATCH"},
                    ],
                },
            },
            {
                "id": 2,
                "supplier_name": "FreshFarm Foods",
                "status": "PENDING_APPROVAL",
                "comparison": {
                    "difference": 34.0,
                    "discrepancies": [{"type": "QUANTITY_MISMATCH"}],
                },
            },
            {
                "id": 3,
                "supplier_name": "Golden Egg Trading",
                "status": "MATCHED",
                "comparison": {"difference": 0.0, "discrepancies": []},
            },
        ]
        insights = {
            1: {"repeat_issue": False},
            2: {"repeat_issue": True},
            3: {"repeat_issue": False},
        }

        radar = build_supplier_radar(cases, lambda case_id: insights[case_id])

        self.assertEqual(radar[0]["supplier_name"], "FreshFarm Foods")
        self.assertEqual(radar[0]["total_cases"], 2)
        self.assertEqual(radar[0]["exception_cases"], 2)
        self.assertEqual(radar[0]["repeat_cases"], 1)
        self.assertEqual(radar[0]["money_at_risk"], 68.0)
        self.assertEqual(radar[0]["top_issue"], "QUANTITY_MISMATCH")
        self.assertEqual(radar[0]["risk_percent"], 100)
        self.assertEqual(radar[1]["risk_percent"], 0)

    def test_approved_cases_do_not_count_as_open_money_at_risk(self):
        cases = [
            {
                "id": 4,
                "supplier_name": "FreshFarm Foods",
                "status": "APPROVED",
                "comparison": {
                    "difference": 50.0,
                    "discrepancies": [{"type": "PRICE_MISMATCH"}],
                },
            }
        ]

        radar = build_supplier_radar(cases, lambda _: {"repeat_issue": False})

        self.assertEqual(radar[0]["money_at_risk"], 0.0)


if __name__ == "__main__":
    unittest.main()
