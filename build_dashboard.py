"""Builds docs/index.html from results.json. Run analysis.py first."""
import json
from dashboard_lib import *
R=json.load(open('results.json'))
def bar(cats,vals,color,horiz=False):
    o={**base(),**{"series":[{"type":"bar","data":vals,"itemStyle":{"color":color,"borderRadius":[4,4,0,0] if not horiz else [0,4,4,0]}}]}}
    if horiz:
        o["xAxis"]={"type":"value",**AX}; o["yAxis"]={"type":"category","data":cats,**AX}; o["grid"]={"left":150,"right":15,"top":10,"bottom":25}
    else:
        o["xAxis"]={"type":"category","data":cats,**AX}; o["yAxis"]={"type":"value",**AX}
    return ch(o)
T=R['hours']; rate=R['rate']; seg=R['segments']; dr=R['drivers']; wi=R['whatif']
emp=R['emp_top12']; cum=[e['cum_share'] for e in emp]
pc=[d for d in dr if d['factor']=='planned_care'][0]
inv=round(1/pc['odds_ratio'],1)
p=[]
p.append(page('1. Problem',lede(f'<b>The problem:</b> lost hours are concentrated, so a company-wide attendance policy aims at the wrong target. In this real dataset <b>{R["employees"]} employees lost {T:,} hours in {R["events"]} absence events</b>.')
+kpi([(f'{T:,}','hours lost, Jul 2007 to Jul 2010'),(str(R['events']),'absence events'),(str(R['employees']),'employees'),(f'{R["top5_share"]:.0f}%','of hours from the top 5 people'),(f'{R["planned_hours"]:,}','hours were planned care (visits, therapy, labs)')])
+'<div class="g"><div class="c w12"><h3>Cumulative share of lost hours, top 12 employees</h3><small>Source: UCI "Absenteeism at work" (CC BY 4.0), a Brazilian courier company. Real data, but not a call center.</small>'
+ch({**base(),**{"xAxis":{"type":"category","data":[str(e['ID']) for e in emp],"name":"employee ID",**AX},"yAxis":{"type":"value","max":100,"name":"% of hours",**AX},"series":[{"type":"line","data":cum,"itemStyle":{"color":"#ff6b8b"},"areaStyle":{"opacity":0.15}}]}})+'</div></div>'))
p.append(page('2. Impact',lede(f'<b>What the problem is worth:</b> three scenarios recover between {int(wi[2]["hours"]):,} and {int(wi[0]["hours"]):,} hours over the 3-year window. The cost is an <b>assumed ${int(rate)}/hour</b>, not a figure from the data.')
+kpi([(f'{int(w["hours"]):,} h',w['scenario']) for w in wi]+[(f'${wi[0]["usd"]:,}','value of the top scenario at the assumed rate')])
+'<div class="g"><div class="c w12"><h3>Hours recovered by scenario</h3>'+bar([w['scenario'] for w in reversed(wi)],[w['hours'] for w in reversed(wi)],'#27d3a2',True).replace('class="ch"','class="ch t"')+'</div></div>'
+ins('Honest reading',['<b>Scenarios are inputs, not forecasts.</b> 50%, 25% and 30% are my illustrations. Change them in sql/01_aggregates.sql.','<b>They overlap</b> (a top-5 employee may also have long illness events), so do not add them up.'])))
rs=R['reasons_top10']
p.append(page('3. Where',lede('<b>Where the hours come from:</b> musculoskeletal problems and injuries lead by hours, while medical and dental visits lead by number of events but are short.')
+'<div class="g"><div class="c w12"><h3>Hours lost by reason, top 10</h3>'+ch({**base(),**{"tooltip":{"trigger":"axis"},"grid":{"left":150,"right":15,"top":10,"bottom":25},"xAxis":{"type":"value",**AX},"yAxis":{"type":"category","data":[r['reason_name'] for r in reversed(rs)],**AX},
"series":[{"type":"bar","data":[{"value":r['hours'],"itemStyle":{"color":"#6c8cff" if r['reason_group']=='Planned care' else "#ff6b8b"}} for r in reversed(rs)]}]}},'ch t')+'<small>Blue = planned care, pink = illness, injury or other.</small></div></div>'
+tbl([{'Reason':r['reason_name'],'Events':r['events'],'Hours':r['hours'],'Avg h/event':r['avg_h']} for r in rs],['Reason','Events','Hours','Avg h/event'])))
cols=['#6c8cff','#ffb454','#27d3a2','#b07cff']
p.append(page('4. Who',lede(f'<b>Who is absent:</b> clustering the {R["employees"]-R["zero_hour_employees"]} employees with recorded hours gives three groups with different problems. {R["zero_hour_employees"]} employees have no recorded hours and are left out.')
+'<div class="g"><div class="c w12"><h3>Employees: events vs hours per event</h3>'+ch({**base(),**{"tooltip":{"trigger":"item"},"legend":{"top":0,"textStyle":{"color":"#9aa6d6"}},"grid":{"left":45,"right":15,"top":40,"bottom":40},"xAxis":{"type":"value","name":"events","nameLocation":"middle","nameGap":25,**AX},"yAxis":{"type":"value","name":"hours/event",**AX},
"series":[{"type":"scatter","name":s['name'].split(':')[0],"symbolSize":11,"itemStyle":{"color":cols[i]},"data":[[e['events'],round(e['hours_per_event'],1)] for e in R['emp_seg'] if e['seg']==s['seg']]} for i,s in enumerate(seg)]}},'ch t')+'</div></div>'
+tbl([{'Group':s['name'],'People':s['employees'],'Hours':int(s['hours']),'Share of hours':f'{s["share_hours_pct"]}%'} for s in seg],['Group','People','Hours','Share of hours'])
+ins('Honest reading',[f'<b>The clusters are weak.</b> Silhouette scores for 2, 3 and 4 groups are {R["silhouette"]["2"]}, {R["silhouette"]["3"]} and {R["silhouette"]["4"]}, nearly equal and below 0.35. I chose 3 for a readable story, not because the data forces it.','<b>36 people.</b> These are labels for discussion, not proven types.'])))
dd=[{'Factor':d['factor'].replace('_',' '),'Odds ratio':d['odds_ratio'],'95% CI':f'{d["lo"]} to {d["hi"]}','p-value':('<0.001' if d['p']<0.001 else d['p'])} for d in dr]
p.append(page('5. Why',lede(f'<b>Why some absences run long:</b> one factor stands out. The odds that a planned-care absence is long (8 hours or more) are about <b>{inv}x lower</b> than for illness or injury absences. Nothing else is statistically clear.')
+tbl(dd,['Factor','Odds ratio','95% CI','p-value'],'p-value',lambda v:'good' if (v=='<0.001' or float(v)<0.05) else 'warn')
+ins('Honest reading',[f'<b>Association, not cause.</b> Logistic model of "event is 8 h or more" on {R["model_n"]} events with hours above zero, standard errors clustered by employee ({R["model_clusters"]} clusters).','<b>"Planned care" is part of how the outcome is built</b> (visits are short by nature), so this finding is expected, not surprising. The useful part is that age, commute distance, tenure and workload show no clear effect.','<b>Monday</b> is borderline (odds ratio 1.37, p 0.10). I would not act on it.'])))
p.append(page('6. When',lede('<b>When it happens:</b> hours by weekday and by season. Differences are modest.')
+'<div class="g"><div class="c"><h3>Hours by weekday</h3>'+bar([d['d'] for d in R['dow']],[int(d['h']) for d in R['dow']],'#ffb454')+'</div><div class="c"><h3>Hours by season</h3>'+bar([d['s'] for d in R['season']],[int(d['h']) for d in R['season']],'#27d3a2')+'</div></div>'
+ins('Honest reading',['<b>Mondays and winter are the highest bars,</b> but the model above gives no clear weekday or season effect once reasons are controlled for.'])))
A,B,C=seg[0],seg[1],seg[2]
p.append(page('7. Fix',lede('<b>Recommendations by group</b>, for an HR or contact-center operations manager. Each ties to a number above.')
+fixes([('Group A: make planned care schedulable',f'{A["employees"]} people, {A["share_hours_pct"]}% of hours, many short visits. Offer bookable slots and easy shift swaps so visits stop creating gaps.','Who + Where tabs'),
('Group B: support longer illness and injury cases',f'{B["employees"]} people, {B["share_hours_pct"]}% of hours, about {B["hpe"]:.0f} hours per event. Early return-to-work contact and adjusted duties are the lever.','Who + Impact tabs'),
('Group C: leave alone',f'{C["employees"]} people, {C["share_hours_pct"]}% of hours. A blanket attendance policy would mostly hit this group and gain almost nothing.','Problem tab'),
('Target, do not blanket',f'The top 5 people are {R["top5_share"]:.0f}% of hours. Halving their hours is worth about {int(wi[0]["hours"]):,} hours.','Impact tab'),
('Rerun on your own data','Validate with call-center rosters and exit data before acting. This sample is 36 couriers.','Method')])
+'<p class="note">Method and limits: UCI Absenteeism at Work (740 rows, 36 employees, Brazilian courier company, 2007-2010, CC BY 4.0). Real data, not a call center, no attrition data. Cost uses an assumed $18/h. Models show association, not cause. 3 employees have only zero-hour records and are excluded from clustering. Code: analysis.py, sql/01_aggregates.sql.</p>'))
open('docs/index.html','w').write(doc('Workforce Absenteeism: Drivers, Segments and What-If','Real public data (UCI, CC BY 4.0): 740 absence events, 36 employees. SQL + statsmodels + scikit-learn',p))
print('ok')
