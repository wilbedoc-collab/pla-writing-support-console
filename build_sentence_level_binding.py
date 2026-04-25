#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

ROOT = Path('/Users/ahnbot/.openclaw/workspace/thesis_foundry/35_deepevidence_fulltext_acquisition_and_reading_v1')
OUT = Path('/Users/ahnbot/.openclaw/workspace/review_ui_v2/state/sentence_level_binding_deepevidence_v1.json')


def load(path):
    return json.loads(path.read_text())


def norm(text):
    text = ' '.join(str(text or '').split()).lower()
    for ch in '.,;:!?()[]{}*"\'':
        text = text.replace(ch, ' ')
    return text


def tokens(text):
    return {t for t in norm(text).split() if len(t) >= 2}


def score(sentence_text, passage):
    st = tokens(sentence_text)
    support = tokens(passage.get('what_it_actually_supports', ''))
    quote = tokens(passage.get('key_passage_text', ''))
    paper = tokens(passage.get('paper_id', ''))
    s = len(st & support) * 4 + len(st & quote) * 2 + len(st & paper)
    sl = norm(sentence_text)
    pid = passage.get('paper_id', '').lower()
    support_text = norm(passage.get('what_it_actually_supports', ''))
    if 'entropy' in pid and '엔트로피' not in sl and 'entropy' not in sl:
        s -= 8
    if 'integrin' in pid and ('인테그린' in sl or 'integrin' in sl):
        s += 6
    if ('msc' in pid or 'msc' in support_text) and ('msc' in sl or '중간엽' in sl or '줄기세포' in sl):
        s += 6
    if 'niche' in support_text and ('niche' in sl or '니치' in sl or '줄기세포' in sl):
        s += 5
    if ('fibroblast' in support_text or 'fibroblast' in pid) and ('섬유아세포' in sl or 'fibroblast' in sl or '콜라겐' in sl):
        s += 5
    if 'matreotype' in sl and ('matreotype' in pid or 'longevity' in pid or 'foxo' in pid):
        s += 5
    return s


def main():
    queue = load(ROOT / '02_claim_queue' / 'claim_followup_queue.json')
    bindings = load(ROOT / '09_evidence_interpretation' / 'claim_evidence_binding.json')
    passages = load(ROOT / '08_fulltext_read' / 'fulltext_key_passage_bank.json')

    by_claim = {x['claim_id']: x for x in bindings}
    by_pid = {x['passage_id']: x for x in passages}
    out = []

    for row in queue:
        claim_id = row['claim_id']
        sentence_id = row['sentence_id']
        sentence_text = row['claim_text']
        binding = by_claim.get(claim_id, {})
        passage_ids = binding.get('supporting_passage_ids', [])
        candidate_passages = [by_pid[pid] for pid in passage_ids if pid in by_pid]
        scored = []
        seen = set()
        for passage in candidate_passages:
            sc = score(sentence_text, passage)
            key = (passage.get('paper_id'), passage.get('what_it_actually_supports'))
            if key in seen:
                continue
            seen.add(key)
            scored.append({
                'score': sc,
                'paper_id': passage.get('paper_id'),
                'passage_id': passage.get('passage_id'),
                'support_or_limit': passage.get('support_or_limit'),
                'what_it_actually_supports': passage.get('what_it_actually_supports'),
                'what_it_does_not_support': passage.get('what_it_does_not_support'),
                'key_passage_text': passage.get('key_passage_text'),
                'claim_ceiling_note': passage.get('claim_ceiling_note'),
                'population_or_context': passage.get('population_or_context'),
            })
        scored.sort(key=lambda x: x['score'], reverse=True)
        selected = [x for x in scored if x['score'] > 0][:4]
        out.append({
            'sentence_id': sentence_id,
            'claim_id': claim_id,
            'claim_type': row.get('claim_type'),
            'risk_level': row.get('risk_level'),
            'support_grade': binding.get('support_grade', 'none'),
            'selected_evidence': selected,
            'selected_count': len(selected),
            'unselected_count': max(0, len(scored) - len(selected)),
        })

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(str(OUT))


if __name__ == '__main__':
    main()
