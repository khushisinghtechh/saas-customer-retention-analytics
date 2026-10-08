CREATE DATABASE IF NOT EXISTS saas_analytics
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE saas_analytics;

CREATE TABLE IF NOT EXISTS dim_customers (
  customer_id VARCHAR(50) NOT NULL,
  signup_date DATE NOT NULL,
  country VARCHAR(100) NOT NULL DEFAULT 'Unknown',
  industry VARCHAR(150) NOT NULL DEFAULT 'Unknown',
  company_size VARCHAR(50),
  segment VARCHAR(50),
  PRIMARY KEY (customer_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dim_plans (
  plan_id VARCHAR(50) NOT NULL,
  plan_name VARCHAR(100) NOT NULL,
  monthly_price DECIMAL(10, 2) NOT NULL,
  billing_cycle VARCHAR(30) NOT NULL,
  PRIMARY KEY (plan_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fact_subscriptions (
  subscription_id VARCHAR(50) NOT NULL,
  customer_id VARCHAR(50) NOT NULL,
  plan_id VARCHAR(50) NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NULL,
  status VARCHAR(30) NOT NULL,
  PRIMARY KEY (subscription_id),
  KEY idx_subscriptions_customer_status (customer_id, status),
  KEY idx_subscriptions_plan (plan_id),
  KEY idx_subscriptions_end_date (end_date),
  CONSTRAINT fk_subscriptions_customer
    FOREIGN KEY (customer_id) REFERENCES dim_customers (customer_id),
  CONSTRAINT fk_subscriptions_plan
    FOREIGN KEY (plan_id) REFERENCES dim_plans (plan_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fact_payments (
  payment_id VARCHAR(50) NOT NULL,
  subscription_id VARCHAR(50) NOT NULL,
  payment_date DATE NOT NULL,
  amount DECIMAL(10, 2) NOT NULL,
  payment_status VARCHAR(30) NOT NULL,
  payment_method VARCHAR(80) NOT NULL,
  PRIMARY KEY (payment_id),
  KEY idx_payments_subscription_date (subscription_id, payment_date),
  KEY idx_payments_status_date (payment_status, payment_date),
  CONSTRAINT fk_payments_subscription
    FOREIGN KEY (subscription_id) REFERENCES fact_subscriptions (subscription_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fact_support (
  ticket_id VARCHAR(50) NOT NULL,
  customer_id VARCHAR(50) NOT NULL,
  ticket_date DATE NOT NULL,
  priority VARCHAR(30) NOT NULL,
  category VARCHAR(100) NOT NULL,
  resolution_time DECIMAL(10, 2),
  status VARCHAR(30) NOT NULL,
  PRIMARY KEY (ticket_id),
  KEY idx_support_customer_date (customer_id, ticket_date),
  CONSTRAINT fk_support_customer
    FOREIGN KEY (customer_id) REFERENCES dim_customers (customer_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fact_usage (
  usage_id VARCHAR(50) NOT NULL,
  customer_id VARCHAR(50) NOT NULL,
  event_date DATE NOT NULL,
  feature_name VARCHAR(100) NOT NULL DEFAULT 'Unknown',
  login_count INT UNSIGNED,
  session_minutes DECIMAL(10, 2),
  PRIMARY KEY (usage_id),
  KEY idx_usage_event_customer (event_date, customer_id),
  KEY idx_usage_customer_event (customer_id, event_date),
  KEY idx_usage_feature_date (feature_name, event_date),
  CONSTRAINT fk_usage_customer
    FOREIGN KEY (customer_id) REFERENCES dim_customers (customer_id)
) ENGINE=InnoDB;

SELECT COUNT(*) FROM saas_analytics.dim_customers;