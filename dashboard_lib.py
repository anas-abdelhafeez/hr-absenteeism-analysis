"""Small helpers for the dark multi-tab ECharts dashboard (HTML, loads ECharts from jsDelivr CDN)."""
import json
CSS = open('/dev/stdin').read() if False else """:root{--bg:#0f1426;--card:#1a2140;--card2:#222b52;--tx:#e8ecff;--mut:#9aa6d6;--a:#6c8cff;--b:#27d3a2;--c:#ffb454;--d:#ff6b8b;--e:#b07cff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font-family:Segoe UI,Roboto,Arial,sans-serif}
header{padding:16px 22px;background:linear-gradient(120deg,#1c2a6b,#5b2a86 70%,#a02c6e)}
header h1{margin:0;font-size:21px}header p{margin:4px 0 0;color:#d7dcff;font-size:13px}
.story{display:flex;gap:5px;flex-wrap:wrap;padding:8px 18px;background:#10152e;color:var(--mut);font-size:11px;align-items:center}
.story b{color:var(--c)}
nav{display:flex;gap:6px;padding:10px 18px;overflow-x:auto;background:#141a33;position:sticky;top:0;z-index:5}
nav button{border:0;background:var(--card);color:var(--mut);padding:9px 14px;border-radius:20px;font-weight:600;cursor:pointer;white-space:nowrap;font-size:13px}
nav button.on{background:linear-gradient(90deg,var(--a),var(--e));color:#fff}
.wrap{padding:6px 18px 30px;max-width:1400px;margin:auto}
.pg{display:none}.pg.on{display:block}
.kpis{margin-top:14px;display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:14px}
.k{background:var(--card);border-radius:14px;padding:14px 16px;border-top:3px solid var(--a)}
.k:nth-child(2){border-color:var(--b)}.k:nth-child(3){border-color:var(--c)}.k:nth-child(4){border-color:var(--d)}.k:nth-child(5){border-color:var(--e)}.k:nth-child(6){border-color:var(--a)}
.k b{font-size:24px;display:block}.k span{font-size:12px;color:var(--mut)}
.lede{background:var(--card2);border-left:4px solid var(--a);border-radius:10px;padding:12px 16px;font-size:15px;line-height:1.5;margin:12px 0}
.g{display:grid;grid-template-columns:repeat(12,1fr);gap:14px}
.c{background:var(--card);border-radius:14px;padding:12px 14px;grid-column:span 6;min-width:0}
.c.w4{grid-column:span 4}.c.w8{grid-column:span 8}.c.w12{grid-column:span 12}
.c h3{margin:0 0 2px;font-size:14px}.c small{color:var(--mut);font-size:12px;display:block;margin-bottom:4px}
.ch{height:300px}.ch.t{height:380px}
.ins{background:var(--card);border-radius:14px;padding:14px 18px;margin-top:14px;border-left:4px solid var(--c)}
.ins h3{margin:0 0 6px}.ins li{margin:6px 0;font-size:14px;line-height:1.45}.ins b{color:var(--c)}
.fix{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:12px}
.f{background:var(--card);border-radius:14px;padding:14px 16px;border-top:3px solid var(--b)}
.f h4{margin:0 0 6px;font-size:14px;color:var(--b)}.f p{margin:0;font-size:13px;color:var(--tx);line-height:1.5}.f small{color:var(--mut);font-size:11px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:7px 8px;text-align:right;border-bottom:1px solid #2c3562}th:first-child,td:first-child{text-align:left;white-space:nowrap}th{color:var(--mut)}
.pill{padding:2px 8px;border-radius:10px;font-size:12px}.good{background:#134d3c;color:#6df0c2}.bad{background:#59203a;color:#ff9db6}.mid{background:#4a3a12;color:#ffd27a}
pre{background:#0b0f22;border:1px solid #2c3562;border-radius:10px;padding:10px;font-size:11px;overflow-x:auto;color:#c9d4ff}
details summary{color:var(--a);cursor:pointer;font-size:13px;margin:8px 0 4px}
.note{color:var(--mut);font-size:12px;margin-top:14px;line-height:1.5}
.hero{background:linear-gradient(135deg,#232c63,#3a2a6e);border-radius:16px;padding:18px 20px;margin:12px 0}
.hero .n{font-size:44px;font-weight:800;line-height:1;color:#ff8fa8}.hero .t{font-size:17px;line-height:1.4;margin-top:8px}.hero .s{color:var(--mut);font-size:13px;margin-top:8px}
.vs{display:flex;gap:12px;flex-wrap:wrap;margin:12px 0}.vs .k{flex:1;min-width:140px}
.calc{background:var(--card);border-radius:14px;padding:16px 18px;margin:12px 0}
.calc label{display:block;font-size:13px;color:var(--mut);margin:10px 0 4px}.calc input[type=range]{width:100%}
.calc input[type=number]{background:#0f1426;color:var(--tx);border:1px solid #3a4580;border-radius:8px;padding:8px;width:110px;font-size:16px}
.out{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-top:14px}.out div{background:var(--card2);border-radius:12px;padding:12px}.out b{font-size:24px;display:block;color:var(--b)}.out span{font-size:12px;color:var(--mut)}
.tag{display:inline-block;background:#4a3a12;color:#ffd27a;border-radius:10px;padding:2px 8px;font-size:11px;margin-left:6px}
@media(max-width:900px){.c,.c.w4,.c.w8{grid-column:span 12}.ch{height:260px}}"""

