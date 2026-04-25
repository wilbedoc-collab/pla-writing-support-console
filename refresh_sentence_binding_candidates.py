#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

STATE = Path('/Users/ahnbot/.openclaw/workspace/review_ui_v2/state')
BASE = STATE / 'sentence_level_binding_deepevidence_v1.json'
CANDIDATES = STATE / 'sentence_targeted_candidate_refresh_v1.json'
OUT = STATE / 'updated_sentence_level_binding_v1.json'


def load(path):
    return json.loads(path.read_text()) if path.exists() else []


def main():
    base = load(BASE)
    cands = {x['sentence_id']: x for x in load(CANDIDATES)}
    out = []
    for row in base:
        sid = row['sentence_id']
        merged = dict(row)
        merged['refresh_status'] = 'refreshed' if sid in cands else 'unchanged'
        merged['candidate_ladder'] = cands.get(sid, {}).get('candidate_ladder', [])
        out.append(merged)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(str(OUT))


if __name__ == '__main__':
    main()
