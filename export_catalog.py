#!/usr/bin/env python3
"""Export a public-only catalog suitable for a separate Homarr import workflow."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

def export(data, audience):
    items=[]
    for r in data['repositories']:
        if audience=='public' and r.get('visibility')!='public': continue
        url=r.get('deployment_url')
        parsed=urlparse(url or '')
        if parsed.scheme!='https' or not parsed.hostname: url=None
        items.append({'id':r['name'],'title':r['name'].split('/')[-1],'source_url':r['source_url'],'site_url':url,'visibility':r.get('visibility'),'http_status':r.get('http_status'),'ci_conclusion':(r.get('latest_workflow') or {}).get('conclusion'),'deployment_state':(r.get('latest_deployment') or {}).get('state'),'observed_at':r.get('observed_at')})
    return {'classification':audience,'items':items,'count':len(items)}
def main():
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('output',type=Path);p.add_argument('--audience',choices=['public','private'],required=True);a=p.parse_args();a.output.write_text(json.dumps(export(json.loads(a.input.read_text()),a.audience),indent=2)+'\n')
if __name__=='__main__':main()
