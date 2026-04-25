#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

STATE = Path('/Users/ahnbot/.openclaw/workspace/review_ui_v2/state')
VALIDATION = STATE / 'sentence_level_binding_validation_v1.json'
SALVAGE = STATE / 'sentence_zero_evidence_salvage_v1.json'
OUT = STATE / 'sentence_rewrite_recommendations_v1.json'


def load(path):
    return json.loads(path.read_text())


def build_recommendation(validation, salvage):
    verdict = validation.get('verdict')
    reasons = validation.get('reason_codes', [])
    if verdict == 'EMPTY':
        if salvage and salvage.get('salvage_class') == 'SENTENCE_WEAKEN_REQUIRED':
            return 'soften_claim', ['no_attachable_support', 'human_evidence_missing'], '직접 주장 대신 시사적/제한적 표현으로 낮추기'
        return 'narrow_scope', ['no_attachable_support'], '주장 범위를 좁히고 필요한 근거 종류를 명시하기'
    if verdict == 'MISBOUND':
        return 'convert_to_mechanistic_statement', ['off_topic_domain_drift'], '강한 일반화 대신 기전 수준 문장으로 재정렬하기'
    if verdict == 'WARN':
        if 'same_paper_redundant' in reasons:
            return 'require_citation_split', ['same_paper_redundant'], '한 문장에 근거를 몰지 말고 문장/인용을 분리하기'
        return 'split_sentence_into_two_claims', reasons[:2], '설명과 주장 요소를 둘로 분리하기'
    return None


def main():
    validations = load(VALIDATION)
    salvage_rows = {x['sentence_id']: x for x in load(SALVAGE)} if SALVAGE.exists() else {}
    out = []
    for v in validations:
        rec = build_recommendation(v, salvage_rows.get(v['sentence_id']))
        if not rec:
            continue
        rec_type, rationale_codes, direction = rec
        out.append({
            'sentence_id': v['sentence_id'],
            'recommendation_type': rec_type,
            'rationale_codes': rationale_codes,
            'suggested_direction': direction,
        })
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(str(OUT))


if __name__ == '__main__':
    main()
