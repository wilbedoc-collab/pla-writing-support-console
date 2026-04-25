#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

STATE = Path('/Users/ahnbot/.openclaw/workspace/review_ui_v2/state')
VALIDATION = STATE / 'sentence_level_binding_validation_v1.json'
BINDING = STATE / 'sentence_level_binding_deepevidence_v1.json'
OUT = STATE / 'sentence_zero_evidence_salvage_v1.json'


def load(path):
    return json.loads(path.read_text())


def classify(sentence_id, binding_row, validation_row):
    text = (binding_row.get('claim_id', '') + ' ' + sentence_id).lower()
    claim_type = (binding_row.get('claim_type') or '').lower()
    if validation_row['verdict'] != 'EMPTY':
        return None
    if 'mechanism' in claim_type:
        return {
            'sentence_id': sentence_id,
            'salvage_class': 'MECHANISTIC_SALVAGE',
            'missing_facet': 'direct support missing',
            'preferred_evidence_type': 'mechanism_review_or_in_vitro',
            'rewrite_required': False,
            'next_action': 'add mechanism-grounded support',
        }
    if 'advocacy' in claim_type or 'translational' in claim_type:
        return {
            'sentence_id': sentence_id,
            'salvage_class': 'SENTENCE_WEAKEN_REQUIRED',
            'missing_facet': 'claim too strong for current support',
            'preferred_evidence_type': 'human_or_direct_support',
            'rewrite_required': True,
            'next_action': 'weaken or narrow sentence',
        }
    return {
        'sentence_id': sentence_id,
        'salvage_class': 'RETRIEVAL_RETRY',
        'missing_facet': 'attachable evidence missing',
        'preferred_evidence_type': 'direct_or_indirect_human',
        'rewrite_required': False,
        'next_action': 'retry retrieval with narrowed query',
    }


def main():
    validations = {x['sentence_id']: x for x in load(VALIDATION)}
    bindings = {x['sentence_id']: x for x in load(BINDING)}
    out = []
    for sid, v in validations.items():
        row = classify(sid, bindings.get(sid, {}), v)
        if row:
            out.append(row)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(str(OUT))


if __name__ == '__main__':
    main()
