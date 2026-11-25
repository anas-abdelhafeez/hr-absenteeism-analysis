"""Builds powerbi/absenteeism_story.pbix programmatically with pbix-mcp (MIT). NOT opened in Power BI Desktop."""
import json, pandas as pd
from pbix_mcp.builder import PBIXBuilder
R = json.load(open('results.json'))
d = pd.read_csv('data/absenteeism_enriched.csv')
grp = {e['ID']: e['name'].split(':')[0] for e in R['emp_seg']}
planned = ['Medical consultation','Dental consultation','Physiotherapy','Laboratory examination','Patient follow-up','Blood donation']
rows = [{'Employee ID': str(int(r.ID)), 'Reason': r.reason_name,
         'Reason group': 'Planned care' if r.reason_name in planned else 'Illness, injury, other',
         'Weekday': r.dow_name, 'Season': r.season_name, 'Hours': int(r['Absenteeism time in hours']),
         'Employee group': grp.get(int(r.ID), 'No recorded hours')} for _, r in d.iterrows()]
b = PBIXBuilder('Absenteeism Story')
b.add_table('Events', [{'name': c, 'data_type': 'Int64' if c == 'Hours' else 'String'} for c in rows[0]], rows=rows)
M = [('Total Hours', 'SUM(Events[Hours])'), ('Absence Events', 'COUNTROWS(Events)'), ('Employees', 'DISTINCTCOUNT(Events[Employee ID])'),
     ('Planned Care Hours', 'CALCULATE(SUM(Events[Hours]), Events[Reason group] = "Planned care")'),
     ('Planned Care Share', 'DIVIDE([Planned Care Hours], [Total Hours])'),
     ('Long Event Share', 'DIVIDE(CALCULATE(COUNTROWS(Events), Events[Hours] >= 8), CALCULATE(COUNTROWS(Events), Events[Hours] > 0))'),
     ('Cost at 18 USD per hour (assumed)', '[Total Hours] * 18'),
     ('Scenario: shift 30% of planned care', '[Planned Care Hours] * 0.3')]
for n, x in M: b.add_measure('Events', n, x)
def card(i, m, x): return {'name': f'c{i}', 'type': 'card', 'x': x, 'y': 10, 'width': 230, 'height': 90, 'config': {'measure': m}}
def chart(n, t, cat, m, x, y, w, h): return {'name': n, 'type': t, 'x': x, 'y': y, 'width': w, 'height': h, 'config': {'category': {'table': cat.split('[')[0], 'column': cat.split('[')[1].rstrip(']')}, 'measure': m}}
b.add_page('1 Problem', [card(1, 'Total Hours', 10), card(2, 'Absence Events', 250), card(3, 'Employees', 490), card(4, 'Planned Care Share', 730),
                          chart('p1', 'clusteredColumnChart', 'Events[Weekday]', 'Total Hours', 10, 120, 700, 350)])
b.add_page('2 Where', [chart('w1', 'clusteredBarChart', 'Events[Reason]', 'Total Hours', 10, 10, 900, 600), chart('w2', 'pieChart', 'Events[Reason group]', 'Total Hours', 10, 620, 400, 250)])
b.add_page('3 Who', [{'name': 's1', 'type': 'slicer', 'x': 10, 'y': 10, 'width': 250, 'height': 200, 'config': {'column': {'table': 'Events', 'column': 'Employee group'}}},
                     chart('o1', 'clusteredColumnChart', 'Events[Employee group]', 'Total Hours', 280, 10, 600, 350), card(5, 'Long Event Share', 280)])
b.add_page('4 When', [chart('t1', 'clusteredColumnChart', 'Events[Season]', 'Total Hours', 10, 10, 500, 350), chart('t2', 'clusteredColumnChart', 'Events[Weekday]', 'Total Hours', 520, 10, 500, 350)])
b.add_page('5 Fix', [card(6, 'Scenario: shift 30% of planned care', 10), card(7, 'Cost at 18 USD per hour (assumed)', 250)])
b.save('powerbi/absenteeism_story.pbix')
print('saved')
