#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import time
from pathlib import Path

STATE = Path('/Users/ahnbot/.openclaw/workspace/review_ui_v2/state')
BINDING = STATE / 'sentence_level_binding_deepevidence_v1.json'
OUT = STATE / 'console_state_index.json'


def load(path):
    return json.loads(path.read_text()) if path.exists() else []


def ts(path):
    return int(path.stat().st_mtime) if path.exists() else 0


def main():
    binding = load(BINDING)
    now = int(time.time())
    out = []
    for row in binding:
        sid = row['sentence_id']
        out.append({
            'sentence_id': sid,
            'evidence_last_updated': ts(STATE / 'updated_sentence_level_binding_v1.json'),
            'rewrite_last_updated': ts(STATE / 'recommended_sentence_options_v1.json'),
            'citation_last_updated': ts(STATE / 'sentence_citation_slots_v1.json'),
            'transition_last_updated': ts(STATE / 'sentence_transition_validation_v1.json'),
            'feedback_last_updated': ts(STATE / 'validator_feedback_tuning_v1.json'),
            'stale_flags': {
                'rewrite': False,
                'citation': False,
                'transition': False,
                'feedback': False,
            }
        })
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(str(OUT))


if __name__ == '__main__':
    main()
