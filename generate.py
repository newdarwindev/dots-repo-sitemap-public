#!/usr/bin/env python3
"""Render the repository sitemap from classified inventory data."""
import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

CSS = '''
:root{color-scheme:dark;font-family:Inter,ui-sans-serif,system-ui,sans-serif;background:#0a101b;color:#e8f0fa}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 80% -10%,#1c3760 0,transparent 34%),#0a101b}.wrap{max-width:1200px;margin:auto;padding:38px 22px 80px}header{display:flex;justify-content:space-between;align-items:flex-start;gap:20px}h1{font-size:clamp(2rem,5vw,4rem);letter-spacing:-.055em;margin:12px 0 8px}p{color:#aab9ce;line-height:1.55}.eyebrow{color:#70d6c7;font-size:.76rem;letter-spacing:.2em;text-transform:uppercase;font-weight:800}.stamp{background:#152238;border:1px solid #31445d;border-radius:30px;padding:10px 16px;color:#c9d8e8;font-size:.82rem;white-space:nowrap}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:30px 0}.stat{background:#121e31;border:1px solid #293951;border-radius:17px;padding:19px}.stat strong{font-size:1.85rem;display:block}.stat span{color:#91a6bd;font-size:.84rem}.toolbar{display:flex;justify-content:space-between;gap:15px;align-items:center;margin:34px 0 14px}input{background:#121e31;color:white;border:1px solid #40536c;border-radius:11px;padding:12px 15px;font:inherit;width:min(330px,100%)}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}.card{background:linear-gradient(145deg,#17253b,#101c2e);border:1px solid #2f425c;border-radius:20px;padding:20px;min-width:0}.top{display:flex;justify-content:space-between;gap:12px}.name{color:white;text-decoration:none;font-size:1.08rem;font-weight:750;overflow-wrap:anywhere}.name:hover{color:#70d6c7}.desc{min-height:42px;margin:12px 0 18px;font-size:.9rem}.signals{display:flex;gap:7px;flex-wrap:wrap}.pill{border-radius:30px;padding:7px 10px;background:#233047;color:#c4d2e3;font-size:.76rem;font-weight:700}.good{background:#153d37;color:#89e6c9}.bad{background:#4a2530;color:#ffb0bd}.warn{background:#4b3a22;color:#ffd390}.meta{display:flex;justify-content:space-between;margin-top:20px;padding-top:14px;border-top:1px solid #30415a;color:#91a6bd;font-size:.75rem;gap:8px}.meta a{color:#8ec8fa}.note{border-left:3px solid #70d6c7;padding-left:15px;margin-top:30px;font-size:.84rem}.empty{display:none;color:#aab9ce}@media(max-width:720px){header{display:block}.stamp{display:inline-block;margin-top:12px}.stats{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}.toolbar{display:block}.toolbar input{margin-top:9px;width:100%}}
'''

def esc(v): return html.escape(str(v if v is not None else 'unknown'))
def safe_link(url):
    p = urlparse(url or '')
    return html.escape(url, quote=True) if p.scheme == 'https' and p.hostname else None

def pill(label, value, kind=''):
    return f'<span class="pill {kind}">{esc(label)} · {esc(value)}</span>'

def build(data, audience, now=None):
    now = now or datetime.now(timezone.utc)
    repos = [r for r in data['repositories'] if audience == 'private' or r.get('visibility') == 'public']
    cards=[]
    sites=healthy=passing=0
    for r in repos:
        source=safe_link(r.get('source_url'))
        if not source: continue
        site=safe_link(r.get('deployment_url'))
        if site: sites+=1
        code=r.get('http_status')
        if code == 200: healthy+=1
        run=r.get('latest_workflow') or {}
        conclusion=run.get('conclusion') or run.get('status') or 'unknown'
        observed=r.get('observed_at') or run.get('observed_at')
        stale=True
        try:
            stale=(now-datetime.fromisoformat(observed.replace('Z','+00:00'))).total_seconds()>86400
        except (ValueError,AttributeError,TypeError): pass
        if stale: conclusion='stale / unknown'
        if conclusion == 'success': passing+=1
        deployment=(r.get('latest_deployment') or {}).get('state') or 'unknown'
        signals=pill('CI',conclusion,'good' if conclusion=='success' else 'bad' if conclusion=='failure' else 'warn') + pill('Deploy',deployment,'good' if deployment=='success' else 'warn') + pill('HTTP',code if code is not None else 'unknown','good' if code==200 else 'bad' if isinstance(code,int) and code>=400 else 'warn')
        site_html=f'<a href="{site}">Open site ↗</a>' if site else 'No verified Pages URL'
        cards.append(f'<article class="card" data-name="{esc(r["name"].lower())}"><div class="top"><a class="name" href="{source}">{esc(r["name"])}</a></div><p class="desc">{esc(r.get("description") or "Public source repository")}</p><div class="signals">{signals}</div><div class="meta"><span>{site_html}</span><span>Checked {esc(observed or "unknown")}</span></div></article>')
    count=len(cards)
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Repository constellation</title><style>{CSS}</style><main class="wrap"><header><div><div class="eyebrow">New Darwin · public systems</div><h1>Repository constellation</h1><p>Source, build and deployment signals across the public fleet.</p></div><div class="stamp">Observed {esc(data.get('refreshed_at') or 'unknown')}</div></header><section class="stats"><div class="stat"><strong>{count}</strong><span>Public repositories</span></div><div class="stat"><strong>{sites}</strong><span>Pages sites</span></div><div class="stat"><strong>{passing}</strong><span>Passing latest CI</span></div><div class="stat"><strong>{healthy}</strong><span>HTTP 200 sites</span></div></section><div class="toolbar"><div><div class="eyebrow">Live inventory</div><p>Search the source map</p></div><input id="q" type="search" placeholder="Filter repositories" aria-label="Filter repositories"></div><section class="grid" id="grid">{''.join(cards)}</section><p class="empty" id="empty">No repositories match.</p><p class="note">CI, GitHub deployment state and HTTP reachability are separate observations. Unknown means unavailable, not healthy. A site returning HTTP 200 does not prove app functionality. Public repositories only.</p></main><script>const q=document.querySelector('#q'), cards=[...document.querySelectorAll('.card')],empty=document.querySelector('#empty');q.addEventListener('input',()=>{{let n=0;for(const card of cards){{const show=card.dataset.name.includes(q.value.toLowerCase());card.hidden=!show;if(show)n++}}empty.style.display=n?'none':'block'}});</script></html>'''

def main():
    p=argparse.ArgumentParser();p.add_argument('inventory',type=Path);p.add_argument('output',type=Path);p.add_argument('--audience',choices=['public','private'],required=True);a=p.parse_args();data=json.loads(a.inventory.read_text());a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(build(data,a.audience))
if __name__=='__main__':main()
