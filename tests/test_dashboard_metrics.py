import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.dashboard_metrics import build_dashboard_metrics


class DashboardMetricsTests(unittest.TestCase):
    def test_metrics_use_unique_users_and_flag_partial_latest_month(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            input_dir = root / "input"
            output_dir = root / "output"
            input_dir.mkdir()

            pd.DataFrame({"customer_id": ["c1", "c2"]}).to_csv(input_dir / "dim_customers.csv", index=False)
            pd.DataFrame({"plan_id": ["p1", "p2"], "plan_name": ["Pro", "Basic"]}).to_csv(
                input_dir / "dim_plans.csv", index=False
            )
            pd.DataFrame({
                "subscription_id": ["s1", "s2", "s3"],
                "plan_id": ["p1", "p1", "p2"],
                "status": ["active", "churned", "active"],
            }).to_csv(input_dir / "fact_subscriptions.csv", index=False)
            pd.DataFrame({
                "usage_id": ["u1", "u2", "u3", "u4"],
                "customer_id": ["c1", "c1", "c2", "c2"],
                "event_date": ["2025-11-30", "2025-12-01", "2025-12-17", "2025-12-17"],
                "feature_name": ["dashboard_view", "dashboard_view", "dashboard_view", "Unknown"],
            }).to_csv(input_dir / "fact_usage.csv", index=False)

            summary = build_dashboard_metrics(input_dir, output_dir)

            monthly = pd.read_csv(output_dir / "monthly_active_users.csv")
            features = pd.read_csv(output_dir / "feature_adoption.csv").set_index("feature_name")
            plan_status = pd.read_csv(output_dir / "subscription_status_by_plan.csv")
            self.assertEqual(summary["total_customers"], 2)
            self.assertEqual(summary["observed_churn_rate"], 1 / 3)
            self.assertEqual(summary["last_usage_event_date"], "2025-12-17")
            self.assertTrue(summary["latest_month_likely_partial"])
            self.assertEqual(monthly.loc[monthly["month"].eq("2025-12"), "active_users"].iloc[0], 2)
            self.assertTrue(monthly.loc[monthly["month"].eq("2025-12"), "likely_partial_month"].iloc[0])
            self.assertEqual(features.loc["dashboard_view", "usage_records"], 3)
            self.assertEqual(features.loc["dashboard_view", "unique_users"], 2)
            self.assertAlmostEqual(
                plan_status.loc[plan_status["plan_name"].eq("Pro"), "share_within_plan"].sum(), 1.0
            )


if __name__ == "__main__":
    unittest.main()