JS = """const nav=document.getElementById('nav'),pages=[...document.querySelectorAll('.pg')];
pages.forEach((p,i)=>{const b=document.createElement('button');b.textContent=p.dataset.t;if(i==0)b.classList.add('on');
b.onclick=()=>{pages.forEach(x=>x.classList.remove('on'));p.classList.add('on');[...nav.children].forEach(x=>x.classList.remove('on'));b.classList.add('on');
requestAnimationFrame(()=>{p.querySelectorAll('.ch').forEach(el=>{if(!el._c){el._c=echarts.init(el);el._c.setOption(JSON.parse(el.dataset.o));}else el._c.resize();});});};
nav.appendChild(b);});
const si=Math.min(pages.length-1,Math.max(0,parseInt((location.hash||'#1').slice(1))-1||0));
pages.forEach(x=>x.classList.remove('on'));pages[si].classList.add('on');[...nav.children].forEach(x=>x.classList.remove('on'));nav.children[si].classList.add('on');
requestAnimationFrame(()=>{pages[si].querySelectorAll('.ch').forEach(el=>{el._c=echarts.init(el);el._c.setOption(JSON.parse(el.dataset.o));});});
window.addEventListener('resize',()=>{document.querySelectorAll('.ch').forEach(el=>el._c&&el._c.resize());});"""

AX = {"axisLabel":{"color":"#9aa6d6"},"axisLine":{"lineStyle":{"color":"#2c3562"}}}
def base(): return {"backgroundColor":"transparent","textStyle":{"color":"#e8ecff"},
 "tooltip":{"trigger":"axis","backgroundColor":"#222b52","borderColor":"#3a4580","textStyle":{"color":"#e8ecff"}},
 "grid":{"left":45,"right":15,"top":32,"bottom":30}}
def ch(opt, cls="ch"): return f'<div class="{cls}" data-o=\'{json.dumps(opt,separators=(",",":"))}\'></div>'
def kpi(items): return '<div class="kpis">'+''.join(f'<div class="k"><b>{v}</b><span>{s}</span></div>' for v,s in items)+'</div>'
def ins(title, items): return f'<div class="ins"><h3>{title}</h3><ul>'+''.join(f'<li>{i}</li>' for i in items)+'</ul></div>'
def lede(t): return f'<div class="lede">{t}</div>'
def fixes(items): return '<div class="fix">'+''.join(f'<div class="f"><h4>{t}</h4><p>{p}</p><small>{s}</small></div>' for t,p,s in items)+'</div>'
def page(t, b): return f'<div class="pg" data-t="{t}"><div class="wrap">{b}</div></div>'
def tbl(rows, cols, pill_col=None, pill_rule=None, maxn=None):
    h='<table><tr>'+''.join(f'<th>{c}</th>' for c in cols)+'</tr>'
    for r in (rows[:maxn] if maxn else rows):
        h+='<tr>'
        for c in cols:
            v=r.get(c,'')
            if pill_col==c and pill_rule: h+=f'<td><span class="pill {pill_rule(v)}">{v}</span></td>'
            else: h+=f'<td>{v}</td>'
        h+='</tr>'
    return h+'</table>'
def story(): return '<div class="story">Story flow: <b>1 Problem</b> &rarr; <b>2 Impact</b> &rarr; <b>3 Where</b> &rarr; <b>4 Who</b> &rarr; <b>5 Why</b> &rarr; <b>6 When</b> &rarr; <b>7 Fix</b> &middot; Appendix</div>'
def doc(title, subtitle, pages):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{CSS}</style>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script></head><body>
<header><h1>{title}</h1><p>{subtitle}</p></header>{story()}
<nav id="nav"></nav>{''.join(pages)}<script>{JS}</script></body></html>"""
def heat(data, days, hours, name, vmin, vmax):
    return {"backgroundColor":"transparent","tooltip":{"position":"top","backgroundColor":"#222b52","textStyle":{"color":"#e8ecff"}},
     "grid":{"left":70,"right":15,"top":10,"bottom":60},
     "xAxis":{"type":"category","data":hours,**AX},"yAxis":{"type":"category","data":days,**AX},
     "visualMap":{"min":vmin,"max":vmax,"calculable":True,"orient":"horizontal","left":"center","bottom":0,
      "textStyle":{"color":"#9aa6d6"},"inRange":{"color":["#1a2140","#2c4a8a","#6c8cff","#ffb454","#ff6b8b"]}},
     "series":[{"name":name,"type":"heatmap","data":data,"label":{"show":False}}]}

DOW=['Mon','Tue','Wed','Thu','Fri','Sat','Sun']; HRS=[f'{h:02d}' for h in range(24)]
