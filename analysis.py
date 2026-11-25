"""Absenteeism analysis: SQL aggregates, driver model, segmentation, what-if. Run: python analysis.py"""
import json, duckdb, numpy as np, pandas as pd
import statsmodels.api as sm
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

RATE = 18.0  # ASSUMED cost per lost hour in USD, not from the data
PLANNED = ['Medical consultation','Dental consultation','Physiotherapy','Laboratory examination','Patient follow-up','Blood donation']
con = duckdb.connect()
sql = open('sql/01_aggregates.sql').read()
for st in sql.split(';'):
    st = '\n'.join(l for l in st.splitlines() if not l.strip().startswith('--')).strip()
    if st.upper().startswith('CREATE'): con.execute(st)
tot = con.execute("select count(*),count(distinct ID),sum(hours) from ev").fetchone()
emp = con.execute("select * from emp order by hours desc, ID").df()
emp['cum_share'] = (100*emp.hours.cumsum()/emp.hours.sum()).round(1)
reasons = con.execute("select reason_name,reason_group,count(*) AS events,sum(hours) AS hours,round(avg(hours),1) AS avg_h from ev group by 1,2 order by 4 desc").df()
dow = con.execute("select dow_name AS d,sum(hours) AS h from ev group by 1 order by min(\"Day of the week\")").df()
season = con.execute("select season_name AS s,sum(hours) AS h from ev group by 1 order by min(Seasons)").df()
R = {'events': int(tot[0]), 'employees': int(tot[1]), 'hours': int(tot[2]), 'rate': RATE}
R['top5_share'] = float(emp.cum_share.iloc[4]); R['top20_share'] = float(emp.cum_share.iloc[6])
planned_h = int(reasons[reasons.reason_group == 'Planned care'].hours.sum())
R['planned_hours'] = planned_h; R['planned_events'] = int(reasons[reasons.reason_group == 'Planned care'].events.sum())
# ---- driver model: P(event is long, >= 8h), cluster-robust SE by employee
ev = con.execute("select * from ev").df()
ev['long'] = (ev.hours >= 8).astype(int)
ev = ev[ev.hours > 0].copy()  # drop 0-hour records (no duration)
X = pd.DataFrame({
 'planned_care': (ev.reason_group == 'Planned care').astype(int),
 'monday': (ev['Day of the week'] == 2).astype(int),
 'winter': (ev.season_name == 'Winter').astype(int),
 'distance_10km': ev['Distance from Residence to Work']/10,
 'age_10y': ev['Age']/10,
 'service_10y': ev['Service time']/10,
 'workload_100': ev['Work load Average/day']/100})
mod = sm.Logit(ev['long'], sm.add_constant(X)).fit(disp=0, cov_type='cluster', cov_kwds={'groups': ev.ID})
d = pd.DataFrame({'odds_ratio': np.exp(mod.params), 'lo': np.exp(mod.conf_int()[0]), 'hi': np.exp(mod.conf_int()[1]), 'p': mod.pvalues}).drop('const').round(3)
R['drivers'] = d.reset_index().rename(columns={'index': 'factor'}).to_dict('records')
R['model_n'] = int(len(ev)); R['model_clusters'] = int(ev.ID.nunique())
# ---- segmentation of employees (employees with 0 recorded hours are reported separately, not clustered)
R['zero_hour_employees'] = int((emp.hours == 0).sum())
f = emp[emp.hours > 0].copy(); f['log_events'] = np.log1p(f.events); f['log_hpe'] = np.log1p(f.hours_per_event)
Z = StandardScaler().fit_transform(f[['log_events', 'log_hpe', 'planned_share']])
sil = {}
for k in (2, 3, 4):
    sil[k] = round(float(silhouette_score(Z, KMeans(k, n_init=20, random_state=7).fit_predict(Z))), 3)
R['silhouette'] = sil; K = 3  # silhouettes for k=2..4 are nearly equal (weak structure); k=3 chosen for a readable story
R['k'] = K
f['seg'] = KMeans(K, n_init=20, random_state=7).fit_predict(Z)
prof = f.groupby('seg').agg(employees=('ID', 'count'), hours=('hours', 'sum'), events=('events', 'sum'), hpe=('hours_per_event', 'mean'), planned=('planned_share', 'mean')).round(2)
prof['events_each'] = (prof.events/prof.employees).round(1)
order = prof.sort_values('events_each', ascending=False)
names = {i: f"Group {chr(65+n)}: ~{r.events_each:.0f} events each, {r.hpe:.1f} h per event, {100*r.planned:.0f}% planned care" for n, (i, r) in enumerate(order.iterrows())}
prof['name'] = prof.index.map(names); prof = prof.loc[order.index]
prof['share_hours_pct'] = (100*prof.hours/prof.hours.sum()).round(1)
R['segments'] = prof.reset_index().to_dict('records')
# ---- what-if (assumptions are scenario inputs, not forecasts)
top5 = emp.hours.head(5).sum()
ill24 = ev[(ev.reason_group != 'Planned care') & (ev.hours >= 24)].hours.sum()
sc = [('Top 5 employees: cut lost hours by 50%', 0.5*top5), ('Illness events of 24h+: shorten by 25%', 0.25*ill24), ('Planned care: move 30% outside work hours', 0.30*planned_h)]
R['whatif'] = [{'scenario': a, 'hours': round(float(b), 1), 'usd': round(float(b)*RATE)} for a, b in sc]
R['emp_top12'] = emp.head(12)[['ID', 'hours', 'events', 'hours_per_event', 'planned_share', 'cum_share']].to_dict('records')
R['reasons_top10'] = reasons.head(10)[['reason_name', 'reason_group', 'events', 'hours', 'avg_h']].to_dict('records')
R['dow'] = dow.to_dict('records'); R['season'] = season.to_dict('records')
R['emp_seg'] = f[['ID', 'hours', 'events', 'hours_per_event', 'planned_share', 'seg']].assign(name=f.seg.map(names)).to_dict('records')
json.dump(R, open('results.json', 'w'), indent=1, default=float)
print(json.dumps({k: R[k] for k in ('events','employees','hours','top5_share','top20_share','planned_hours','silhouette','whatif')}, default=float))
print(d); print(prof)
