import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.revenue_forecast import build_revenue_forecast


class RevenueForecastTests(unittest.TestCase):
    def test_forecast_compares_baseline_and_trend_and_preserves_negative_rows(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            input_path = root / "payments.csv"
            output_dir = root / "forecast"
            months = pd.period_range("2025-01", periods=12, freq="M")
            amounts = [12000, 11000, 10000, 9000, 8000, 7000, 6000, 5000, 4000, 3000, 2000, 1000]
            payments = pd.DataFrame({
                "payment_id": [f"p{index}" for index in range(12)] + ["negative", "refund"],
                "payment_date": [month.to_timestamp().strftime("%Y-%m-%d") for month in months]
                + ["2025-06-15", "2025-08-15"],
                "amount": amounts + [-100, 50000],
                "payment_status": ["paid"] * 12 + ["paid", "refunded"],
            })
            payments.to_csv(input_path, index=False)

            summary = build_revenue_forecast(input_path, output_dir)

            forecast = pd.read_csv(output_dir / "revenue_forecast.csv")
            observed = pd.read_csv(output_dir / "monthly_paid_revenue.csv")
            self.assertEqual(summary["months_observed"], 12)
            self.assertEqual(summary["negative_paid_amount_rows_excluded_from_forecast"], 1)
            self.assertEqual(summary["directional_trend_scenario"], "decreasing")
            self.assertEqual(summary["selected_forecast_direction"], "decreasing")
            self.assertEqual(forecast["month"].tolist(), ["2026-01", "2026-02", "2026-03"])
            self.assertTrue(forecast["log_linear_trend_scenario"].ge(0).all())
            june = observed.loc[observed["month"].eq("2025-06")].iloc[0]
            self.assertEqual(june["paid_amount_as_recorded"], 6900)
            self.assertEqual(june["positive_paid_amount"], 7000)
            self.assertEqual(june["negative_amount_rows"], 1)
            self.assertEqual(summary["selected_model_by_lowest_mae"], "log_linear_trend")


if __name__ == "__main__":
    unittest.main()