#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

STATE = Path('/Users/ahnbot/.openclaw/workspace/review_ui_v2/state')
VALIDATION = STATE / 'sentence_level_binding_validation_v1.json'
OUT = STATE / 'sentence_transition_validation_v1.json'


def load(path):
    return json.loads(path.read_text()) if path.exists() else []


def main():
    rows = load(VALIDATION)
    out = []
    for i, row in enumerate(rows):
        sid = row['sentence_id']
        prev_id = rows[i-1]['sentence_id'] if i > 0 else None
        next_id = rows[i+1]['sentence_id'] if i+1 < len(rows) else None
        verdict = 'PASS'
        issue_type = None
        if row['verdict'] == 'EMPTY':
            verdict = 'FLOW_BREAK'
            issue_type = 'missing_bridge'
        elif row['verdict'] == 'WARN':
            verdict = 'WARN'
            issue_type = 'unsupported_escalation'
        out.append({
            'sentence_id': sid,
            'previous_valid_sentence': prev_id,
            'current_target_sentence': sid,
            'next_valid_sentence': next_id,
            'transition_verdict': verdict,
            'issue_type': issue_type,
            'recommendation': 'check local sentence flow',
        })
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(str(OUT))


if __name__ == '__main__':
    main()
