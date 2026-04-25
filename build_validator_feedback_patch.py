#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from collections import Counter
from pathlib import Path

STATE = Path('/Users/ahnbot/.openclaw/workspace/review_ui_v2/state')
OVERRIDES = STATE / 'sentence_overrides.json'
OUT1 = STATE / 'validator_feedback_tuning_v1.json'
OUT2 = STATE / 'scoring_patch_suggestions_v1.json'

NEGATIVE = {'틀림', '과민판정', '버려라', '근거약함'}


def load(path):
    return json.loads(path.read_text()) if path.exists() else {'by_document': {}}


def main():
    data = load(OVERRIDES)
    flat = []
    for doc_id, rows in data.get('by_document', {}).items():
        for sid, payload in rows.items():
            flat.append({'sentence_id': sid, 'feedback_button': payload.get('verdict'), 'reason_tag': payload.get('reason_tag')})
    reason_counter = Counter(x.get('reason_tag') for x in flat if x.get('reason_tag'))
    patches = []
    for reason, count in reason_counter.items():
        if count >= 2:
            patches.append({'reason_tag': reason, 'count': count, 'suggested_patch': 'review validator scoring for repeated human feedback'})
    OUT1.write_text(json.dumps(flat, ensure_ascii=False, indent=2))
    OUT2.write_text(json.dumps(patches, ensure_ascii=False, indent=2))
    print(str(OUT1))
    print(str(OUT2))


if __name__ == '__main__':
    main()
