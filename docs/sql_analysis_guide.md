# MySQL Import and Analysis Guide

## Load the Project

1. Open MySQL Workbench and connect to your local MySQL Server. Enter your password only in Workbench; do not put it in project files or share it in chat.
2. Open and run `sql/01_schema.sql`. This creates the `saas_analytics` database and its six related tables.
3. In the Schemas panel, refresh `saas_analytics`.
4. For each table below, right-click the table and choose **Table Data Import Wizard**. Select the matching cleaned CSV from `data/processed` and import into the existing table.
5. Import in this order so parent rows exist before foreign-key rows:

   1. `dim_customers`
   2. `dim_plans`
   3. `fact_subscriptions`
   4. `fact_payments`
   5. `fact_support`
   6. `fact_usage`

6. Open and run the business queries one at a time: `sql/02_business_analysis.sql` contains the core analysis; `sql/03_advanced_analysis.sql` adds deeper segmentation and time-based analysis.

Do not import `cleaning_report.json`; it is a data-quality report, not a database table. If re-importing into an already populated database, clear existing table rows first or use a fresh schema to avoid primary-key conflicts.

## Subscription Import with Nullable End Dates

`fact_subscriptions.csv` contains 1,043 blank `end_date` values for active subscriptions. MySQL Workbench's wizard may send these as empty strings, which strict MySQL date columns reject. The cleaner therefore creates two import-safe subsets:

- `fact_subscriptions_with_end_dates.csv`: 457 rows with valid end dates and all six columns.
- `fact_subscriptions_open_end_dates.csv`: 1,043 active rows without an `end_date` column. Because the target column is nullable, MySQL stores its value as `NULL`.

For a fresh database, import the 457-row file first and then the 1,043-row file, both into the existing `fact_subscriptions` table. In the current database used during guided setup, the 457 valid-date rows are already loaded, so import **only** `fact_subscriptions_open_end_dates.csv`. Do not re-import the full `fact_subscriptions.csv` or the 457-row subset; that would duplicate primary keys.

After both parts are loaded, verify:

```sql
SELECT COUNT(*) FROM saas_analytics.fact_subscriptions;
SELECT COUNT(*) FROM saas_analytics.fact_subscriptions WHERE end_date IS NULL;
```

Expected counts are 1,500 total and 1,043 with a null end date.

## Usage Import with Invalid Login Counts

The raw usage file contains 810 negative `login_count` values, which MySQL rejects for the `INT UNSIGNED` column. A login count cannot be negative, so the cleaner keeps the raw source unchanged, records `0` in the cleaned copy, and writes `fact_usage_negative_login_recovery.csv` with the 810 corrected rows.

For a fresh database, import the corrected full `fact_usage.csv`. For the current guided database, **23,946 valid rows are already present**, so import only `fact_usage_negative_login_recovery.csv` into the existing `saas_analytics.fact_usage` table. Do not re-import the full usage CSV or the existing rows will hit duplicate `usage_id` values.

Verify the final usage count:

```sql
SELECT COUNT(*) FROM saas_analytics.fact_usage;
```

Expected: 24,756 rows.

## What Each Query Means

- **DAU/MAU:** Counts distinct customers with usage rows. Average DAU includes dates that have logged usage; days without a usage row are absent from the source.
- **Feature usage vs churn:** Aggregates to one row per customer per feature before calculating churn association, so frequent users do not get extra weight. Association does not prove causation.
- **Plan churn:** Reports the churned-status share among subscriptions in this synthetic sample, not a time-adjusted company churn benchmark.
- **Payment outcomes:** Separates paid and refunded amounts from failed-payment counts by month and plan.
- **Cohort retention:** Counts signup-cohort customers with at least one usage record in each later observed month.
- **Payment-segment engagement:** Compares usage for customers with and without any successful payment. This is not a trial conversion funnel.
- **At-risk list:** Uses a transparent rule for inactivity, failed payments, and support-ticket volume. It is for review, not a trained prediction model.
- **Customer value ranking:** Ranks recorded successful payments; it is not a forecast of lifetime value.

The source has no trial flag, trial dates, conversion event, or acquisition channel. Trial-to-paid conversion and channel conversion are unavailable and must not be inferred or invented.

## Validation Status

The SQL files have editor diagnostics with no reported errors. The Python cleaning test passes. Live SQL execution has not been verified because the local MySQL server requires the user's password; run the scripts in Workbench to validate them against the local server.