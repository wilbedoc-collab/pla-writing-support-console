#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

STATE = Path('/Users/ahnbot/.openclaw/workspace/review_ui_v2/state')
REWRITE = STATE / 'sentence_rewrite_recommendations_v1.json'
OUT1 = STATE / 'sentence_rewrite_options_v1.json'
OUT2 = STATE / 'recommended_sentence_options_v1.json'

TEMPLATES = {
    'soften_claim': '가능성을 시사하는 수준으로 표현을 낮춘 버전',
    'narrow_scope': '범위를 좁혀 근거 상한 안에 맞춘 버전',
    'convert_to_mechanistic_statement': '기전 수준 설명으로 바꾼 버전',
    'require_citation_split': '한 문장을 둘로 나누고 citation도 분리하는 버전',
    'split_sentence_into_two_claims': '설명과 주장 요소를 두 문장으로 나눈 버전',
}


def load(path):
    return json.loads(path.read_text()) if path.exists() else []


def main():
    rows = load(REWRITE)
    out = []
    for row in rows:
        rec = row['recommendation_type']
        out.append({
            'sentence_id': row['sentence_id'],
            'current_sentence': '',
            'option_type': rec,
            'rewritten_candidate': TEMPLATES.get(rec, 'no_change'),
            'rewrite_intent': rec,
            'support_assumption': 'bounded_by_validator_ceiling',
            'linked_papers': [],
            'key_passages': [],
            'ceiling_note': 'do not exceed current evidence ceiling',
            'risk_note': 'suggestion only',
            'why_this_wording': row.get('suggested_direction', ''),
            'generation_mode': 'pregenerated',
        })
    OUT1.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    OUT2.write_text(json.dumps(out[:], ensure_ascii=False, indent=2))
    print(str(OUT1))
    print(str(OUT2))


if __name__ == '__main__':
    main()
