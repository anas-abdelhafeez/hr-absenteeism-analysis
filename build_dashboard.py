"""Builds docs/index.html from results.json. Run analysis.py first."""
import json
from dashboard_lib import *
R = json.load(open('results.json')); P = R['persist']; M = R['monday']; PO = R['planned_care_odds']; I = R['impact']
pct = lambda x: f'{round(x):d}%'
def opt(**kw): return {**base(), **kw}
def luck(p): return 'under 1 in 100' if p < 0.01 else f'{p:.0%}'
pages = []

# 1 PROBLEM: one headline
pages.append(page('1. Problem',
  f'<div class="hero"><div class="n">{pct(R["top5_pct"])}</div><div class="t">of all lost hours come from <b>5 of {R["employees"]} people</b>, and they keep doing it: '
  f'the 5 heaviest in 2007-08 caused <b>{pct(P["early_top5_late_share"])}</b> of the hours in 2009-10. Five random people would cause {pct(P["chance_share"])}.</div>'
  f'<div class="s">Real absence records, {R["events"]} events, {R["hours"]:,} hours, Jul 2007 to Jul 2010. A Brazilian courier company, used here as a stand-in for any shift-based team.</div></div>'
  + '<div class="g"><div class="c w12"><h3>Share of all lost hours, people ranked from most to least absent</h3><small>Dotted line = what an even spread would look like</small>'
  + ch(opt(xAxis={"type": "category", "data": [str(i + 1) for i in range(len(R['lorenz']))], "name": "people (most absent first)", "nameLocation": "middle", "nameGap": 26, **AX},
           yAxis={"type": "value", "max": 100, "axisLabel": {"color": "#9aa6d6", "formatter": "{value}%"}, "axisLine": AX["axisLine"]},
           grid={"left": 50, "right": 15, "top": 20, "bottom": 55}, series=[{"type": "line", "data": R['lorenz'], "showSymbol": False, "lineStyle": {"color": "#ff6b8b", "width": 3}, "areaStyle": {"opacity": 0.18, "color": "#ff6b8b"},
                    "markLine": {"silent": True, "symbol": "none", "lineStyle": {"color": "#9aa6d6", "type": "dotted"}, "label": {"show": False}, "data": [[{"coord": [0, 0]}, {"coord": [len(R['lorenz']) - 1, 100]}]]}}],
           tooltip={"trigger": "axis", "valueFormatter": None, "backgroundColor": "#222b52", "textStyle": {"color": "#e8ecff"}}), 'ch t') + '</div></div>'))

# 2 IMPACT: calculator
pages.append(page('2. Impact',
  lede('<b>What it is worth:</b> move the slider and set your own cost. The number of hours comes from the data. <b>The cost per hour is an assumption</b>, so type your own.')
  + f'<div class="calc"><label>Cut the top 5 people\'s lost hours by: <b id="cv">{I["default_cut_pct"]}%</b></label><input id="cut" type="range" min="0" max="100" value="{I["default_cut_pct"]}">'
    f'<label>Cost of one lost hour, in USD <span class="tag">assumed, not from the data</span></label><input id="rate" type="number" min="0" value="{int(I["default_rate"])}">'
    f'<div class="out"><div><b id="oh">0</b><span>hours recovered in 3 years</span></div><div><b id="oy">0</b><span>hours per year</span></div><div><b id="ou">$0</b><span>value in 3 years</span></div></div></div>'
  + f'<script>const T5={I["top5_hours"]};function calc(){{const c=+document.getElementById("cut").value,r=+document.getElementById("rate").value||0,h=T5*c/100;'
    f'document.getElementById("cv").textContent=c+"%";document.getElementById("oh").textContent=Math.round(h).toLocaleString();document.getElementById("oy").textContent=Math.round(h/3).toLocaleString();'
    f'document.getElementById("ou").textContent="$"+Math.round(h*r).toLocaleString();}}["cut","rate"].forEach(i=>document.getElementById(i).addEventListener("input",calc));calc();</script>'
  + ins('How sure', [f'The top 5 hold <b>{pct(R["top5_pct"])}</b> of hours in this sample. With only {R["employees"]} people, resampling gives a range of <b>{R["top5_ci"][0]}% to {R["top5_ci"][1]}%</b>.',
                     f'The top 5 total {I["top5_hours"]:,} hours of {I["all_hours"]:,}. The slider is an input, not a forecast.'])))

