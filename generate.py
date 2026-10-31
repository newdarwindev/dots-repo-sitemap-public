#!/usr/bin/env python3
"""Build a static repository sitemap from a curated, bounded inventory."""
import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path


def build(data, audience, now=None):
    now = now or datetime.now(timezone.utc)
    rows = []
    for repo in data['repositories']:
        if repo.get('visibility') != 'public' and audience == 'public':
            continue
        name = html.escape(repo['name'])
        source = html.escape(repo['source_url'], quote=True)
        deployment = repo.get('deployment_url')
        deploy = f'<a href="{html.escape(deployment, quote=True)}">site</a>' if deployment else 'undocumented'
        run = repo.get('latest_workflow') or {}
        observed = run.get('observed_at')
        fresh = False
        if observed:
            try:
                stamp = datetime.fromisoformat(observed.replace('Z', '+00:00'))
                fresh = 0 <= (now - stamp).total_seconds() <= 86400
            except (ValueError, TypeError):
                pass
        state = html.escape(run.get('conclusion') or 'unknown') if fresh else 'stale / unknown'
        rows.append(f'<tr><td><a href="{source}">{name}</a></td><td>{deploy}</td><td>{state}</td><td>{html.escape(observed or "unknown")}</td></tr>')
    return '<!doctype html><meta charset="utf-8"><title>Repository sitemap</title><h1>Repository sitemap</h1><p>Latest workflow status is distinct from deployment health. Status older than 24 hours is stale.</p><table><thead><tr><th>Source</th><th>Documented deployment</th><th>Latest workflow</th><th>Observed UTC</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table>'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('inventory', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--audience', choices=['public', 'private'], required=True)
    a = p.parse_args()
    data = json.loads(a.inventory.read_text())
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(build(data, a.audience))

if __name__ == '__main__':
    main()
