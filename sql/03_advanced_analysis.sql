USE saas_analytics;

-- 1. Signup trend and observed churn status by signup cohort and customer segment.
WITH customer_outcomes AS (
  SELECT customer_id,
         MAX(CASE WHEN status = 'churned' THEN 1 ELSE 0 END) AS has_churned
  FROM fact_subscriptions
  GROUP BY customer_id
)
SELECT DATE_FORMAT(c.signup_date, '%Y-%m') AS signup_month,
       c.segment,
       COUNT(DISTINCT c.customer_id) AS new_customers,
       SUM(COALESCE(o.has_churned, 0)) AS customers_with_churn_status,
       ROUND(100 * AVG(COALESCE(o.has_churned, 0)), 2) AS observed_churn_share_pct
FROM dim_customers AS c
LEFT JOIN customer_outcomes AS o ON o.customer_id = c.customer_id
GROUP BY DATE_FORMAT(c.signup_date, '%Y-%m'), c.segment
ORDER BY signup_month, c.segment;

-- 2. Feature adoption among all registered users; Unknown remains visible.
WITH total_users AS (
  SELECT COUNT(DISTINCT customer_id) AS users
  FROM dim_customers
)
SELECT u.feature_name,
       COUNT(DISTINCT u.customer_id) AS feature_users,
       t.users AS total_users,
       ROUND(100 * COUNT(DISTINCT u.customer_id) / NULLIF(t.users, 0), 2) AS adoption_pct,
       SUM(u.login_count) AS recorded_logins,
       ROUND(AVG(u.session_minutes), 2) AS average_recorded_session_minutes
FROM fact_usage AS u
CROSS JOIN total_users AS t
GROUP BY u.feature_name, t.users
ORDER BY adoption_pct DESC;

-- 3. Churn association across customer-level engagement quartiles.
WITH customer_outcomes AS (
  SELECT customer_id,
         MAX(CASE WHEN status = 'churned' THEN 1 ELSE 0 END) AS has_churned
  FROM fact_subscriptions
  GROUP BY customer_id
),
customer_engagement AS (
  SELECT customer_id,
         SUM(login_count) AS total_recorded_logins,
         COUNT(DISTINCT event_date) AS active_days,
         AVG(session_minutes) AS average_session_minutes
  FROM fact_usage
  GROUP BY customer_id
),
ranked_engagement AS (
  SELECT e.customer_id,
         e.total_recorded_logins,
         e.active_days,
         e.average_session_minutes,
         COALESCE(o.has_churned, 0) AS has_churned,
         NTILE(4) OVER (ORDER BY e.active_days DESC, e.total_recorded_logins DESC) AS engagement_quartile
  FROM customer_engagement AS e
  LEFT JOIN customer_outcomes AS o ON o.customer_id = e.customer_id
)
SELECT engagement_quartile,
       COUNT(*) AS customers_with_usage,
       ROUND(AVG(total_recorded_logins), 2) AS average_recorded_logins,
       ROUND(AVG(active_days), 2) AS average_active_days,
       ROUND(100 * AVG(has_churned), 2) AS associated_churn_rate_pct
FROM ranked_engagement
GROUP BY engagement_quartile
ORDER BY engagement_quartile;

-- 4. Compare customer-level support load by observed churn status.
WITH customer_outcomes AS (
  SELECT customer_id,
         MAX(CASE WHEN status = 'churned' THEN 1 ELSE 0 END) AS has_churned
  FROM fact_subscriptions
  GROUP BY customer_id
),
customer_support AS (
  SELECT customer_id,
         COUNT(*) AS ticket_count,
         AVG(resolution_time) AS average_resolution_time,
         SUM(priority = 'High') AS high_priority_tickets
  FROM fact_support
  GROUP BY customer_id
)
SELECT CASE WHEN o.has_churned = 1 THEN 'Churned status' ELSE 'No churned status' END AS customer_outcome,
       COUNT(*) AS customers,
       ROUND(AVG(COALESCE(s.ticket_count, 0)), 2) AS average_tickets_per_customer,
       ROUND(AVG(s.average_resolution_time), 2) AS average_ticket_resolution_time,
       ROUND(AVG(COALESCE(s.high_priority_tickets, 0)), 2) AS average_high_priority_tickets
