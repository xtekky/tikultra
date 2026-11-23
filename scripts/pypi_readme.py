"""Build README.pypi.md (the PyPI project page) from README.md.

PyPI cannot resolve repo-relative paths, and it freezes the page for each version. So the PyPI copy turns
repo-relative images and links into absolute github.com / raw.githubusercontent.com URLs (they load once the repo is
public), and points any tikultra.com page listed in FALLBACK at a live page. Run it before building; the release
workflow does.

  python scripts/pypi_readme.py
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://tikultra.com'
REPO = 'xtekky/tikultra'
RAW = f'https://raw.githubusercontent.com/{REPO}/main'
BLOB = f'https://github.com/{REPO}/blob/main'

# tikultra.com pages that are not live when releasing -> the closest live page, e.g. {'/some-guide': '/docs'}.
FALLBACK: dict[str, str] = {}



def fix_url(m: re.Match) -> str:
    path, rest = m.group(1) or '/', m.group(2) or ''
    path = FALLBACK.get(path.rstrip('/') or '/', path)
    rest = rest.replace('utm_source=github', 'utm_source=pypi').replace('ref=github-python', 'ref=pypi')
    return f'{SITE}{path}{rest}'


def build() -> str:
    s = (ROOT / 'README.md').read_text(encoding='utf-8')
    # Repo-relative images -> raw.githubusercontent.com, repo-relative links -> github.com.
    s = re.sub(r'(src)="(?:\./)?((?:assets|docs)/[^"]+)"', lambda m: f'{m.group(1)}="{RAW}/{m.group(2)}"', s)
    s = re.sub(r'href="\./([^"#]+)"', lambda m: f'href="{BLOB}/{m.group(1)}"', s)
    s = re.sub(r'\]\(\./([^)#]+)\)', lambda m: f']({BLOB}/{m.group(1)})', s)
    s = s.replace('ref=github-python', 'ref=pypi')
    s = re.sub(r'https://tikultra\.com(/[a-z0-9/-]*)?([?#][^\s")<>]*)?', fix_url, s)
    if re.search(r'(src|href)="(?!https?:|mailto:|#)', s) or re.search(r'\]\((?!https?:|mailto:|#)', s):
        raise SystemExit('README.pypi.md still has a relative link or image; fix README.md or this script.')
    return s


if __name__ == '__main__':
    out = ROOT / 'README.pypi.md'
    out.write_text(build(), encoding='utf-8')
    print('wrote', out.relative_to(ROOT))
