#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

STATE = Path('/Users/ahnbot/.openclaw/workspace/review_ui_v2/state')
BINDING = STATE / 'sentence_level_binding_deepevidence_v1.json'
VALIDATION = STATE / 'sentence_level_binding_validation_v1.json'
OUT = STATE / 'sentence_citation_slots_v1.json'


def load(path):
    return json.loads(path.read_text()) if path.exists() else []


def main():
    binding = {x['sentence_id']: x for x in load(BINDING)}
    validation = {x['sentence_id']: x for x in load(VALIDATION)}
    out = []
    ordered_ids = list(binding.keys())
    for i, sid in enumerate(ordered_ids):
        row = binding[sid]
        val = validation.get(sid, {})
        selected = row.get('selected_evidence', [])
        primary = selected[0]['paper_id'] if selected else None
        merge_candidates = []
        if i > 0 and primary:
            prev = binding.get(ordered_ids[i-1], {})
            prev_selected = prev.get('selected_evidence', [])
            if prev_selected and prev_selected[0]['paper_id'] == primary:
                merge_candidates.append(ordered_ids[i-1])
        out.append({
            'sentence_id': sid,
            'citation_strategy': 'no_citation_recommended_until_salvaged' if val.get('verdict') == 'EMPTY' else 'single_primary',
            'primary_citation_paper_id': primary,
            'secondary_citation_paper_ids': [x['paper_id'] for x in selected[1:3]],
            'caveat_citation_needed': val.get('verdict') == 'WARN',
            'inline_citation_count_recommendation': 0 if val.get('verdict') == 'EMPTY' else 1,
            'paragraph_merge_candidate_ids': merge_candidates,
            'citation_role': 'primary_direct_citation' if primary else 'no_citation_needed',
            'why_here': 'sentence-local primary support',
            'citation_strength': val.get('strongest_support_label', 'none'),
        })
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(str(OUT))


if __name__ == '__main__':
    main()
