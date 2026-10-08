# Dataset Research

## Decision

The user approved synthetic data for this portfolio project. The selected dataset is the Kaggle SaaS Customer Churn Dataset: its dataset card explicitly identifies it as synthetic, it contains six related CSV tables, and its extracted size is about 1.67 MB. The archive has been downloaded and extracted under `data/raw`; no additional synthetic records have been generated.

The fit percentages below are rough estimates of coverage for the requested analyses, not source-quality scores.

| Dataset | Published size | Important columns and possible analysis | Gaps | Fit / decision |
|---|---:|---|---|---:|
| [SaaS Customer Churn Dataset](https://www.kaggle.com/datasets/mounikabusi/saas-customer-churn-dataset) | 6 CSV files; 1.67 MB extracted; 31,656 raw rows across tables | Customer, plan, subscription, payment, support, and usage facts. Supports activity, plans, payment outcomes, support, cohorts, and churn analysis. | Synthetic. No explicit trial, conversion timestamp, or acquisition channel. | 75%; **selected** |
| [KKBox Churn Prediction Challenge](https://www.kaggle.com/competitions/kkbox-churn-prediction-challenge/data) | 8.95 GB across 10 files; `transactions.csv` is commonly reported at about 21.5 million rows | `msno`, transaction and membership-expiry dates, plan days/price, auto-renewal, daily user-log date, song completion counts, unique songs, and total listening seconds. Supports subscription renewal/churn and engagement associations. | Music streaming rather than SaaS; no free-trial lifecycle, marketing acquisition channel, or SaaS feature events. Daily listening totals are not login/session records. Exceeds the agreed data budget. | 68%; **exclude** |
| [E-Commerce Customer Churn](https://www.kaggle.com/datasets/ankitverma2010/ecommerce-customer-churn-analysis-and-prediction) | 5,630 customers; about 556 KB | `CustomerID`, `Churn`, `Tenure`, `HourSpendOnApp`, `PreferredLoginDevice`, `OrderCount`, `DaySinceLastOrder`, and customer/profile fields. Supports one-time engagement-versus-churn comparisons. | No dated event history, SaaS subscription/trial lifecycle, feature events, DAU/MAU, or cohorts. The uploader describes company data, but its provenance is not independently clear. | 43%; **not sufficient** |
| [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) | 1,067,371 transaction rows; 43.5 MB file | `InvoiceNo`, `StockCode`, `Quantity`, `InvoiceDate`, `UnitPrice`, `CustomerID`, and `Country`. Supports repeat purchase, transaction cohorts, and inactivity-based retention proxies. | Retail rather than SaaS; no app activity, sessions, plans, trial conversion, or explicit churn outcome. | 22%; **not sufficient** |
| [SaaS Product Dashboard dataset](https://www.kaggle.com/datasets/philbertchan/saas-product-dashboard-mau-feature-usage-mrr) | 3 CSV files; 38.05 KB total | Small `users`, `events`, and `subscriptions` dataset; the linked project reports user, event, plan, and MRR analysis. | The linked [GitHub project](https://github.com/rahmasayed18/saas-product-analytics) describes its product as simulated. The Kaggle card does not document real-world provenance, so it is not verified real data and is excluded. | **Excluded: simulated / provenance unverified** |
| [Customer Subscription Churn and Usage Patterns](https://www.kaggle.com/datasets/jayjoshi37/customer-subscription-churn-and-usage-patterns) | 2,800 records; 10 columns; 126.31 KB | Subscription, usage, support, payment, and churn indicators for simple customer-level comparisons. | The dataset card explicitly says it is synthetic; it is not a dated product-event history. | **Excluded: synthetic** |

## Can These Sources Be Combined?

No. These datasets describe different products and do not share customer identifiers or a common event model. Joining them would not create a valid SaaS user journey and would lead to misleading conversion or retention results.

## Next Step

Use only metrics supported by the selected source. Trial conversion and acquisition-channel performance are unavailable; do not infer or invent them. See `docs/data_dictionary.md` for observed table grain, schema, and cleaning findings.