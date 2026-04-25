#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

STATE = Path('/Users/ahnbot/.openclaw/workspace/review_ui_v2/state')
VALIDATION = STATE / 'sentence_level_binding_validation_v1.json'
BINDING = STATE / 'sentence_level_binding_deepevidence_v1.json'
SALVAGE = STATE / 'sentence_zero_evidence_salvage_v1.json'
OUT = STATE / 'sentence_targeted_deepening_v1.json'


def load(path):
    return json.loads(path.read_text())


def choose_mode(validation, salvage):
    if salvage and salvage.get('salvage_class') == 'MECHANISTIC_SALVAGE':
        return 'stronger_mechanism_first'
    if validation.get('human_support_present') is False:
        return 'stronger_human_first'
    if 'same_paper_redundant' in validation.get('reason_codes', []):
        return 'diversify_same_paper_overuse'
    return 'sharpen_logic'


def main():
    validations = {x['sentence_id']: x for x in load(VALIDATION)}
    bindings = {x['sentence_id']: x for x in load(BINDING)}
    salvage_rows = {x['sentence_id']: x for x in load(SALVAGE)} if SALVAGE.exists() else {}
    out = []
    for sid, binding in bindings.items():
        validation = validations.get(sid, {})
        salvage = salvage_rows.get(sid)
        out.append({
            'sentence_id': sid,
            'mode': choose_mode(validation, salvage),
            'current_binding_summary': {
                'selected_count': binding.get('selected_count', 0),
                'support_grade': binding.get('support_grade', 'none'),
            },
            'weakness_profile': validation.get('reason_codes', []),
            'deepening_targets': salvage.get('missing_facet', 'fit/coverage') if salvage else 'fit/coverage',
            'recommended_candidates': [x.get('paper_id') for x in binding.get('selected_evidence', [])],
        })
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(str(OUT))


if __name__ == '__main__':
    main()
