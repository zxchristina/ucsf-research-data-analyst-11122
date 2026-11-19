-- SYNTHETIC ONLY. Example audit and research cohort queries for PostgreSQL.

-- 1. Identify registry cases missing a linked anesthesia record.
SELECT r.site_id, r.case_id
FROM demo_research.registry r
LEFT JOIN demo_research.anesthesia a USING (case_id)
WHERE a.case_id IS NULL
ORDER BY r.site_id, r.case_id;

-- 2. Identify site label mismatches across submissions.
SELECT r.case_id, r.site_id AS registry_site, p.site_id AS redcap_site,
       a.site_id AS anesthesia_site
FROM demo_research.registry r
JOIN demo_research.redcap p USING (case_id)
JOIN demo_research.anesthesia a USING (case_id)
WHERE r.site_id <> p.site_id OR r.site_id <> a.site_id;

-- 3. Illustrative quality-screened extraction and site-level aggregates.
-- Thresholds are NOT clinical definitions, and pre-validated staging is assumed.
WITH screened AS (
    SELECT r.case_id, r.site_id, r.recipient_age, r.graft_status,
           a.ebl_ml, a.anesthesia_minutes
    FROM demo_research.registry r
    JOIN demo_research.redcap p USING (case_id)
    JOIN demo_research.anesthesia a USING (case_id)
    WHERE r.site_id = p.site_id
      AND r.site_id = a.site_id
      AND r.recipient_age BETWEEN 18 AND 100
      AND p.asa_class IN ('I', 'II', 'III', 'IV', 'V')
      AND p.anesthesia_end > p.anesthesia_start
      AND a.ebl_ml BETWEEN 0 AND 15000
      AND a.anesthesia_minutes BETWEEN 1 AND 1440
)
SELECT site_id, COUNT(*) AS eligible_cases,
       ROUND(AVG(recipient_age), 1) AS mean_recipient_age,
       ROUND(AVG(ebl_ml), 1) AS mean_ebl_ml
FROM screened
GROUP BY site_id
ORDER BY site_id;
