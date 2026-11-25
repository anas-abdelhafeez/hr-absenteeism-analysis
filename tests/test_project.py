import json, os, re, pathlib, numpy as np, pandas as pd, duckdb
import analysis
ROOT = pathlib.Path(__file__).resolve().parents[1]
os.chdir(ROOT)
D = pd.read_csv('data/absences.csv'); R = json.load(open('results.json')); T = analysis.run_duckdb(analysis.load_queries())

def test_totals(): assert (len(D), D.emp_id.nunique(), int(D.hours.sum())) == (740, 36, 5124) == (R['events'], R['employees'], R['hours'])
def test_top5_share_matches_sql_and_pandas():
    e = D.groupby('emp_id').hours.sum().sort_values(ascending=False)
    assert round(100 * e.head(5).sum() / e.sum()) == 41 == round(R['top5_pct']) == round(float(T['top5_share'].top5_pct.iloc[0]))
def test_top5_range_contains_point(): assert R['top5_ci'][0] < R['top5_pct'] < R['top5_ci'][1]
def test_periods_cover_all_dated_events(): assert D.period.notna().sum() == 737 and set(D.period.dropna()) == {'2007-08', '2009-10'}
def test_persistence_sql_equals_python():
    p = T['period_hours'].set_index('emp_id').reindex(T['employee_hours'].emp_id).fillna(0)
    top = np.argsort(-p.hours_early.values, kind='stable')[:5]
    assert abs(100 * p.hours_late.values[top].sum() / p.hours_late.sum() - R['persist']['early_top5_late_share']) < 0.11
def test_persistence_beats_chance():
    P = R['persist']; assert P['early_top5_late_share'] > 2 * P['chance_share'] and P['p_luck'] < 0.01 and P['top10_overlap'] > P['top10_overlap_chance']
def test_persistence_survives_dropping_longest_event(): assert R['persist']['without_longest_event']['early_top5_late_share'] > 25
def test_monday_hours_exceed_events(): assert R['monday']['hours_pct'] > R['monday']['events_pct'] + 5
def test_weekday_shares_sum_to_100():
    assert abs(sum(w['hours_pct'] for w in R['weekday']) - 100) < 0.6 and abs(sum(w['events_pct'] for w in R['weekday']) - 100) < 0.6
def test_profile_has_no_clear_link(): assert all(abs(x['link_pct']) < 25 and x['p'] > 0.05 for x in R['profile'])
def test_planned_care_odds_below_one(): assert R['planned_care_odds']['hi'] < 1 and R['planned_care_odds']['lower_odds_pct'] == 93
def test_groups_cover_all_nonzero_hours(): assert sum(r['hours'] for r in R['groups']['rows']) == 5124
def test_no_forbidden_words_in_repo():
    bad = re.compile(r'pbix[-_ ]?mcp|pbixray|claude|gpt|openai|anthropic|\bllm\b|machine learning|artificial intelligence|\bAI\b', re.I)
    hits = []
    for f in ROOT.rglob('*'):
        if f.is_file() and f.suffix in {'.py', '.md', '.txt', '.sql', '.html', '.json', '.csv'} and '.git' not in f.parts and f.name != 'test_project.py':
            if bad.search(f.read_text(errors='ignore')): hits.append(str(f))
    assert hits == []
def test_dashboard_has_no_raw_decimals_for_ratios():
    html = open('docs/index.html').read(); assert 'odds ratio' not in html.lower() and '0.074' not in html
def test_every_dashboard_tab_present():
    html = open('docs/index.html').read(); assert [html.count(f'data-t="{t}"') for t in ('1. Problem', '2. Impact', '3. Where', '4. Who', '5. Why', '6. When', '7. Fix', 'Appendix')] == [1] * 8
