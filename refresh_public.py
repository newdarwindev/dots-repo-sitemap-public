#!/usr/bin/env python3
"""Bounded discovery of the owner's public repositories and independent health signals."""
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

OWNER = 'newdarwindev'
API = 'https://api.github.com'

def request(url, *, method='GET'):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'dots-public-sitemap/2'}
    if os.getenv('GITHUB_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers, method=method), timeout=8) as response:
            body = response.read() if method == 'GET' else b''
            return (json.loads(body) if body else None), response.status
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 405):
            return None, exc.code
        raise
    except (TimeoutError, urllib.error.URLError):
        return None, None

def public_repos():
    repos = []
    for page in range(1, 11):
        batch, code = request(f'{API}/users/{OWNER}/repos?type=owner&per_page=100&page={page}')
        if code != 200:
            raise RuntimeError(f'public discovery failed: {code}')
        if not batch:
            break
        repos.extend(r for r in batch if r.get('owner', {}).get('login', '').lower() == OWNER and r.get('visibility') == 'public' and not r.get('private'))
        if len(batch) < 100:
            break
    else:
        raise RuntimeError('repository pagination cap reached')
    return sorted(repos, key=lambda r: r['name'].lower())

def pages_url(repo):
    page, code = request(f"{API}/repos/{repo['full_name']}/pages")
    if code != 200 or not page:
        return None, None
    url = page.get('html_url')
    parsed = urlparse(url or '')
    if parsed.scheme != 'https' or parsed.hostname != f'{OWNER}.github.io':
        return None, None
    return url, page.get('status')

def main():
    observed = datetime.now(timezone.utc).isoformat()
    result = []
    for repo in public_repos():
        name = repo['full_name']
        runs, code = request(f'{API}/repos/{name}/actions/runs?per_page=1')
        run = ((runs or {}).get('workflow_runs') or [None])[0] if code == 200 else None
        deployments, code = request(f'{API}/repos/{name}/deployments?per_page=1')
        latest = deployments[0] if code == 200 and deployments else None
        status = None
        if latest:
            statuses, code = request(f"{API}/repos/{name}/deployments/{latest['id']}/statuses?per_page=1")
            status = statuses[0] if code == 200 and statuses else None
        site, pages_state = pages_url(repo)
        http_code = request(site, method='HEAD')[1] if site else None
        result.append({'name': name, 'visibility': 'public', 'source_url': repo['html_url'], 'description': repo.get('description') or '', 'updated_at': repo.get('updated_at'), 'deployment_url': site, 'pages_status': pages_state, 'http_status': http_code, 'latest_deployment': {'state': status.get('state') if status else None, 'updated_at': status.get('updated_at') if status else None}, 'latest_workflow': {'conclusion': run.get('conclusion') if run else None, 'status': run.get('status') if run else None, 'url': run.get('html_url') if run else None, 'updated_at': run.get('updated_at') if run else None}, 'observed_at': observed})
    Path('inventory.json').write_text(json.dumps({'repositories': result, 'refreshed_at': observed, 'count': len(result)}, indent=2) + '\n')
    print(f'Public repositories discovered: {len(result)}')

if __name__ == '__main__':
    main()
