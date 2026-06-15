#!/usr/bin/env python3
"""
resolve_paper_hint.py — minimal CLI wrapper around resolver_hints.py.

Examples:
  python3 scripts/resolve_paper_hint.py title "Attention Is All You Need"
  python3 scripts/resolve_paper_hint.py repo https://github.com/google-research/bert
  python3 scripts/resolve_paper_hint.py arxiv 2503.08102
  python3 scripts/resolve_paper_hint.py any "bert" --input-kind paper_title
"""

import os
import sys

# Allow running this script directly from anywhere
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from resolver_hints import _cli  # noqa: E402

if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
