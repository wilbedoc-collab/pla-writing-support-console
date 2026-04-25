#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

STATE = Path('/Users/ahnbot/.openclaw/workspace/review_ui_v2/state')
BINDING = STATE / 'sentence_level_binding_deepevidence_v1.json'
OUT_VALIDATION = STATE / 'sentence_level_binding_validation_v1.json'
OUT_STRENGTH = STATE / 'sentence_evidence_strength_labels_v1.json'


def load(path):
    return json.loads(path.read_text())


def strength_label(paper_id, support_text):
    pid = (paper_id or '').lower()
    st = (support_text or '').lower()
    if 'bmmsc' in pid or 'bm-msc' in st or 'msc ex vivo' in st:
        return 'in_vitro'
    if 'review' in pid and 'mechanism' in st:
        return 'mechanism_review'
    if 'review' in pid:
        return 'narrative_review'
    if 'fibroblast' in st:
        return 'in_vitro'
    if 'adjacent domain niche' in st:
        return 'indirect_human'
    if 'longevity mechanism' in st:
        return 'mechanism_review'
    return 'indirect_human'


def human_present(labels):
    return any(x in ['direct_human', 'indirect_human'] for x in labels)


def validate_entry(row):
    selected = row.get('selected_evidence', [])
    reason_codes = []
    evidence_checks = []
    labels = []
    if not selected:
        return {
            'sentence_id': row['sentence_id'],
            'verdict': 'EMPTY',
            'coverage_status': 'no_evidence',
            'strongest_support_label': 'none',
            'human_support_present': False,
            'evidence_checks': [],
            'reason_codes': ['no_attachable_support', 'human_evidence_missing'],
            'better_candidate_exists': False,
        }

    same_paper_count = {}
    for ev in selected:
        pid = ev.get('paper_id')
        same_paper_count[pid] = same_paper_count.get(pid, 0) + 1

    best_score = max((ev.get('score', 0) for ev in selected), default=0)
    for ev in selected:
        pid = ev.get('paper_id')
        support = ev.get('what_it_actually_supports', '')
        score = ev.get('score', 0)
        label = strength_label(pid, support)
        labels.append(label)
        local_reasons = []
        if score >= 8:
            local_reasons.append('direct_quote_match')
        elif score >= 4:
            local_reasons.append('indirect_but_relevant')
        else:
            local_reasons.append('keyword_only_match')
        if 'mechanism' in support.lower():
            local_reasons.append('mechanism_support_only')
        if same_paper_count.get(pid, 0) > 1:
            local_reasons.append('same_paper_redundant')
        if 'entropy' in pid.lower():
            local_reasons.append('entropy_paper_outside_entropy_sentence')
        evidence_checks.append({
            'paper_id': pid,
            'score': score,
            'support_directness': label,
            'reason_codes': local_reasons,
        })
        reason_codes.extend(local_reasons)

    unique_reason_codes = sorted(set(reason_codes))
    strongest = labels[0] if labels else 'none'
    human = human_present(labels)
    verdict = 'PASS'
    coverage_status = 'covered'
    if best_score <= 0:
        verdict = 'MISBOUND'
        coverage_status = 'misbound'
        unique_reason_codes.extend(['off_topic_domain_drift'])
    elif not human or 'keyword_only_match' in unique_reason_codes or 'same_paper_redundant' in unique_reason_codes:
        verdict = 'WARN'
        coverage_status = 'weak_or_indirect'
    if row.get('support_grade') == 'complete_refutation' and verdict == 'PASS':
        verdict = 'WARN'
    return {
        'sentence_id': row['sentence_id'],
        'verdict': verdict,
        'coverage_status': coverage_status,
        'strongest_support_label': strongest,
        'human_support_present': human,
        'evidence_checks': evidence_checks,
        'reason_codes': sorted(set(unique_reason_codes)),
        'better_candidate_exists': False,
    }


def main():
    rows = load(BINDING)
    validations = []
    strength_rows = []
    for row in rows:
        v = validate_entry(row)
        validations.append(v)
        labels = [x['support_directness'] for x in v['evidence_checks']]
        strength_rows.append({
            'sentence_id': row['sentence_id'],
            'strongest_support_label': v['strongest_support_label'],
            'support_mix_profile': labels,
            'human_support_present': v['human_support_present'],
        })
    OUT_VALIDATION.write_text(json.dumps(validations, ensure_ascii=False, indent=2))
    OUT_STRENGTH.write_text(json.dumps(strength_rows, ensure_ascii=False, indent=2))
    print(str(OUT_VALIDATION))
    print(str(OUT_STRENGTH))


if __name__ == '__main__':
    main()
