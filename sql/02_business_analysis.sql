USE saas_analytics;



-- 1. DAU, MAU, and average DAU/MAU for dates with recorded activity.
WITH daily_active AS (
  SELECT event_date, COUNT(DISTINCT customer_id) AS dau
  FROM fact_usage
  GROUP BY event_date
),
monthly_active AS (
  SELECT DATE_FORMAT(event_date, '%Y-%m-01') AS month_start,
         COUNT(DISTINCT customer_id) AS mau
  FROM fact_usage
  GROUP BY DATE_FORMAT(event_date, '%Y-%m-01')
)
SELECT m.month_start,
       ROUND(AVG(d.dau), 2) AS average_dau_on_logged_days,
       m.mau,
       ROUND(AVG(d.dau) / NULLIF(m.mau, 0), 4) AS average_dau_mau_ratio
FROM monthly_active AS m
JOIN daily_active AS d
  ON d.event_date >= m.month_start
 AND d.event_date < DATE_ADD(m.month_start, INTERVAL 1 MONTH)
GROUP BY m.month_start, m.mau
ORDER BY m.month_start;

-- 2. Feature usage versus churn status. This is association, not causation.
WITH customer_outcomes AS (
  SELECT customer_id, MAX(status = 'churned') AS has_churned
  FROM fact_subscriptions
  GROUP BY customer_id
),
feature_customer_usage AS (
  SELECT feature_name,
         customer_id,
         SUM(login_count) AS recorded_logins,
         AVG(session_minutes) AS average_recorded_session_minutes
  FROM fact_usage
  GROUP BY feature_name, customer_id
)
SELECT f.feature_name,
       COUNT(*) AS customers_using_feature,
       SUM(f.recorded_logins) AS recorded_logins,
       ROUND(AVG(f.average_recorded_session_minutes), 2) AS average_recorded_session_minutes,
       ROUND(100 * AVG(o.has_churned), 2) AS associated_churn_rate_pct
FROM feature_customer_usage AS f
JOIN customer_outcomes AS o ON o.customer_id = f.customer_id
GROUP BY f.feature_name
ORDER BY customers_using_feature DESC;

-- 3. Observed churn status by plan.
SELECT p.plan_name,
       p.billing_cycle,
       COUNT(DISTINCT s.subscription_id) AS subscriptions,
       COUNT(DISTINCT CASE WHEN s.status = 'active' THEN s.subscription_id END) AS active_subscriptions,
       COUNT(DISTINCT CASE WHEN s.status = 'churned' THEN s.subscription_id END) AS churned_subscriptions,
       ROUND(100 * COUNT(DISTINCT CASE WHEN s.status = 'churned' THEN s.subscription_id END)
             / NULLIF(COUNT(DISTINCT s.subscription_id), 0), 2) AS observed_churn_rate_pct
FROM fact_subscriptions AS s
JOIN dim_plans AS p ON p.plan_id = s.plan_id
GROUP BY p.plan_name, p.billing_cycle
ORDER BY observed_churn_rate_pct DESC;

-- 4. Payment outcomes by month and plan.
SELECT DATE_FORMAT(py.payment_date, '%Y-%m') AS payment_month,
       pl.plan_name,
       COUNT(*) AS payment_records,
       SUM(CASE WHEN py.payment_status = 'paid' THEN py.amount ELSE 0 END) AS paid_amount,
       SUM(CASE WHEN py.payment_status = 'refunded' THEN py.amount ELSE 0 END) AS refunded_amount,
       SUM(py.payment_status = 'failed') AS failed_payment_records
FROM fact_payments AS py
JOIN fact_subscriptions AS s ON s.subscription_id = py.subscription_id
JOIN dim_plans AS pl ON pl.plan_id = s.plan_id
GROUP BY DATE_FORMAT(py.payment_date, '%Y-%m'), pl.plan_name
ORDER BY payment_month, pl.plan_name;

-- 5. Signup-cohort retention by month with at least one usage record.
WITH customer_cohorts AS (
  SELECT customer_id, DATE_FORMAT(signup_date, '%Y-%m-01') AS cohort_month
  FROM dim_customers
),
cohort_sizes AS (
  SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_users
  FROM customer_cohorts
  GROUP BY cohort_month
),
monthly_activity AS (
  SELECT DISTINCT customer_id, DATE_FORMAT(event_date, '%Y-%m-01') AS activity_month
  FROM fact_usage
),
cohort_retention AS (
  SELECT c.cohort_month,
         TIMESTAMPDIFF(MONTH, c.cohort_month, a.activity_month) AS months_since_signup,
         COUNT(DISTINCT a.customer_id) AS retained_users
  FROM customer_cohorts AS c
  JOIN monthly_activity AS a
    ON a.customer_id = c.customer_id AND a.activity_month >= c.cohort_month
  GROUP BY c.cohort_month, TIMESTAMPDIFF(MONTH, c.cohort_month, a.activity_month)
)
SELECT r.cohort_month,
       r.months_since_signup,
       s.cohort_users,
       r.retained_users,
       ROUND(100 * r.retained_users / NULLIF(s.cohort_users, 0), 2) AS retention_pct
