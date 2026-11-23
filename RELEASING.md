# Releasing to PyPI

Releases are automatic: publishing a GitHub release runs `.github/workflows/release.yml`, which tests, builds and
uploads the package to PyPI. No API token is stored in GitHub; PyPI trusts this repository through OIDC.

## One-time setup

1. Sign in at https://pypi.org (turn on 2FA, PyPI requires it).
2. Go to **Your account → Publishing → Add a new pending publisher** and fill in:
   - PyPI project name: `tikultra`
   - Owner: `xtekky` · Repository: `tikultra-sdk`
   - Workflow name: `release.yml` · Environment: `pypi`
3. In GitHub: **Settings → Environments → New environment → `pypi`** (optionally require your approval).

The first release creates the `tikultra` project on PyPI and turns the pending publisher into a normal one.

## Every release

```bash
# 1. bump the version in pyproject.toml and src/tikultra/__init__.py, e.g. 1.0.1
git commit -am "Release 1.0.1" && git push
# 2. publish a release whose tag matches the version
gh release create v1.0.1 --generate-notes
```

Watch it with `gh run watch`. The workflow refuses to publish if the tag and the version differ.

## The PyPI page

PyPI shows `README.pypi.md`, which `scripts/pypi_readme.py` builds from `README.md` (the release workflow runs it).
It turns repo-relative images and links into github.com URLs, which load once this repo is public. If a linked
tikultra.com page is not live when you release, add it to `FALLBACK` in that script. PyPI freezes the page for each
version, so a README fix needs a new version.
