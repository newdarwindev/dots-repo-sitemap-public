# Public repository constellation

A daily GitHub Actions job paginates the public repository list of `newdarwindev` and builds a responsive static sitemap. It records source metadata, the latest Actions run, the latest GitHub deployment status, a verified GitHub Pages URL and an HTTP HEAD result. These are independent signals; HTTP 200 does not prove app functionality. Observations older than 24 hours display stale.

Discovery uses `GET /users/newdarwindev/repos`, caps at ten pages, filters `visibility=public`, and refuses to publish private repositories. It uses the workflow's ordinary `GITHUB_TOKEN` for public API reads. No private source, Slack prompt or account spending data enters this site.

Run locally:

```sh
GITHUB_TOKEN=... python3 refresh_public.py
python3 generate.py inventory.json site/index.html --audience public
python3 -m unittest discover -s tests
```
