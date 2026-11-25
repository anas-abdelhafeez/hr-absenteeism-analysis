# Workforce Absenteeism: Drivers, Segments and What-If

A story-driven analysis of real absence records: **what is lost, where it comes from, who it comes from, why some absences run long, and what to do.** Built with SQL (DuckDB), statsmodels, scikit-learn, an HTML dashboard and a Power BI file.

Story flow: Problem -> Impact -> Where -> Who -> Why -> When -> Fix.

## Data
UCI, "Absenteeism at work" (archive.ics.uci.edu): 740 absence records, 36 employees, July 2007 to July 2010, from a Brazilian courier company. License: CC BY 4.0 (attribution required, kept here). `data/absenteeism_enriched.csv` is that file plus readable labels for coded columns (reason, weekday, season).
**This is real data but not a call center.** I use it as a stand-in for any shift-based service team and say so wherever it matters. There is no attrition data.

## Findings
- 36 employees lost **5,124 hours** in 740 events. The top 5 people account for **41%** of hours.
- Planned care (medical and dental visits, physiotherapy, labs, follow-ups, blood donation) is 26% of hours but most events, and they are short.
- Driver model (logistic regression, event is 8 h or more): planned care has an odds ratio of **0.074** (95% CI 0.039 to 0.139). Age, commute distance, tenure, workload, winter and Monday show no clear effect.
- Three employee groups (k-means): A, 10 people with about 45 short events each, mostly planned care, 47% of hours. B, 10 people with about 20 events of 13 h each, 46% of hours. C, 13 people with few events, 8% of hours.
- What-if (illustrations, not forecasts): halving the top 5 people's hours recovers about 1,050 hours; shortening 24 h+ illness events by 25% recovers 528; moving 30% of planned care outside work hours recovers 402. Cost uses an **assumed** $18 per hour.

## Honest limits
- 36 people. Models describe association, not cause. Standard errors are clustered by employee, and the intervals are still wide.
- Silhouette scores for 2, 3 and 4 clusters are 0.325, 0.330 and 0.332: weak structure. I chose 3 for readability.
- "Planned care" is partly built into the outcome (visits are short by nature), so that finding is expected. The useful result is what shows no effect.
- 44 events have 0 recorded hours (43 are coded "unspecified"); they are dropped from the driver model (696 events remain). 3 employees have only zero-hour records and are left out of the clustering.
- Scenario sizes (50%, 25%, 30%) and the $18 rate are my assumptions.

## Power BI file: not in this repo, not opened in Power BI Desktop
A Power BI file with the same story (Events table, 8 DAX measures, 5 report pages) was built separately and is not stored here. It was checked only by reading it back (740 rows, 5,124 hours). **It has not been opened in Power BI Desktop**, and the DAX results were not evaluated by Power BI. The HTML dashboard below shows the same story without Desktop.

## Dashboard
`docs/index.html` is a dark 7-tab dashboard (ECharts via CDN, works on a phone). Phone-width screenshots are not in this repo yet; open `docs/index.html` in a browser (it loads ECharts from a CDN).

## Run it
```
pip install -r requirements.txt
python analysis.py          # SQL + models -> results.json
python build_dashboard.py   # -> docs/index.html
pytest                      # 5 checks
```
SQL is in `sql/01_aggregates.sql` (run directly with DuckDB).

## License
Code: MIT (see LICENSE). Data: CC BY 4.0, UCI, "Absenteeism at work" (archive.ics.uci.edu).
