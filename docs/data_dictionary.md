# Synthetic data dictionary — demo only

All identifiers, dates, ages and outcomes are fictional. These CSVs are not modeled on any particular real patient's record.

| Source | Field | Type | Meaning | Illustrative validation |
|---|---|---|---|
| registry.csv | `case_id` | string | Synthetic cross-source case key | Non-null, unique per source |
| registry.csv | `site_id` | string | Fictional site code `SITE01`...`SITE16` | In site list |
| registry.csv | `recipient_age` | integer | Synthetic age in years | Example-only range 18–100 |
| registry.csv | `transplant_date` | ISO date | Synthetic procedure date | Valid date |
| registry.csv | `graft_status` | string | Fictional status (`functioning`, `unknown`) | Code list |
| redcap.csv | `case_id` | string | Synthetic case key | Non-null, unique per source |
| redcap.csv | `site_id` | string | REDCap-style site label | Must agree with registry |
| redcap.csv | `anesthesia_start` | ISO datetime | Fictional start | Before end |
| redcap.csv | `anesthesia_end` | ISO datetime | Fictional end | Required and after start |
| redcap.csv | `asa_class` | string | Coded category in demo | I, II, III, IV, V |
| anesthesia.csv | `case_id` | string | Synthetic case key | Non-null, unique per source |
| anesthesia.csv | `site_id` | string | Anesthesia export site | Must agree with registry |
| anesthesia.csv | `ebl_ml` | integer | Fictional blood-loss example value | Illustrative range 0–15000 |
| anesthesia.csv | `anesthesia_minutes` | integer | Fictional duration | Illustrative range 1–1440 |

**Note:** clinical data dictionaries, appropriate mappings, and outlier criteria must be approved by a qualified PI; toy thresholds here are not medical advice.
