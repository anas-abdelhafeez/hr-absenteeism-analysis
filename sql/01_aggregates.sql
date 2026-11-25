-- Aggregates for the absenteeism story. Run with DuckDB: duckdb < sql/01_aggregates.sql
-- Source: data/absenteeism_enriched.csv (UCI Absenteeism at work, CC BY 4.0)
CREATE OR REPLACE VIEW ev AS
SELECT *, "Absenteeism time in hours" AS hours,
       CASE WHEN reason_name IN ('Medical consultation','Dental consultation','Physiotherapy','Laboratory examination','Patient follow-up','Blood donation')
            THEN 'Planned care' ELSE 'Illness, injury, other' END AS reason_group
FROM read_csv_auto('data/absenteeism_enriched.csv');

-- Q1 totals
SELECT count(*) AS events, count(DISTINCT ID) AS employees, sum(hours) AS hours FROM ev;

-- Q2 employee rollup with cumulative share (Pareto)
CREATE OR REPLACE TABLE emp AS
SELECT ID, sum(hours) AS hours, count(*) AS events,
       round(avg(hours),1) AS hours_per_event,
       round(avg((reason_group='Planned care')::INT),3) AS planned_share,
       any_value(Age) AS age, any_value("Service time") AS service,
       any_value("Distance from Residence to Work") AS distance
FROM ev GROUP BY ID;
SELECT ID, hours, events, round(100*sum(hours) OVER (ORDER BY hours DESC, ID)/sum(hours) OVER (),1) AS cum_share_pct
FROM emp ORDER BY hours DESC;

-- Q3 reasons
SELECT reason_name, reason_group, count(*) AS events, sum(hours) AS hours, round(avg(hours),1) AS avg_hours
FROM ev GROUP BY 1,2 ORDER BY hours DESC;

-- Q4 weekday and season
SELECT dow_name, count(*) AS events, sum(hours) AS hours FROM ev GROUP BY 1 ORDER BY min("Day of the week");
SELECT season_name, count(*) AS events, sum(hours) AS hours FROM ev GROUP BY 1 ORDER BY min(Seasons);

-- Q5 what-if scenarios (hours recovered)
SELECT 'Top 5 employees cut hours by 50%' AS scenario,
       sum(hours)*0.5 AS hours_recovered
FROM (SELECT hours FROM emp ORDER BY hours DESC LIMIT 5)
UNION ALL
SELECT 'Illness events of 24h+ shortened by 25%', sum(hours)*0.25 FROM ev WHERE reason_group<>'Planned care' AND hours>=24
UNION ALL
SELECT 'Planned-care events moved outside work hours (30% of them)', sum(hours)*0.30 FROM ev WHERE reason_group='Planned care';
