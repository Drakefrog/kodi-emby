#!/usr/bin/env python3
"""Fetch upstream tips and write an auditable sync report; never merges content."""
import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'upstreams.json').read_text()); changed=[]
for name, upstream in data.items():
    tip=subprocess.check_output(['git','ls-remote',upstream['url'],f"refs/heads/{upstream['branch']}"]).decode().split()[0]
    if not tip.startswith(upstream['commit']): changed.append((name,upstream['commit'],tip))
(ROOT/'UPSTREAM_SYNC_REPORT.md').write_text('# Upstream sync report\n\n'+('No updates.\n' if not changed else '\n'.join(f'- {n}: `{old}` → `{new}`' for n,old,new in changed)+'\n'))
if changed:
    raise SystemExit(10)