FROM customer_outcomes AS o
LEFT JOIN customer_support AS s ON s.customer_id = o.customer_id
GROUP BY customer_outcome;

-- 5. Payment success, failure, and refund shares by plan.
SELECT pl.plan_name,
       COUNT(*) AS payment_records,
       SUM(py.payment_status = 'paid') AS paid_records,
       SUM(py.payment_status = 'failed') AS failed_records,
       SUM(py.payment_status = 'refunded') AS refunded_records,
       ROUND(100 * SUM(py.payment_status = 'paid') / NULLIF(COUNT(*), 0), 2) AS paid_share_pct,
       ROUND(100 * SUM(py.payment_status = 'failed') / NULLIF(COUNT(*), 0), 2) AS failed_share_pct,
       ROUND(100 * SUM(py.payment_status = 'refunded') / NULLIF(COUNT(*), 0), 2) AS refunded_share_pct
FROM fact_payments AS py
JOIN fact_subscriptions AS s ON s.subscription_id = py.subscription_id
JOIN dim_plans AS pl ON pl.plan_id = s.plan_id
GROUP BY pl.plan_name
ORDER BY paid_share_pct DESC;

-- 6. Monthly active-user trend and month-over-month change.
WITH monthly_active AS (
  SELECT DATE_FORMAT(event_date, '%Y-%m-01') AS activity_month,
         COUNT(DISTINCT customer_id) AS mau
  FROM fact_usage
  GROUP BY DATE_FORMAT(event_date, '%Y-%m-01')
),
with_previous_month AS (
  SELECT activity_month,
         mau,
         LAG(mau) OVER (ORDER BY activity_month) AS previous_month_mau
  FROM monthly_active
)
SELECT activity_month,
       mau,
       previous_month_mau,
       mau - previous_month_mau AS mau_change,
       ROUND(100 * (mau - previous_month_mau) / NULLIF(previous_month_mau, 0), 2) AS mau_change_pct
FROM with_previous_month
ORDER BY activity_month;

-- 7. Usage during the 30 days before ended canceled/churned subscriptions.
WITH subscription_pre_end_usage AS (
  SELECT s.subscription_id,
         s.status,
         COALESCE(SUM(u.login_count), 0) AS logins_in_final_30_days,
         COUNT(DISTINCT u.event_date) AS active_days_in_final_30_days,
         AVG(u.session_minutes) AS average_session_minutes_in_final_30_days
  FROM fact_subscriptions AS s
  LEFT JOIN fact_usage AS u
    ON u.customer_id = s.customer_id
    AND u.event_date >= DATE_SUB(s.end_date, INTERVAL 30 DAY)
    AND u.event_date < s.end_date
  WHERE s.status IN ('canceled', 'churned')
    AND s.end_date IS NOT NULL
  GROUP BY s.subscription_id, s.status
)
SELECT status,
       COUNT(*) AS ended_subscriptions,
       ROUND(AVG(logins_in_final_30_days), 2) AS average_logins_in_final_30_days,
       ROUND(AVG(active_days_in_final_30_days), 2) AS average_active_days_in_final_30_days,
       ROUND(AVG(average_session_minutes_in_final_30_days), 2) AS average_session_minutes
FROM subscription_pre_end_usage
GROUP BY status;

-- 8. Recorded subscription duration by plan for ended subscriptions.
SELECT pl.plan_name,
       s.status,
       COUNT(*) AS ended_subscriptions,
       ROUND(AVG(DATEDIFF(s.end_date, s.start_date)), 1) AS average_subscription_days,
       MIN(DATEDIFF(s.end_date, s.start_date)) AS shortest_subscription_days,
       MAX(DATEDIFF(s.end_date, s.start_date)) AS longest_subscription_days
FROM fact_subscriptions AS s
JOIN dim_plans AS pl ON pl.plan_id = s.plan_id
WHERE s.status IN ('canceled', 'churned')
  AND s.end_date IS NOT NULL
GROUP BY pl.plan_name, s.status
ORDER BY pl.plan_name, s.status;