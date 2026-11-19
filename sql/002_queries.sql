-- Research-style extracts without reproducing any medical dataset or workflow.

-- Verify ownership dimension, unique ticket identifiers, and category mix.
SELECT region, channel, category,
       COUNT(*) AS ticket_count,
       ROUND(AVG(resolution_minutes), 1) AS mean_resolution_minutes,
       ROUND(100.0 * AVG(sla_breached::int), 2) AS sla_breach_pct
FROM ops.clean_ticket_fact
GROUP BY region, channel, category
ORDER BY region, channel, ticket_count DESC;

-- Daily workload and staffing reconciled by region/day.
-- Invalid staffing shifts are surfaced rather than silently counted.
WITH demand AS (
  SELECT region, ticket_day, COUNT(*) AS tickets,
         SUM(sla_breached::int) AS sla_breaches
  FROM ops.clean_ticket_fact
  GROUP BY region, ticket_day
)
SELECT d.region, d.ticket_day, d.tickets, d.sla_breaches,
       s.scheduled_agent_hours,
       CASE WHEN s.scheduled_agent_hours > 0
            THEN ROUND(s.scheduled_agent_hours / d.tickets, 2)
            ELSE NULL END AS staffed_hours_per_ticket,
       CASE WHEN s.scheduled_agent_hours <= 0 THEN 'invalid_shift'
            WHEN s.shift_date IS NULL THEN 'missing_shift'
            ELSE 'matched' END AS reconciliation_status
FROM demand d
LEFT JOIN ops.workforce_shifts s
  ON d.region = s.region AND d.ticket_day = s.shift_date
ORDER BY d.region, d.ticket_day;

-- Cohort-style month-over-month output for stakeholder reporting.
SELECT date_trunc('month', ticket_day)::date AS reporting_month,
       region, COUNT(*) AS volume,
       ROUND(100.0 * AVG(sla_breached::int), 2) AS breach_pct,
       ROUND(percentile_cont(0.5) WITHIN GROUP
              (ORDER BY resolution_minutes)::numeric, 1) AS p50_resolution_minutes
FROM ops.clean_ticket_fact
GROUP BY 1, region
ORDER BY 1, region;

-- Defensive QA query against accidental duplicate or owner mismatches.
SELECT t.ticket_id, t.region AS ticket_region, a.home_region
FROM ops.clean_ticket_fact t
JOIN ops.agent_dimension a USING (agent_id)
WHERE t.region IS DISTINCT FROM a.home_region;
