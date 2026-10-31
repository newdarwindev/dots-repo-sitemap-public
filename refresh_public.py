#!/usr/bin/env python3
"""Refresh only explicitly allowlisted public repository workflow metadata."""
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ALLOWED = ['newdarwindev/dots-workflow-refinery-demo', 'newdarwindev/dots-dspy-refinery-architecture']

def get_json(url):
    req = urllib.request.Request(url, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'dots-sitemap/1'})
    token = os.getenv('GITHUB_TOKEN')
    if token:
        req.add_header('Authorization', 'Bearer ' + token)
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.load(response)

def main():
    repos = []
    for name in ALLOWED:
        repo = get_json(f'https://api.github.com/repos/{name}')
        if repo.get('private') or repo.get('visibility') != 'public':
            raise RuntimeError('non-public repository in public allowlist')
        runs = get_json(f'https://api.github.com/repos/{name}/actions/runs?per_page=1')
        latest = (runs.get('workflow_runs') or [None])[0]
        repos.append({'name': name, 'visibility': 'public', 'source_url': repo['html_url'], 'deployment_url': repo.get('homepage') or None, 'latest_workflow': {'conclusion': latest.get('conclusion') if latest else None, 'observed_at': datetime.now(timezone.utc).isoformat()}})
    Path('inventory.json').write_text(json.dumps({'repositories': repos}, indent=2) + '\n')

if __name__ == '__main__':
    main()
