# Sample Findings and Business Recommendations

> **Important:** These figures come from a synthetically generated Kaggle learning dataset. They demonstrate an analysis workflow; they are not evidence about a real SaaS company.

## 1. Churn Status Is Similar Across Plans

**What happened?** There are 151 churned subscriptions among 1,500 subscriptions (10.07%). The observed churn-status share is 10.08% for Basic, 10.15% for Enterprise, and 10.01% for Pro.

**Why might this matter?** In this sample, plan category alone does not separate churned subscriptions meaningfully. The small differences may be random or built into the synthetic generator.

**Business decision:** Do not prioritize a retention campaign by plan based on these small differences. In a real product, test engagement, tenure, payment history, and support experience alongside plan before allocating retention effort.

## 2. About Half of Complete Signup Cohorts Use the Product in the Next Month

**What happened?** For January–October 2025 signup cohorts, weighted next-calendar-month usage retention is 54.7%. Individual cohort rates range from 51.3% to 58.3%. November's following month and December are excluded because the available activity ends on December 17, 2025.

**Why might this matter?** A usage record in the next calendar month is a simple activity-retention definition. It does not prove continuous subscription or explain why users return or drop off.

**Business decision:** In a real SaaS setting, review onboarding and early-life product education, then test an intervention against a properly defined retention outcome. Do not claim this sample establishes that onboarding caused the observed rate.

## 3. Named Features Do Not Show a Clear Churn Separation

**What happened?** Churn status among customers recorded against named features ranges from 9.19% to 9.38%: dashboard view 9.19%, team invite 9.29%, billing edit 9.29%, export CSV 9.31%, and API post 9.38%. Each customer contributes once per feature in this comparison. There are 942 usage records with an unknown feature label.

**Why might this matter?** The small spread does not support a strong feature-specific churn conclusion. Unknown feature labels weaken adoption analysis.

**Business decision:** Avoid removing or promoting a feature based on these results. Improve event-name instrumentation and investigate the source of unknown labels before using feature adoption to guide product investment.

## 4. Payment Records Need Outcome Review, Not a Conversion Claim

**What happened?** The table contains 1,542 paid, 761 refunded, and 760 failed payment records. A total of 1,009 customers have at least one successful payment (67.27% of customers).

**Why might this matter?** Failed and refunded records are numerous in this generated sample, but their reasons and the intended payment process are not described.

**Business decision:** In a real business, validate payment-state definitions and investigate failure/refund reasons before proposing retries or billing changes. The 67.27% figure is an ever-paid share in this sample, **not trial-to-paid conversion**.

## 5. Customers With a Successful Payment Have Slightly Higher Recorded Usage

**What happened?** Among the 1,000 customers with usage records, 674 had at least one successful payment and 326 did not. The paid group averaged 109.17 recorded logins and 24.15 active days, compared with 105.29 logins and 23.20 active days for the group without a successful payment. Average recorded session minutes were 62.19 versus 61.68.

**Why might this matter?** The differences are modest and describe only customers with usage records. Payment could be associated with engagement, but this comparison does not establish which came first or whether either caused the other.

**Business decision:** Treat this as a question to investigate, not a conversion claim. A real product team could define activation events and test onboarding changes while measuring a valid trial-to-paid outcome.

## 6. The Rule-Based Review List Flags 450 Active Customers

**What happened?** The SQL rule returned 450 customers with active subscriptions for review. It scores 30-or-more inactivity days or no usage history as two points, any failed payment in the last 90 days as one point, and at least two support tickets in the last 30 days as one point. Customers with a score of two or more are labeled High.

**Why might this matter?** The list makes signals visible to an analyst, but the thresholds were chosen for a transparent practice rule, not learned or validated against future churn.

**Business decision:** In a real business, review sample records and validate whether the rule captures customers who subsequently churn before using it to trigger outreach. Do not call this a predictive model.

## 7. The Highest Recorded Paid Amount Is Tied

**What happened?** The top four customers tie at a recorded successful-payment total of `$1,996` each, with four successful payment records apiece.

**Why might this matter?** `RANK()` correctly gives tied customers the same rank. The metric sums observed paid transactions; it does not forecast future revenue or customer lifetime value.

**Business decision:** Use this as observed-value segmentation practice only. A real high-value customer program would define a time window, account for refunds, and validate future value before prioritizing service.

## Metric Boundaries

- Trial-to-paid conversion cannot be calculated because there is no trial flag, trial date, or conversion event.
- Acquisition-channel performance cannot be calculated because there is no acquisition-source field.
- DAU and MAU use dated usage rows as activity. They are not verified login-session telemetry.
- Cohort activity retention is not the same as paid-subscription retention.
- These are observational comparisons and do not establish causal behavior.

## Interview Explanation

“I first audited the schema and source disclosure. The dataset was explicitly synthetic, so I label results as practice findings rather than real-company conclusions. I cleaned case-variant plan keys, retained missing feature labels as `Unknown`, validated the foreign keys, and did not report trial conversion because the required trial fields are absent. In a real company, I would request event-level trial and acquisition data before recommending a conversion program.”