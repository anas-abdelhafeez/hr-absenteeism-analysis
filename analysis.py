"""Absenteeism analysis. Run: python analysis.py  -> results.json
SQL lives in sql/queries.sql and is run on DuckDB here; tests/test_postgres.py runs the same file on PostgreSQL."""
import json, re, duckdb, numpy as np, pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

RATE = 18.0          # ASSUMED cost per lost hour in USD. Not in the data. The dashboard lets the reader change it.
SEED = 11

def load_queries(path='sql/queries.sql'):
    out = {}
    for block in re.split(r'-- name: ', open(path).read())[1:]:
        name, sql = block.split('\n', 1)
        out[name.strip()] = '\n'.join(l for l in sql.splitlines() if not l.strip().startswith('--')).strip().rstrip(';')
    return out

def run_duckdb(Q):
    con = duckdb.connect()
    con.execute("CREATE TABLE absences AS SELECT * FROM read_csv_auto('data/absences.csv')")
    return {k: con.execute(v).df() for k, v in Q.items()}

def main():
    Q = load_queries(); T = run_duckdb(Q); rng = np.random.default_rng(SEED)
    D = pd.read_csv('data/absences.csv'); D['hours'] = D.hours.astype(int)
    tot = T['totals'].iloc[0]; R = {'events': int(tot.events), 'employees': int(tot.employees), 'hours': int(tot.hours), 'rate': RATE}
    eh = T['employee_hours']; hrs = eh.hours.values.astype(float)
    R['top5_pct'] = float(T['top5_share'].top5_pct.iloc[0])
    # top-5 share: bootstrap over employees (how much does it depend on who is in the sample)
    bs = [np.sort(x)[::-1][:5].sum() / x.sum() for x in (rng.choice(hrs, len(hrs)) for _ in range(5000))]
    R['top5_ci'] = [round(100 * float(np.percentile(bs, q))) for q in (2.5, 97.5)]
    R['top5_hours'] = int(np.sort(hrs)[::-1][:5].sum())
    cum = 100 * np.cumsum(np.sort(hrs)[::-1]) / hrs.sum()
    R['lorenz'] = [round(float(c), 1) for c in cum]
    # ---------------- persistence: same people in 2007-08 and 2009-10?
    P = T['period_hours'].set_index('emp_id').reindex(eh.emp_id).fillna(0)   # all employees; 0 if absent in a period
    he, hl = P.hours_early.values, P.hours_late.values
    obs = hl[np.argsort(-he, kind='stable')[:5]].sum() / hl.sum()
    assert abs(100 * obs - float(T['early_top5_late_share'].late_share_pct.iloc[0])) < 0.1   # SQL and Python agree
    null = np.array([hl[rng.permutation(len(hl))[:5]].sum() / hl.sum() for _ in range(20000)])
    R['persist'] = {'n': int(len(he)), 'early_top5_late_share': round(100 * float(obs), 1), 'chance_share': round(100 * float(null.mean()), 1),
                    'p_luck': float((null >= obs).mean()), 'rank_corr_hours': round(float(stats.spearmanr(he, hl)[0]), 3),
                    'rank_corr_hours_p': float(stats.spearmanr(he, hl)[1]),
                    'rank_corr_events': round(float(stats.spearmanr(P.events_early, P.events_late)[0]), 3),
                    'rank_corr_events_p': float(stats.spearmanr(P.events_early, P.events_late)[1])}
    top10e = set(P.index[np.argsort(-he, kind='stable')[:10]]); top10l = set(P.index[np.argsort(-hl, kind='stable')[:10]])
    R['persist']['top10_overlap'] = len(top10e & top10l); R['persist']['top10_overlap_chance'] = round(10 * 10 / len(he), 1)
    # robustness: drop each employee's single longest event in each period, do the top-5 result still hold?
    A = D[D.period.notna()].copy(); A['rk'] = A.groupby(['emp_id', 'period']).hours.rank(method='first', ascending=False)
    B = A[A.rk > 1].pivot_table(index='emp_id', columns='period', values='hours', aggfunc='sum', fill_value=0).reindex(eh.emp_id).fillna(0)
    he2, hl2 = B['2007-08'].values, B['2009-10'].values
    R['persist']['without_longest_event'] = {'early_top5_late_share': round(100 * float(hl2[np.argsort(-he2, kind='stable')[:5]].sum() / hl2.sum()), 1),
                                              'rank_corr': round(float(stats.spearmanr(he2, hl2)[0]), 3)}
    order = np.argsort(-he, kind='stable')
    R['persist_top8'] = [{'id': int(P.index[i]), 'early': int(he[i]), 'late': int(hl[i])} for i in order[:8]]
    R['persist_scatter'] = [{'id': int(P.index[i]), 'early': int(he[i]), 'late': int(hl[i]), 'top5': bool(j < 5)} for j, i in enumerate(order)]
    # ---------------- not who they are: employee profile vs total hours
    E = D.groupby('emp_id').agg(hours=('hours', 'sum'), age=('age', 'first'), distance_km=('distance_km', 'first'), service_years=('service_years', 'first'),
                                bmi=('bmi', 'first'), children=('children', 'first'), transport=('transport_expense', 'first'), workload=('workload', 'mean'))
    names = {'age': 'Age', 'distance_km': 'Commute distance', 'service_years': 'Years at the company', 'bmi': 'Body mass index', 'children': 'Number of children',
             'transport': 'Transport expense', 'workload': 'Average workload'}
    prof = []
    for c, n in names.items():
        r, p = stats.spearmanr(E[c], E.hours); prof.append({'factor': n, 'link_pct': round(100 * float(r)), 'p': round(float(p), 3)})
    R['profile'] = prof; R['profile_n'] = int(len(E))
    # ---------------- weekday: events are even, hours are not
    W = T['weekday']; R['weekday'] = W[['weekday', 'events', 'hours', 'events_pct', 'hours_pct', 'avg_hours']].to_dict('records')
    Dw = A.copy(); mon_obs = Dw[Dw.weekday_no == 2].hours.sum() / Dw.hours.sum()
    grp = [g.values for _, g in Dw.groupby('emp_id').weekday_no]; hh = [g.values for _, g in Dw.groupby('emp_id').hours]
    nullm = []
    for _ in range(4000):
        s = 0
        for w, h in zip(grp, hh): s += h[rng.permutation(len(w)) < 0].sum() if False else h[(rng.permutation(w) == 2)].sum()
        nullm.append(s / Dw.hours.sum())
    R['monday'] = {'hours_pct': round(100 * float(mon_obs), 1), 'events_pct': round(100 * float((Dw.weekday_no == 2).mean()), 1),
                   'p_luck': float((np.array(nullm) >= mon_obs).mean())}
    top5ids = set(eh.emp_id.head(5)); X5 = Dw[~Dw.emp_id.isin(top5ids)]
    R['monday']['hours_pct_without_top5'] = round(100 * float(X5[X5.weekday_no == 2].hours.sum() / X5.hours.sum()), 1)
    # ---------------- reasons and planned care
    rs = T['reasons']; R['reasons_top8'] = rs.head(8).to_dict('records')
    pg = T['planned_vs_other'].set_index('reason_group'); R['planned'] = {'hours': int(pg.loc['Planned care', 'hours']), 'events': int(pg.loc['Planned care', 'events'])}
    ev = D[D.hours > 0].copy(); ev['long'] = (ev.hours >= 8).astype(int)
    X = pd.DataFrame({'planned_care': (ev.reason_group == 'Planned care').astype(int), 'monday': (ev.weekday_no == 2).astype(int), 'winter': (ev.season == 'Winter').astype(int),
                      'distance_10km': ev.distance_km / 10, 'age_10y': ev.age / 10, 'service_10y': ev.service_years / 10, 'workload_100': ev.workload / 100})
    mod = sm.Logit(ev['long'], sm.add_constant(X)).fit(disp=0, cov_type='cluster', cov_kwds={'groups': ev.emp_id})
    ci = np.exp(mod.conf_int())
    R['planned_care_odds'] = {'odds_ratio': round(float(np.exp(mod.params['planned_care'])), 3), 'lo': round(float(ci.loc['planned_care', 0]), 3),
                              'hi': round(float(ci.loc['planned_care', 1]), 3), 'p': float(mod.pvalues['planned_care']), 'n': int(len(ev)), 'clusters': int(ev.emp_id.nunique()),
                              'lower_odds_pct': round(100 * (1 - float(np.exp(mod.params['planned_care']))))}
    R['zero_hour_events'] = int((D.hours == 0).sum())
    # ---------------- appendix: employee groups (weak structure, labelled as such)
    f = D.groupby('emp_id').agg(hours=('hours', 'sum'), events=('hours', 'size'), planned=('reason_group', lambda s: (s == 'Planned care').mean()))
    f['hpe'] = f.hours / f.events; f = f[f.hours > 0].copy()
    Z = StandardScaler().fit_transform(np.c_[np.log1p(f.events), np.log1p(f.hpe), f.planned])
    sil = {k: round(float(silhouette_score(Z, KMeans(k, n_init=20, random_state=SEED).fit_predict(Z))), 3) for k in (2, 3, 4)}
    f['seg'] = KMeans(3, n_init=20, random_state=SEED).fit_predict(Z)
    g = f.groupby('seg').agg(people=('hours', 'size'), hours=('hours', 'sum'), events=('events', 'sum'), planned=('planned', 'mean')).assign(hpe=lambda x: x.hours / x.events)
    g = g.sort_values('events', ascending=False); g['label'] = [f'Group {c}' for c in 'ABC']; g['share_pct'] = (100 * g.hours / g.hours.sum()).round(0)
    g['events_each'] = (g.events / g.people).round(0)
    R['groups'] = {'silhouette': sil, 'excluded_zero_hour_people': int(R['employees'] - len(f)),
                   'rows': [{'label': r.label, 'people': int(r.people), 'hours': int(r.hours), 'share_pct': int(r.share_pct), 'events_each': int(r.events_each), 'hpe': round(float(r.hpe), 1), 'planned_pct': round(100 * float(r.planned))} for r in g.itertuples()]}
    # ---------------- impact defaults (inputs, not forecasts)
    R['impact'] = {'top5_hours': R['top5_hours'], 'default_cut_pct': 50, 'default_rate': RATE, 'all_hours': R['hours']}
    json.dump(R, open('results.json', 'w'), indent=1, default=float)
    print(json.dumps({k: R[k] for k in ('top5_pct', 'top5_ci', 'persist', 'monday', 'planned_care_odds', 'profile')}, indent=1, default=float))
    print(R['groups'])

if __name__ == '__main__':
    main()
