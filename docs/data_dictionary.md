# Data Dictionary

## Source and Grain

The source is the Kaggle [SaaS Customer Churn Dataset](https://www.kaggle.com/datasets/mounikabusi/saas-customer-churn-dataset). Its author explicitly describes it as synthetic and educational. It contains six CSV tables. The downloaded archive is about 327 KB; the extracted files are about 1.67 MB total.

| Table | Row meaning | Primary key | Foreign keys |
|---|---|---|---|
| `dim_customers` | One customer profile | `customer_id` | None |
| `dim_plans` | One subscription plan | `plan_id` | None |
| `fact_subscriptions` | One subscription record | `subscription_id` | `customer_id`, `plan_id` |
| `fact_payments` | One payment record | `payment_id` | `subscription_id` |
| `fact_support` | One support ticket | `ticket_id` | `customer_id` |
| `fact_usage` | One dated usage record | `usage_id` | `customer_id` |

## Columns

### `dim_customers`

| Column | Type | Meaning |
|---|---|---|
| `customer_id` | Categorical ID | Unique customer identifier. |
| `signup_date` | Date | Date the customer signed up. |
| `country` | Categorical | Customer country; missing values are stored as `Unknown` after cleaning. |
| `industry` | Categorical | Customer industry; missing values are stored as `Unknown` after cleaning. |
| `company_size` | Categorical | Customer company-size segment. |
| `segment` | Categorical | Customer segment supplied by the dataset. |

There is no acquisition-channel column.

### `dim_plans`

| Column | Type | Meaning |
|---|---|---|
| `plan_id` | Categorical ID | Unique plan identifier. |
| `plan_name` | Categorical | Display name of the plan. |
| `monthly_price` | Decimal | Plan price supplied in the dataset. |
| `billing_cycle` | Categorical | Billing interval, such as monthly or annual. |

### `fact_subscriptions`

| Column | Type | Meaning |
|---|---|---|
| `subscription_id` | Categorical ID | Unique subscription identifier. |
| `customer_id` | Categorical ID | Customer who owns the subscription; links to `dim_customers`. |
| `plan_id` | Categorical ID | Selected plan; links to `dim_plans`. |
| `start_date` | Date | Subscription start date. |
| `end_date` | Date, nullable | Subscription end date; blank for ongoing subscriptions in this dataset. |
| `status` | Categorical | Subscription status. Variants are standardized to `active`, `canceled`, or `churned`. |

There is no explicit trial flag, trial-end date, or conversion date. Trial-to-paid conversion cannot be calculated from this table.

### `fact_payments`

| Column | Type | Meaning |
|---|---|---|
| `payment_id` | Categorical ID | Unique payment identifier. |
| `subscription_id` | Categorical ID | Subscription associated with the payment. |
| `payment_date` | Date | Date the payment was recorded. |
| `amount` | Decimal | Payment amount. |
| `payment_status` | Categorical | Payment outcome, such as paid, failed, or refunded. |
| `payment_method` | Categorical | Payment method recorded for the transaction. |

### `fact_support`

| Column | Type | Meaning |
|---|---|---|
| `ticket_id` | Categorical ID | Unique support-ticket identifier. |
| `customer_id` | Categorical ID | Customer who created the ticket. |
| `ticket_date` | Date | Date the support ticket was created. |
| `priority` | Categorical | Ticket priority. |
| `category` | Categorical | Ticket topic or category. |
| `resolution_time` | Numeric | Recorded time to resolve the ticket; confirm the unit before interpreting it. |
| `status` | Categorical | Support-ticket status, not subscription status. |

### `fact_usage`

| Column | Type | Meaning |
|---|---|---|
| `usage_id` | Categorical ID | Unique usage-record identifier. |
| `customer_id` | Categorical ID | Customer who generated the usage record. |
| `event_date` | Date | Date of the recorded usage. |
| `feature_name` | Categorical | Feature associated with the record; missing values are represented as `Unknown` after cleaning. |
| `login_count` | Integer | Login count recorded for the usage record. |
| `session_minutes` | Numeric | Session duration in minutes as supplied by the dataset. |

## Observed Data Quality and Scope

- Raw row counts: 1,550 customer rows, 3 plans, 1,500 subscriptions, 3,063 payments, 784 support tickets, and 24,756 usage records.
- Fifty exact duplicate customer rows were removed, leaving 1,500 customers.
- `P_PRO` and `p_pro` were case variants of the same plan ID; IDs are normalized to lowercase before relationship checks.
- 337 missing country values and 231 missing industry values are retained as `Unknown` categories.
- 942 blank feature names are labeled `Unknown`; usage rows are preserved because they still contain activity measures.
- 810 negative `login_count` values are invalid because a login count cannot be negative and the MySQL column is `INT UNSIGNED`. The raw source is unchanged; the cleaned copy records these counts as `0`, and a recovery CSV contains those 810 corrected rows.
- 1,043 blank subscription end dates align with active subscriptions and are kept null to represent ongoing subscriptions.
- All checked foreign-key relationships matched after ID normalization.
- DAU/MAU can be derived from distinct customers in `fact_usage` by `event_date`; this is activity-based, not a direct login-session log.
- Feature usage, login counts, session minutes, plan mix, payment outcomes, support patterns, churn status, and signup cohorts can be explored.
- Trial conversion and acquisition-channel performance are not supported by the source and must be shown as unavailable, not estimated or invented.