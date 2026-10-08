import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.clean_data import clean_dataset


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA = PROJECT_ROOT / "data" / "raw"


class CleanDatasetTests(unittest.TestCase):
    def test_cleaned_outputs_preserve_rows_and_resolve_known_quality_issues(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            report = clean_dataset(RAW_DATA, output_dir)

            self.assertEqual(report["dim_customers"]["exact_duplicate_rows_removed"], 50)
            self.assertEqual(report["dim_customers"]["rows_after"], 1500)
            self.assertEqual(report["fact_usage"]["rows_after"], 24756)
            self.assertEqual(report["fact_usage"]["blank_feature_names_replaced"], 942)
            self.assertEqual(report["fact_usage"]["negative_login_count_rows_corrected_to_zero"], 810)
            self.assertEqual(report["fact_subscriptions"]["missing_values_after_cleaning"]["end_date"], 1043)
            self.assertTrue(all(value == 0 for value in report["foreign_key_checks"].values()))

            subscriptions = pd.read_csv(output_dir / "fact_subscriptions.csv")
            dated_subscriptions = pd.read_csv(output_dir / "fact_subscriptions_with_end_dates.csv")
            open_subscriptions = pd.read_csv(output_dir / "fact_subscriptions_open_end_dates.csv")
            usage = pd.read_csv(output_dir / "fact_usage.csv")
            usage_recovery = pd.read_csv(output_dir / "fact_usage_negative_login_recovery.csv")
            customers = pd.read_csv(output_dir / "dim_customers.csv")

            self.assertEqual(set(subscriptions["plan_id"]), {"p_basic", "p_ent", "p_pro"})
            self.assertEqual(set(subscriptions["status"]) - {"active", "canceled", "churned"}, set())
            self.assertEqual(len(open_subscriptions), 1043)
            self.assertEqual(len(dated_subscriptions), 457)
            self.assertEqual(
                set(dated_subscriptions["subscription_id"]).intersection(open_subscriptions["subscription_id"]),
                set(),
            )
            self.assertEqual(
                len(dated_subscriptions) + len(open_subscriptions),
                len(subscriptions),
            )
            self.assertEqual(
                list(open_subscriptions.columns),
                ["subscription_id", "customer_id", "plan_id", "start_date", "status"],
            )
            self.assertTrue(open_subscriptions["status"].eq("active").all())
            self.assertTrue(open_subscriptions["subscription_id"].is_unique)
            self.assertEqual(int(usage["feature_name"].eq("Unknown").sum()), 942)
            self.assertTrue(usage["login_count"].ge(0).all())
            self.assertEqual(len(usage_recovery), 810)
            self.assertTrue(usage_recovery["login_count"].eq(0).all())
            self.assertTrue(usage_recovery["usage_id"].is_unique)
            self.assertEqual(int(customers["country"].eq("Unknown").sum()), 337)
            self.assertEqual(int(customers["industry"].eq("Unknown").sum()), 231)


if __name__ == "__main__":
    unittest.main()