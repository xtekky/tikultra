"""`python -m tikultra`: version, key check and where to get a free API key."""
from __future__ import annotations

import os
import sys

from . import __version__

SIGNUP = 'https://tikultra.com/signup?ref=pypi'
V, G, D, B, R = '\033[38;5;141m', '\033[38;5;84m', '\033[2m', '\033[1m', '\033[0m'


def main() -> int:
    color = sys.stdout.isatty() and os.environ.get('NO_COLOR') is None
    v, g, d, b, r = (V, G, D, B, R) if color else ('', '', '', '', '')
    key = (os.environ.get('TIKULTRA_KEY') or os.environ.get('TIKULTRA_API_KEY') or '').strip()
    print(f"""
  {v}{b}tikultra{r} {d}v{__version__}{r}  TikTok API: data, TikTok Shop, LIVE, managed accounts, X-Argus signing
""")
    if key:
        print(f"  {g}✓{r} API key found in TIKULTRA_KEY ({key[:7]}…)\n")
    else:
        print(f"  {b}Get your free API key{r} (500 requests, no card):\n  {v}{SIGNUP}{r}\n")
        print(f"  {d}then: export TIKULTRA_KEY=tu_live_...{r}\n")
    print(f"""  {d}Quickstart{r}
    from tikultra import TikUltra
    client = TikUltra()
    print(client.user.profile("tiktok")["user"]["follower_count"])

  {d}Docs{r}  https://tikultra.com/docs/python-sdk
""")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