# 3 WHERE: reasons
rs = R['reasons_top8']; pl = R['planned']
pages.append(page('3. Where',
  lede(f'<b>Where the hours come from:</b> injuries and musculoskeletal problems lose the most hours. Medical and dental visits are the most frequent, but short.')
  + '<div class="g"><div class="c w12"><h3>Hours lost by reason</h3><small>Blue = planned care (visits, labs, therapy). Pink = illness, injury or other.</small>'
  + ch(opt(tooltip={"trigger": "axis", "backgroundColor": "#222b52", "textStyle": {"color": "#e8ecff"}}, grid={"left": 140, "right": 15, "top": 10, "bottom": 25}, xAxis={"type": "value", **AX},
           yAxis={"type": "category", "data": [r['reason_name'] for r in reversed(rs)], **AX},
           series=[{"type": "bar", "data": [{"value": int(r['hours']), "itemStyle": {"color": "#6c8cff" if r['reason_group'] == 'Planned care' else "#ff6b8b", "borderRadius": [0, 4, 4, 0]}} for r in reversed(rs)]}]), 'ch t') + '</div></div>'
  + kpi([(pct(100 * pl['events'] / R['events']), 'of events are planned care'), (pct(100 * pl['hours'] / R['hours']), 'of hours are planned care')])))

# 4 WHO: persistence (the finding)
t8 = R['persist_top8']; sc = R['persist_scatter']
pages.append(page('4. Who',
  lede(f'<b>Who:</b> the same people. Ranked by hours in 2007-08, <b>{P["top10_overlap"]} of the top 10</b> were still in the top 10 in 2009-10. Chance alone gives about {round(P["top10_overlap_chance"])}.')
  + kpi([(pct(P['early_top5_late_share']), 'of 2009-10 hours from the 2007-08 top 5'), (pct(P['chance_share']), 'what 5 random people would give')])
  + '<div class="g"><div class="c w12"><h3>The 8 most absent in 2007-08, and the same people in 2009-10</h3><small>Hours lost, by employee ID</small>'
  + ch(opt(legend={"top": 0, "textStyle": {"color": "#9aa6d6"}}, grid={"left": 45, "right": 15, "top": 38, "bottom": 30},
           xAxis={"type": "category", "data": [f'ID {t["id"]}' for t in t8], **AX}, yAxis={"type": "value", **AX},
           series=[{"type": "bar", "name": "2007-08", "data": [t['early'] for t in t8], "itemStyle": {"color": "#6c8cff", "borderRadius": [4, 4, 0, 0]}},
                   {"type": "bar", "name": "2009-10", "data": [t['late'] for t in t8], "itemStyle": {"color": "#ff6b8b", "borderRadius": [4, 4, 0, 0]}}]), 'ch t') + '</div></div>'
  + ins('How sure', [f'Chance of seeing this by luck (random shuffle of {P["n"]} employees, 20,000 tries): <b>{luck(P["p_luck"])}</b>.',
                     f'Still holds when each person\'s single longest absence is removed: top 5 give <b>{pct(P["without_longest_event"]["early_top5_late_share"])}</b> of later hours. So it is a repeating pattern, not one long illness.',
                     'Same answer for number of events, not only hours. Employees with no records in a period count as zero.'])))

# 5 WHY: profile does not explain it
pr = R['profile']
pages.append(page('5. Why',
  lede('<b>Why:</b> not who they are. Age, commute, years at the company, children, BMI, travel cost and workload do not separate heavy from light absentees.')
  + '<div class="g"><div class="c w12"><h3>How strongly each trait moves with total hours</h3><small>Rank correlation, -100% to +100%. Every bar is within the noise for 36 people.</small>'
  + ch(opt(tooltip={"trigger": "axis", "backgroundColor": "#222b52", "textStyle": {"color": "#e8ecff"}}, grid={"left": 140, "right": 20, "top": 10, "bottom": 28},
           xAxis={"type": "value", "min": -100, "max": 100, "axisLabel": {"color": "#9aa6d6", "formatter": "{value}%"}, "axisLine": AX["axisLine"]},
           yAxis={"type": "category", "data": [x['factor'] for x in reversed(pr)], **AX},
           series=[{"type": "bar", "data": [{"value": x['link_pct'], "itemStyle": {"color": "#6b749e"}} for x in reversed(pr)]}]), 'ch t') + '</div></div>'
  + kpi([(f'{PO["lower_odds_pct"]}%', 'lower odds that a planned-care absence is long (8 h or more)')])
  + ins('Honest reading', [f'No trait is clearly linked (smallest p-value {min(x["p"] for x in pr):.2f}, with 7 traits tested). Treat this as "no evidence", not "proof of no effect": {R["profile_n"]} people is small.',
                           f'Planned care is short by nature, so the {PO["lower_odds_pct"]}% is expected (95% range {round(100*(1-PO["hi"]))}% to {round(100*(1-PO["lo"]))}% lower). Logistic regression on {PO["n"]} events, errors clustered by employee.'])))

