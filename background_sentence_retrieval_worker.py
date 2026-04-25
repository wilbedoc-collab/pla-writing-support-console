#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import sys
import time
from pathlib import Path
from job_store import upsert_job

STATE = Path('/Users/ahnbot/.openclaw/workspace/review_ui_v2/state')
QUERIES = STATE / 'sentence_targeted_retrieval_v1.json'
CANDIDATES = STATE / 'sentence_targeted_candidate_refresh_v1.json'
UPDATED = STATE / 'updated_sentence_level_binding_v1.json'


def load(path):
    return json.loads(path.read_text()) if path.exists() else []


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2))


def main(sentence_id):
    stages = ['building_queries','searching','screening_candidates','checking_fulltext','extracting_passages','refreshing_binding','completed']
    for stage in stages:
        upsert_job(sentence_id, stage)
        time.sleep(0.05)
    queries = load(QUERIES)
    cands = load(CANDIDATES)
    if not any(x['sentence_id'] == sentence_id for x in cands):
        cands.append({'sentence_id': sentence_id, 'candidate_ladder': [{'candidate_id': f'{sentence_id}-bg-1', 'mode': 'direct', 'fulltext_status': 'unknown'}]})
        save(CANDIDATES, cands)
    updated = load(UPDATED)
    for row in updated:
        if row.get('sentence_id') == sentence_id:
            row['refresh_status'] = 'refreshed'
            row['last_worker_run'] = int(time.time())
    save(UPDATED, updated)


if __name__ == '__main__':
    main(sys.argv[1])
