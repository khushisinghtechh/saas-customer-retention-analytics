"""Validate and clean the six raw SaaS dataset tables for SQL import."""

import argparse
import json
from pathlib import Path

import pandas as pd


TABLES = {
    "dim_customers": {
        "primary_key": "customer_id",
        "dates": ["signup_date"],
        "numbers": [],
        "fill_unknown": ["country", "industry"],
        "required": ["customer_id", "signup_date", "country", "industry", "company_size", "segment"],
    },
    "dim_plans": {
        "primary_key": "plan_id",
        "dates": [],
        "numbers": ["monthly_price"],
        "required": ["plan_id", "plan_name", "monthly_price", "billing_cycle"],
    },
    "fact_subscriptions": {
        "primary_key": "subscription_id",
        "dates": ["start_date", "end_date"],
        "numbers": [],
        "required": ["subscription_id", "customer_id", "plan_id", "start_date", "end_date", "status"],
    },
    "fact_payments": {
        "primary_key": "payment_id",
        "dates": ["payment_date"],
        "numbers": ["amount"],
        "required": ["payment_id", "subscription_id", "payment_date", "amount", "payment_status", "payment_method"],
    },
    "fact_support": {
        "primary_key": "ticket_id",
        "dates": ["ticket_date"],
        "numbers": ["resolution_time"],
        "required": ["ticket_id", "customer_id", "ticket_date", "priority", "category", "resolution_time", "status"],
    },
    "fact_usage": {
        "primary_key": "usage_id",
        "dates": ["event_date"],
        "numbers": ["login_count", "session_minutes"],
        "required": ["usage_id", "customer_id", "event_date", "feature_name", "login_count", "session_minutes"],
    },
}

STATUS_MAP = {
    "act": "active",
    "active": "active",
    "active_plan": "active",
    "canceled": "canceled",
    "cancelled": "canceled",
    "churned": "churned",
}


def _clean_table(name: str, input_dir: Path) -> tuple[pd.DataFrame, dict]:
    spec = TABLES[name]
    path = input_dir / f"{name}.csv"
    frame = pd.read_csv(path, dtype="string", keep_default_na=True)
    missing_columns = sorted(set(spec["required"]) - set(frame.columns))
    if missing_columns:
        raise ValueError(f"{path} is missing required columns: {', '.join(missing_columns)}")

    rows_before = len(frame)
    frame.columns = frame.columns.str.strip()
    for column in frame.select_dtypes(include="string").columns:
        frame[column] = frame[column].str.strip().replace("", pd.NA)
    for column in frame.columns:
        if column.endswith("_id"):
            frame[column] = frame[column].str.lower()

    missing_feature_names = 0
    negative_login_count_rows = 0
    usage_recovery_rows = None
    if name == "fact_usage":
        missing_feature_names = int(frame["feature_name"].isna().sum())
        frame["feature_name"] = frame["feature_name"].fillna("Unknown")

    for column in spec["dates"]:
        frame[column] = pd.to_datetime(frame[column], errors="coerce")
    for column in spec["numbers"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if name == "fact_usage":
        negative_logins = frame["login_count"] < 0
        negative_login_count_rows = int(negative_logins.sum())
        usage_recovery_rows = frame.loc[negative_logins].copy()
        usage_recovery_rows["login_count"] = 0
        frame.loc[negative_logins, "login_count"] = 0
    for column in spec.get("fill_unknown", []):
        frame[column] = frame[column].fillna("Unknown")

    if "status" in frame.columns:
        normalized_status = frame["status"].str.lower()
        frame["status"] = normalized_status.map(STATUS_MAP).fillna(normalized_status)
    if "payment_status" in frame.columns:
        frame["payment_status"] = frame["payment_status"].str.lower()

    frame = frame.drop_duplicates().reset_index(drop=True)
    duplicate_rows_removed = rows_before - len(frame)

    primary_key = spec["primary_key"]
    if frame[primary_key].isna().any():
        raise ValueError(f"{path} contains missing values in primary key {primary_key}")
    if frame[primary_key].duplicated().any():
        raise ValueError(f"{path} contains conflicting duplicate values in primary key {primary_key}")

    report = {
        "rows_before": rows_before,
        "rows_after": len(frame),
        "exact_duplicate_rows_removed": duplicate_rows_removed,
        "blank_feature_names_replaced": missing_feature_names,
        "missing_values_after_cleaning": {
            column: int(count)
            for column, count in frame.isna().sum().items()
            if count
        },
    }
    if name == "fact_usage":
        report["negative_login_count_rows_corrected_to_zero"] = negative_login_count_rows
        report["usage_recovery_rows"] = usage_recovery_rows
    return frame, report


def clean_dataset(input_dir: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    cleaned = {}
    report = {}
    for name in TABLES:
        frame, table_report = _clean_table(name, input_dir)
        cleaned[name] = frame
        report[name] = table_report

    customer_ids = set(cleaned["dim_customers"]["customer_id"].dropna())
    plan_ids = set(cleaned["dim_plans"]["plan_id"].dropna())
    subscription_ids = set(cleaned["fact_subscriptions"]["subscription_id"].dropna())
    relationships = {
        "subscriptions_without_customer": int((~cleaned["fact_subscriptions"]["customer_id"].isin(customer_ids)).sum()),
        "subscriptions_without_plan": int((~cleaned["fact_subscriptions"]["plan_id"].isin(plan_ids)).sum()),
        "payments_without_subscription": int((~cleaned["fact_payments"]["subscription_id"].isin(subscription_ids)).sum()),
        "usage_without_customer": int((~cleaned["fact_usage"]["customer_id"].isin(customer_ids)).sum()),
        "support_without_customer": int((~cleaned["fact_support"]["customer_id"].isin(customer_ids)).sum()),
    }
    if any(relationships.values()):
        raise ValueError(f"Foreign-key validation failed: {relationships}")
    report["foreign_key_checks"] = relationships

    for name, frame in cleaned.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False, date_format="%Y-%m-%d")

    usage_recovery_rows = report["fact_usage"].pop("usage_recovery_rows")
    usage_recovery_rows.to_csv(
        output_dir / "fact_usage_negative_login_recovery.csv",
        index=False,
        date_format="%Y-%m-%d",
    )

    subscriptions = cleaned["fact_subscriptions"]
    missing_end_date = subscriptions["end_date"].isna()
    subscriptions.loc[~missing_end_date].to_csv(
        output_dir / "fact_subscriptions_with_end_dates.csv",
        index=False,
        date_format="%Y-%m-%d",
    )
    open_subscriptions = subscriptions.loc[
        missing_end_date,
        ["subscription_id", "customer_id", "plan_id", "start_date", "status"],
    ]
    if not open_subscriptions["status"].eq("active").all():
        raise ValueError("Subscriptions with no end_date must have active status for the NULL-date import file")
    open_subscriptions.to_csv(
        output_dir / "fact_subscriptions_open_end_dates.csv",
        index=False,
        date_format="%Y-%m-%d",
    )
    report["fact_subscriptions"]["open_subscription_rows_for_null_date_import"] = len(open_subscriptions)
    report["fact_subscriptions"]["rows_with_end_dates_for_import"] = int((~missing_end_date).sum())

    report_path = output_dir / "cleaning_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    report = clean_dataset(args.input_dir, args.output_dir)
    for name, details in report.items():
        if name == "foreign_key_checks":
            continue
        print(f"{name}: {details['rows_before']} -> {details['rows_after']} rows")
    print(f"Cleaned tables and report written to {args.output_dir}")


if __name__ == "__main__":
    main()