import json, pandas as pd, pytest
D = pd.read_csv('data/absenteeism_enriched.csv'); R = json.load(open('results.json'))
H = 'Absenteeism time in hours'
def test_totals(): assert (len(D), D.ID.nunique(), D[H].sum()) == (740, 36, 5124) == (R['events'], R['employees'], R['hours'])
def test_top5_share():
    e = D.groupby('ID')[H].sum().sort_values(ascending=False); assert round(100*e.head(5).sum()/e.sum()) == 41
def test_groups_cover_all_hours(): assert sum(s['hours'] for s in R['segments']) == 5124
def test_scenarios_nonneg(): assert all(w['hours'] > 0 for w in R['whatif'])
def test_planned_effect_is_negative(): assert [d for d in R['drivers'] if d['factor'] == 'planned_care'][0]['odds_ratio'] < 1
