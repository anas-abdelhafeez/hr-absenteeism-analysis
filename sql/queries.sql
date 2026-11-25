-- Portable SQL (runs unchanged on DuckDB and PostgreSQL). Table: absences (see load scripts in analysis.py).
-- Source: UCI "Absenteeism at work", CC BY 4.0. One row = one absence event. 'period' is NULL for 3 events with no month.

-- name: totals
SELECT COUNT(*) AS events, COUNT(DISTINCT emp_id) AS employees, SUM(hours) AS hours FROM absences;

-- name: employee_hours
SELECT emp_id, SUM(hours) AS hours, COUNT(*) AS events
FROM absences GROUP BY emp_id ORDER BY hours DESC, emp_id;

-- name: top5_share
WITH e AS (SELECT emp_id, SUM(hours) AS h FROM absences GROUP BY emp_id),
     r AS (SELECT h, ROW_NUMBER() OVER (ORDER BY h DESC, emp_id) AS rk FROM e)
SELECT ROUND(100.0 * SUM(CASE WHEN rk <= 5 THEN h ELSE 0 END) / SUM(h), 1) AS top5_pct FROM r;

-- name: period_hours
SELECT emp_id,
       SUM(CASE WHEN period = '2007-08' THEN hours ELSE 0 END) AS hours_early,
       SUM(CASE WHEN period = '2009-10' THEN hours ELSE 0 END) AS hours_late,
       SUM(CASE WHEN period = '2007-08' THEN 1 ELSE 0 END) AS events_early,
       SUM(CASE WHEN period = '2009-10' THEN 1 ELSE 0 END) AS events_late
FROM absences WHERE period IS NOT NULL GROUP BY emp_id ORDER BY emp_id;

-- name: early_top5_late_share
WITH p AS (SELECT emp_id,
                  SUM(CASE WHEN period = '2007-08' THEN hours ELSE 0 END) AS he,
                  SUM(CASE WHEN period = '2009-10' THEN hours ELSE 0 END) AS hl
           FROM absences WHERE period IS NOT NULL GROUP BY emp_id),
     r AS (SELECT hl, ROW_NUMBER() OVER (ORDER BY he DESC, emp_id) AS rk FROM p)
SELECT ROUND(100.0 * SUM(CASE WHEN rk <= 5 THEN hl ELSE 0 END) / SUM(hl), 1) AS late_share_pct FROM r;

-- name: weekday
SELECT weekday, MIN(weekday_no) AS ord, COUNT(*) AS events, SUM(hours) AS hours,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS events_pct,
       ROUND(100.0 * SUM(hours) / SUM(SUM(hours)) OVER (), 1) AS hours_pct,
       ROUND(AVG(hours), 1) AS avg_hours
FROM absences WHERE period IS NOT NULL GROUP BY weekday ORDER BY ord;

-- name: reasons
SELECT reason_name, reason_group, COUNT(*) AS events, SUM(hours) AS hours, ROUND(AVG(hours), 1) AS avg_hours
FROM absences GROUP BY reason_name, reason_group ORDER BY hours DESC, reason_name;

-- name: planned_vs_other
SELECT reason_group, COUNT(*) AS events, SUM(hours) AS hours FROM absences GROUP BY reason_group ORDER BY reason_group;
