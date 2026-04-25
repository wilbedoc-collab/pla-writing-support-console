#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

STATE = Path('/Users/ahnbot/.openclaw/workspace/review_ui_v2/state')
VALIDATION = STATE / 'sentence_level_binding_validation_v1.json'
BINDING = STATE / 'sentence_level_binding_deepevidence_v1.json'
SALVAGE = STATE / 'sentence_zero_evidence_salvage_v1.json'
OUT = STATE / 'sentence_targeted_retrieval_v1.json'


def load(path):
    return json.loads(path.read_text()) if path.exists() else []


def main():
    validations = {x['sentence_id']: x for x in load(VALIDATION)}
    bindings = {x['sentence_id']: x for x in load(BINDING)}
    salvage = {x['sentence_id']: x for x in load(SALVAGE)}
    out = []
    for sid, row in bindings.items():
        v = validations.get(sid, {})
        s = salvage.get(sid, {})
        query_modes = ['direct', 'mechanism', 'proxy', 'caveat', 'counter']
        out.append({
            'sentence_id': sid,
            'validator_verdict': v.get('verdict'),
            'reason_codes': v.get('reason_codes', []),
            'salvage_class': s.get('salvage_class'),
            'weakness_profile': v.get('reason_codes', []),
            'query_modes': query_modes,
            'queries': [f"{sid}::{mode}" for mode in query_modes],
        })
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(str(OUT))


if __name__ == '__main__':
    main()
