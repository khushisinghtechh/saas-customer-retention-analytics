"""Forecast recorded paid-payment amounts and compare them with a naive baseline."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def _trend_forecast(values: np.ndarray, window: int, horizon: int) -> np.ndarray:
    recent_values = np.maximum(values[-window:], 0)
    positions = np.arange(window, dtype=float)
    slope, intercept = np.polyfit(positions, np.log1p(recent_values), 1)
    future_positions = np.arange(window, window + horizon, dtype=float)
    return np.maximum(np.expm1(intercept + slope * future_positions), 0)


def build_revenue_forecast(
    input_path: Path,
    output_dir: Path,
    horizon: int = 3,
    window: int = 6,
) -> dict:
    """Write monthly paid amounts, a trend scenario, and a baseline forecast."""
    if horizon < 1:
        raise ValueError("horizon must be at least 1")
    if window < 3:
        raise ValueError("window must be at least 3 months")

    payments = pd.read_csv(input_path)
    required_columns = {"payment_id", "payment_date", "amount", "payment_status"}
    missing_columns = sorted(required_columns - set(payments.columns))
    if missing_columns:
        raise ValueError(f"{input_path} is missing required columns: {', '.join(missing_columns)}")

    payments["payment_date"] = pd.to_datetime(payments["payment_date"], errors="coerce")
    payments["amount"] = pd.to_numeric(payments["amount"], errors="coerce")
    paid_mask = payments["payment_status"].astype("string").str.strip().str.lower().eq("paid")
    paid = payments.loc[paid_mask].copy()
    if paid.empty:
        raise ValueError("No paid payment records were found")
    if paid["payment_date"].isna().any() or paid["amount"].isna().any():
        raise ValueError("Paid payment records contain invalid dates or amounts")

    paid["month"] = paid["payment_date"].dt.to_period("M")
    observed = paid.groupby("month").agg(
        paid_amount_as_recorded=("amount", "sum"),
        positive_paid_amount=("amount", lambda amounts: float(amounts[amounts.gt(0)].sum())),
        paid_transactions=("payment_id", "nunique"),
        negative_amount_rows=("amount", lambda amounts: int(amounts.lt(0).sum())),
    )
    months = pd.period_range(observed.index.min(), observed.index.max(), freq="M")
    observed = observed.reindex(months, fill_value=0).rename_axis("month").reset_index()
    observed["month"] = observed["month"].astype(str)
    values = observed["positive_paid_amount"].to_numpy(dtype=float)

    minimum_backtest_months = max(window + 2, 9)
    if len(values) < minimum_backtest_months + 3:
        raise ValueError(
            f"Need at least {minimum_backtest_months + 3} observed months for a rolling backtest; "
            f"found {len(values)}"
        )

    baseline_errors = []
    trend_errors = []
    for test_index in range(minimum_backtest_months, len(values)):
        training_values = values[:test_index]
        actual = values[test_index]
        baseline_errors.append(abs(actual - training_values[-1]))
        trend_prediction = _trend_forecast(training_values, window, horizon=1)[0]
        trend_errors.append(abs(actual - trend_prediction))

    baseline_mae = float(np.mean(baseline_errors))
    trend_mae = float(np.mean(trend_errors))
    selected_model = "last_month_baseline" if baseline_mae <= trend_mae else "log_linear_trend"
    baseline_forecast = np.full(horizon, values[-1], dtype=float)
    trend_scenario = _trend_forecast(values, window, horizon)
    selected_forecast = baseline_forecast if selected_model == "last_month_baseline" else trend_scenario

    last_month = pd.Period(observed["month"].iloc[-1], freq="M")
    future_months = pd.period_range(last_month + 1, periods=horizon, freq="M")
    forecast = pd.DataFrame({
        "month": future_months.astype(str),
        "last_month_baseline": baseline_forecast.round(2),
        "log_linear_trend_scenario": trend_scenario.round(2),
        "selected_forecast": selected_forecast.round(2),
        "selected_model": selected_model,
    })

    previous_three_mean = float(np.mean(values[-6:-3]))
    recent_three_mean = float(np.mean(values[-3:]))
    recent_change = (
        (recent_three_mean - previous_three_mean) / abs(previous_three_mean)
        if previous_three_mean
        else None
    )
    trend_direction = "decreasing" if trend_scenario[-1] < values[-1] else (
        "increasing" if trend_scenario[-1] > values[-1] else "stable"
    )
    selected_direction = "decreasing" if selected_forecast[-1] < values[-1] else (
        "increasing" if selected_forecast[-1] > values[-1] else "stable"
    )
    summary = {
        "measure": "positive paid-payment amounts; not verified net or recognized sales",
        "observed_start_month": observed["month"].iloc[0],
        "observed_end_month": observed["month"].iloc[-1],
        "months_observed": len(observed),
        "last_observed_paid_amount": round(float(values[-1]), 2),
        "directional_trend_scenario": trend_direction,
        "selected_forecast_direction": selected_direction,
        "latest_three_month_mean_change_vs_prior_three_months_pct": (
            round(recent_change * 100, 2) if recent_change is not None else None
        ),
        "negative_paid_amount_rows_excluded_from_forecast": int(paid["amount"].lt(0).sum()),
        "rolling_one_month_backtest_months": len(baseline_errors),
        "last_month_baseline_mae": round(baseline_mae, 2),
        "log_linear_trend_mae": round(trend_mae, 2),
        "selected_model_by_lowest_mae": selected_model,
        "forecast_horizon_months": horizon,
        "data_disclosure": "Source dataset is synthetic; forecast is exploratory, not a real-sales prediction.",
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    observed.to_csv(output_dir / "monthly_paid_revenue.csv", index=False)
    forecast.to_csv(output_dir / "revenue_forecast.csv", index=False)
    (output_dir / "revenue_forecast_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/processed/fact_payments.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("report/revenue_forecast"))
    parser.add_argument("--horizon", type=int, default=3)
    parser.add_argument("--window", type=int, default=6)
    args = parser.parse_args()
    summary = build_revenue_forecast(args.input, args.output_dir, args.horizon, args.window)
    print(json.dumps(summary, indent=2))
    print(f"Forecast outputs written to {args.output_dir}")


if __name__ == "__main__":
    main()