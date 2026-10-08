"""Build dashboard-ready aggregates and flag potentially incomplete months."""

import argparse
import json
from pathlib import Path

import pandas as pd


def build_dashboard_metrics(input_dir: Path, output_dir: Path) -> dict:
    """Write verified dashboard aggregates from the cleaned CSV tables."""
    customers = pd.read_csv(input_dir / "dim_customers.csv")
    plans = pd.read_csv(input_dir / "dim_plans.csv")
    subscriptions = pd.read_csv(input_dir / "fact_subscriptions.csv")
    usage = pd.read_csv(input_dir / "fact_usage.csv", parse_dates=["event_date"])
    if usage.empty:
        raise ValueError("fact_usage.csv has no rows; monthly metrics cannot be calculated")

    latest_event_date = usage["event_date"].max()
    latest_month = latest_event_date.to_period("M")
    usage["month"] = usage["event_date"].dt.to_period("M")

    monthly_active_users = (
        usage.groupby("month", as_index=False)
        .agg(active_users=("customer_id", "nunique"), usage_records=("usage_id", "count"))
    )
    monthly_active_users["month"] = monthly_active_users["month"].astype(str)
    monthly_active_users["likely_partial_month"] = monthly_active_users["month"].eq(str(latest_month)) & (
        latest_event_date.day < latest_event_date.days_in_month
    )

    feature_adoption = (
        usage.groupby("feature_name", dropna=False, as_index=False)
        .agg(usage_records=("usage_id", "count"), unique_users=("customer_id", "nunique"))
        .sort_values("unique_users", ascending=False)
    )

    plan_status = subscriptions.merge(plans[["plan_id", "plan_name"]], on="plan_id", validate="many_to_one")
    plan_status = (
        plan_status.groupby(["plan_name", "status"], as_index=False)
        .agg(subscriptions=("subscription_id", "nunique"))
    )
    plan_status["plan_subscriptions"] = plan_status.groupby("plan_name")["subscriptions"].transform("sum")
    plan_status["share_within_plan"] = plan_status["subscriptions"] / plan_status["plan_subscriptions"]

    churned_subscriptions = int(subscriptions["status"].eq("churned").sum())
    subscription_count = int(subscriptions["subscription_id"].nunique())
    summary = {
        "total_customers": int(customers["customer_id"].nunique()),
        "total_subscriptions": subscription_count,
        "churned_subscriptions": churned_subscriptions,
        "observed_churn_rate": churned_subscriptions / subscription_count if subscription_count else None,
        "last_usage_event_date": latest_event_date.strftime("%Y-%m-%d"),
        "latest_usage_month": str(latest_month),
        "latest_month_likely_partial": latest_event_date.day < latest_event_date.days_in_month,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    monthly_active_users.to_csv(output_dir / "monthly_active_users.csv", index=False)
    feature_adoption.to_csv(output_dir / "feature_adoption.csv", index=False)
    plan_status.to_csv(output_dir / "subscription_status_by_plan.csv", index=False)
    (output_dir / "dashboard_audit.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/dashboard_metrics"))
    args = parser.parse_args()
    summary = build_dashboard_metrics(args.input_dir, args.output_dir)
    print(json.dumps(summary, indent=2))
    print(f"Dashboard aggregates written to {args.output_dir}")


if __name__ == "__main__":
    main()