FROM cohort_retention AS r
JOIN cohort_sizes AS s ON s.cohort_month = r.cohort_month
ORDER BY r.cohort_month, r.months_since_signup;

-- 6. Engagement comparison by observed successful-payment segment.
WITH paid_customers AS (
  SELECT DISTINCT s.customer_id
  FROM fact_subscriptions AS s
  JOIN fact_payments AS p ON p.subscription_id = s.subscription_id
  WHERE p.payment_status = 'paid'
),
customer_engagement AS (
  SELECT customer_id,
         SUM(login_count) AS total_logins,
         AVG(session_minutes) AS average_session_minutes,
         COUNT(DISTINCT event_date) AS active_days
  FROM fact_usage
  GROUP BY customer_id
)
SELECT CASE WHEN p.customer_id IS NULL THEN 'No successful payment'
            ELSE 'Has successful payment' END AS payment_segment,
       COUNT(*) AS customers,
       ROUND(AVG(e.total_logins), 2) AS average_recorded_logins,
       ROUND(AVG(e.average_session_minutes), 2) AS average_recorded_session_minutes,
       ROUND(AVG(e.active_days), 2) AS average_active_days
FROM customer_engagement AS e
LEFT JOIN paid_customers AS p ON p.customer_id = e.customer_id
GROUP BY payment_segment
ORDER BY customers DESC;

-- 7. Transparent at-risk review list, not a trained prediction model.
WITH reference_date AS (
  SELECT MAX(event_date) AS as_of_date FROM fact_usage
),
last_activity AS (
  SELECT customer_id, MAX(event_date) AS last_event_date
  FROM fact_usage
  GROUP BY customer_id
),
failed_payments AS (
  SELECT s.customer_id, COUNT(*) AS failed_payments_90d
  FROM fact_subscriptions AS s
  JOIN fact_payments AS p ON p.subscription_id = s.subscription_id
  WHERE p.payment_status = 'failed'
    AND p.payment_date >= DATE_SUB((SELECT as_of_date FROM reference_date), INTERVAL 90 DAY)
  GROUP BY s.customer_id
),
recent_support AS (
  SELECT customer_id, COUNT(*) AS support_tickets_30d
  FROM fact_support
  WHERE ticket_date >= DATE_SUB((SELECT as_of_date FROM reference_date), INTERVAL 30 DAY)
  GROUP BY customer_id
),
active_customers AS (
  SELECT DISTINCT customer_id FROM fact_subscriptions WHERE status = 'active'
),
risk_inputs AS (
  SELECT a.customer_id,
         r.as_of_date,
         la.last_event_date,
         DATEDIFF(r.as_of_date, la.last_event_date) AS inactive_days,
         COALESCE(fp.failed_payments_90d, 0) AS failed_payments_90d,
         COALESCE(rs.support_tickets_30d, 0) AS support_tickets_30d,
         (CASE WHEN la.last_event_date IS NULL OR DATEDIFF(r.as_of_date, la.last_event_date) >= 30 THEN 2 ELSE 0 END)
         + (CASE WHEN COALESCE(fp.failed_payments_90d, 0) > 0 THEN 1 ELSE 0 END)
         + (CASE WHEN COALESCE(rs.support_tickets_30d, 0) >= 2 THEN 1 ELSE 0 END) AS risk_score
  FROM active_customers AS a
  CROSS JOIN reference_date AS r
  LEFT JOIN last_activity AS la ON la.customer_id = a.customer_id
  LEFT JOIN failed_payments AS fp ON fp.customer_id = a.customer_id
  LEFT JOIN recent_support AS rs ON rs.customer_id = a.customer_id
)
SELECT customer_id, as_of_date, last_event_date, inactive_days,
       failed_payments_90d, support_tickets_30d, risk_score,
       CASE WHEN risk_score >= 2 THEN 'High' ELSE 'Monitor' END AS risk_segment
FROM risk_inputs
WHERE risk_score >= 2
ORDER BY risk_score DESC, inactive_days DESC;

-- 8. Rank by observed successful payments, not forecast lifetime value.
WITH customer_revenue AS (
  SELECT s.customer_id,
         SUM(CASE WHEN p.payment_status = 'paid' THEN p.amount ELSE 0 END) AS lifetime_paid_amount,
         COUNT(DISTINCT CASE WHEN p.payment_status = 'paid' THEN p.payment_id END) AS successful_payment_count
  FROM fact_subscriptions AS s
  LEFT JOIN fact_payments AS p ON p.subscription_id = s.subscription_id
  GROUP BY s.customer_id
),
ranked_customers AS (
  SELECT c.customer_id,
         c.segment,
         COALESCE(r.lifetime_paid_amount, 0) AS lifetime_paid_amount,
         COALESCE(r.successful_payment_count, 0) AS successful_payment_count,
         RANK() OVER (ORDER BY COALESCE(r.lifetime_paid_amount, 0) DESC) AS revenue_rank
  FROM dim_customers AS c
  LEFT JOIN customer_revenue AS r ON r.customer_id = c.customer_id
)
SELECT customer_id, segment, lifetime_paid_amount, successful_payment_count, revenue_rank
FROM ranked_customers
ORDER BY revenue_rank, customer_id;