# 6 WHEN: weekday
W = R['weekday']
pages.append(page('6. When',
  lede(f'<b>When:</b> Mondays. They hold {pct(M["events_pct"])} of absences but <b>{pct(M["hours_pct"])} of hours</b>: Monday absences run longer. Thursday is the lightest.')
  + '<div class="g"><div class="c w12"><h3>Share of absences vs share of hours, by weekday</h3><small>If every weekday were alike, both bars would be 20%.</small>'
  + ch(opt(legend={"top": 0, "textStyle": {"color": "#9aa6d6"}}, grid={"left": 45, "right": 15, "top": 38, "bottom": 30}, xAxis={"type": "category", "data": [w['weekday'] for w in W], **AX},
           yAxis={"type": "value", "axisLabel": {"color": "#9aa6d6", "formatter": "{value}%"}, "axisLine": AX["axisLine"]},
           series=[{"type": "bar", "name": "Share of absences", "data": [w['events_pct'] for w in W], "itemStyle": {"color": "#6c8cff", "borderRadius": [4, 4, 0, 0]}},
                   {"type": "bar", "name": "Share of hours", "data": [w['hours_pct'] for w in W], "itemStyle": {"color": "#ffb454", "borderRadius": [4, 4, 0, 0]}}]), 'ch t') + '</div></div>'
  + ins('How sure', [f'Chance of a Monday share this high by luck (weekday shuffled within each person): <b>{luck(M["p_luck"])}</b>.',
                     f'Without the top 5 people, Mondays are still the largest day but smaller: <b>{pct(M["hours_pct_without_top5"])}</b> of hours.',
                     'Months and seasons also differ, but with 3 years and 36 people two long absences can create a peak, so I do not build on them.'])))

# 7 FIX
pages.append(page('7. Fix',
  lede('<b>Fix:</b> aim at the people, not at everyone. A company-wide attendance policy spreads effort over the many people who cause little of the loss.')
  + fixes([('1. Support the repeat group', f'Each quarter, list the people whose hours were highest in the last two years and offer a private check-in and support plan. The top 5 are {pct(R["top5_pct"])} of hours.', 'Who tab'),
           ('2. Pilot Monday cover', f'Mondays carry {pct(M["hours_pct"])} of hours. Trial a Monday return-to-work call or a shift swap for 8 weeks and compare with the other days.', 'When tab'),
           ('3. Make planned care easy to book', f'{pct(100*pl["events"]/R["events"])} of events are visits. Bookable slots turn surprise gaps into planned ones.', 'Where tab'),
           ('4. Prove it on your own data', 'Repeat the same-people test on your own roster before acting. 36 couriers is a starting point, not a verdict.', 'Method')])))

# APPENDIX
G = R['groups']; rows = [{'Group': r['label'], 'People': r['people'], 'Events each': r['events_each'], 'Hours per event': r['hpe'], 'Planned care': f'{r["planned_pct"]}%', 'Share of hours': f'{r["share_pct"]}%'} for r in G['rows']]
pages.append(page('Appendix',
  lede('<b>Appendix:</b> employee groups and limits. The groups are a rough label, not a finding. The story above does not depend on them.')
  + tbl(rows, ['Group', 'People', 'Events each', 'Hours per event', 'Planned care', 'Share of hours'])
  + ins('Why the groups are weak', [f'Cluster quality (silhouette) for 2, 3 and 4 groups: {G["silhouette"]["2"]}, {G["silhouette"]["3"]}, {G["silhouette"]["4"]}. All low and almost equal, so 3 is chosen for readability.',
                                    f'{G["excluded_zero_hour_people"]} people with no recorded hours are left out.'])
  + ins('Limits', ['36 people and 740 events. Differences are patterns, not proof of cause.', 'A Brazilian courier company, 2007-2010. Real data, not a call center, no attrition data.',
                   f'{R["zero_hour_events"]} events have 0 recorded hours (kept in counts, dropped from the long-absence model).',
                   'The cost per hour is an assumption you can change. The split into 2007-08 and 2009-10 is by calendar year taken from record order, because the file has no dates.',
                   'The data file is CC BY 4.0 (UCI "Absenteeism at work"). Code and SQL are in the repo; the same SQL gives the same numbers on DuckDB and PostgreSQL.'])))
open('docs/index.html', 'w').write(doc('Who Is Absent? The Same Few People, Again and Again', f'Real public data (UCI, CC BY 4.0): {R["events"]} absence events, {R["employees"]} employees', pages))
print('ok')
