# SaaS Product Usage & Customer Retention Analytics

## Project Status

Dataset selected and downloaded. This is a synthetic Kaggle learning dataset, not real customer data. Raw CSVs are in `data/raw`; cleaned outputs are in `data/processed`.

## Business Question

Which user behaviors are associated with subscription conversion or customer drop-off?

The analysis is intended to cover acquisition, engagement, login/activity frequency, feature usage, trial-to-paid conversion, subscription plans, churn, retention cohorts, and high-value or at-risk users. Findings will only be reported when the selected dataset contains the required fields.

## Agreed Constraints

- Use a real, publicly available dataset where possible.
- Do not fabricate missing activity, trial, conversion, or churn fields.
- Keep the downloaded data under approximately 100 MB and the initial analysis to around 100,000 rows or fewer.
- Document unsupported metrics and dataset limitations clearly.

## Planned Technology

- Python and Pandas for data inspection, cleaning, and transformation
- MySQL for relational storage and business analysis
- Power BI for interactive reporting
- GitHub for portfolio documentation

## Planned Workflow

1. Select and document a laptop-friendly dataset.
2. Clean and validate raw tables with Python.
3. Create the MySQL model and import cleaned tables.
4. Run SQL business analyses and cross-check their results.
5. Build a four-page Power BI dashboard using only supported metrics.
6. Write evidence-based insights and business recommendations.

## Learning Along the Way

Each step will explain what is being done, why it matters, and how to describe the decision in an interview.

## Dataset Decision

The selected [Kaggle SaaS Customer Churn Dataset](https://www.kaggle.com/datasets/mounikabusi/saas-customer-churn-dataset) is explicitly synthetic, six related CSV tables, and about 1.67 MB extracted. It fits the laptop limit and supports usage, subscription, payment, support, and churn analysis. It does not contain trial conversion or acquisition channel fields; those metrics will be marked unavailable. See [Dataset Source](docs/dataset_source.md), [Dataset Research](docs/dataset_research.md), and the [Data Dictionary](docs/data_dictionary.md) for attribution, comparison, schema, and limitations.

## Current Progress

- Dataset downloaded, inspected, and extracted to `data/raw`.
- Python cleaning pipeline created; cleaned CSVs and a quality report are in `data/processed`.
- Python dashboard audit cross-checks customer and subscription totals, observed churn, unique feature users, and incomplete latest-month activity. The current usage extract ends on December 17, 2025, so December is flagged as partial.
- Cleaning handles 810 invalid negative login counts transparently and generates a recovery CSV for the partially loaded MySQL usage table.
- Integration test passes for duplicate removal, status/ID normalization, missing values, and foreign-key integrity.
- MySQL schema and business-analysis queries are written; run them in Workbench to validate against the password-protected local server.
- Power BI model, measures, page design, and interpretation guidance are in [Power BI Dashboard Guide](docs/power_bi_guide.md).

## Project Files

- `src/clean_data.py` — Pandas cleaning, validation, and import-safe recovery files for nullable dates and invalid negative counts
- `src/dashboard_metrics.py` — verified monthly active users, feature adoption, plan status shares, and a partial-month warning for Power BI
- `tests/test_clean_data.py` — focused data-quality regression test
- `tests/test_dashboard_metrics.py` — dashboard metric and partial-month regression test
- `requirements.txt` — Python dependency for rerunning the cleaning pipeline
- `docs/dataset_source.md` — dataset source, synthetic-data disclosure, and license note
- `sql/01_schema.sql` — MySQL database and relational tables
- `sql/02_business_analysis.sql` — DAU/MAU, feature/churn association, plan, payments, cohort, at-risk, and customer-value queries
- `sql/03_advanced_analysis.sql` — signup cohorts, adoption, engagement quartiles, support, payment rates, MoM MAU, pre-end activity, and subscription duration
- `docs/data_dictionary.md` — table grain, keys, column meanings, data issues, and metric limitations
- `docs/insights.md` — sample findings, business decisions, and interview explanation (clearly labeled synthetic)
- `docs/sql_analysis_guide.md` — MySQL import order and query interpretation
- `docs/power_bi_guide.md` — Power BI relationships, DAX measures, and four report pages

## Rerun the Python Checks

From the project root, run the cleaning pipeline first, then build the dashboard aggregates:

```powershell
python -m src.clean_data
python -m src.dashboard_metrics
python -m unittest discover -s tests
```

The dashboard audit writes `monthly_active_users.csv`, `feature_adoption.csv`, `subscription_status_by_plan.csv`, and `dashboard_audit.json` under `data/processed/dashboard_metrics`. Use `unique_users` rather than `usage_records` when charting customers by feature. Exclude or clearly flag the latest partial month when interpreting trends.