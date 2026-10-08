# Power BI Dashboard Guide

## Connect and Model

Use Power BI Desktop's MySQL database connector to connect to the local MySQL Server and select `saas_analytics`. Import the six dimension/fact tables. Do not put the MySQL password in this repository or in project files.

Create these single-direction, one-to-many relationships:

- `dim_customers[customer_id]` to `fact_subscriptions[customer_id]`
- `dim_customers[customer_id]` to `fact_usage[customer_id]`
- `dim_customers[customer_id]` to `fact_support[customer_id]`
- `dim_plans[plan_id]` to `fact_subscriptions[plan_id]`
- `fact_subscriptions[subscription_id]` to `fact_payments[subscription_id]`

Create a date table in DAX and relate its date to the fact date used by each visual:

```DAX
Calendar =
CALENDAR (
    MIN ( fact_usage[event_date] ),
    MAX ( fact_usage[event_date] )
)
```

Mark it as the model's date table. Create single-direction one-to-many date relationships to `fact_usage[event_date]`, `fact_payments[payment_date]`, `fact_support[ticket_date]`, and `dim_customers[signup_date]`. Add a month label for visuals:

```DAX
Year Month = FORMAT ( 'Calendar'[Date], "YYYY-MM" )
```

Sort `Year Month` by a numeric year-month sort column if Power BI sorts the label alphabetically.

## Starter Measures

```DAX
Total Users =
DISTINCTCOUNT ( dim_customers[customer_id] )

Active Users =
DISTINCTCOUNT ( fact_usage[customer_id] )

DAU =
DISTINCTCOUNT ( fact_usage[customer_id] )

Average DAU on Logged Days =
AVERAGEX (
    VALUES ( 'Calendar'[Date] ),
    CALCULATE ( DISTINCTCOUNT ( fact_usage[customer_id] ) )
)

MAU =
CALCULATE (
    DISTINCTCOUNT ( fact_usage[customer_id] ),
    DATESMTD ( 'Calendar'[Date] )
)

DAU MAU Ratio =
DIVIDE ( [Average DAU on Logged Days], [MAU] )

Paid Users =
VAR PaidSubscriptionIds =
    CALCULATETABLE (
        VALUES ( fact_payments[subscription_id] ),
        fact_payments[payment_status] = "paid"
    )
RETURN
    CALCULATE (
        DISTINCTCOUNT ( fact_subscriptions[customer_id] ),
        TREATAS ( PaidSubscriptionIds, fact_subscriptions[subscription_id] )
    )

Churned Subscriptions =
CALCULATE (
    DISTINCTCOUNT ( fact_subscriptions[subscription_id] ),
    fact_subscriptions[status] = "churned"
)

Observed Churn Rate =
DIVIDE (
    [Churned Subscriptions],
    DISTINCTCOUNT ( fact_subscriptions[subscription_id] )
)

Average Recorded Session Minutes =
AVERAGE ( fact_usage[session_minutes] )

Recorded Logins per Active User =
DIVIDE (
    SUM ( fact_usage[login_count] ),
    DISTINCTCOUNT ( fact_usage[customer_id] )
)
```

`DAU` is meaningful when the visual is filtered to one calendar day. `Average DAU on Logged Days` averages daily distinct users over dates with usage records; dates without a usage row are not represented in the source. `MAU` uses month-to-date in the current date context. These measures do not imply a trial or a product event missing from the source.

## Four Report Pages

### 1. Executive Overview

Use cards for total users, active users, paid users, observed churn rate, and average DAU/MAU. Add a monthly active-user and paid-amount trend. Label paid users as customers with at least one successful payment, not trial conversions.

### 2. User Engagement

Show daily active users, monthly active users, recorded logins per active user, average recorded session minutes, and customers by `feature_name`. Include date, plan, country, and segment slicers. Treat `Unknown` as its own visible feature/category value.

### 3. Subscription and Payment Analysis

Use plan-level subscription and observed-churn comparisons, payment outcomes over time, paid/refunded amounts, and engagement for customers with or without successful payments. Do not label this a trial-to-paid funnel: the dataset has no trial lifecycle fields.

For a forecasting-method demonstration, import `report/revenue_forecast/monthly_paid_revenue.csv` and `report/revenue_forecast/revenue_forecast.csv` with **Get data > Text/CSV**. Plot `positive_paid_amount` as historical amounts and compare `selected_forecast` with `log_linear_trend_scenario` for the forecast period. Label the forecast cutoff as March 2026 and disclose that the source is synthetic, 26 negative paid rows are excluded from the forecast fit, and the values are payment records rather than verified recognized sales. The April-June 2026 forecast is now historical; do not present it as a current forecast.

### 4. Churn and Retention

Show observed churn by plan/status, the SQL signup-cohort retention matrix, and the SQL at-risk review list. Add a support-ticket and inactivity view. Label risk flags as rule-based signals, not a prediction model.

## Interpretation Guardrails

- This is synthetic practice data. Dashboard findings are demonstrations, not real-company evidence.
- Associations between usage and churn do not prove that usage caused churn.
- Trial conversion, channel conversion, and actual marketing acquisition source are unavailable.
- Session minutes are reported as supplied; the source grain is a usage record, so do not assume every row is a separately captured session without validating that definition.
- Use the SQL outputs and `data/processed/cleaning_report.json` to cross-check dashboard totals.