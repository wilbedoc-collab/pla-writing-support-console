#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import subprocess
import time
from pathlib import Path
from job_store import upsert_job

STATE = Path('/Users/ahnbot/.openclaw/workspace/review_ui_v2/state')
QUERIES = STATE / 'sentence_targeted_retrieval_v1.json'
JOBS = STATE / 'refresh_jobs_status.json'
CANDIDATES = STATE / 'sentence_targeted_candidate_refresh_v1.json'

STAGES = [
    'queued', 'building_queries', 'searching', 'screening_candidates',
    'checking_fulltext', 'extracting_passages', 'refreshing_binding', 'completed'
]


def load(path):
    return json.loads(path.read_text()) if path.exists() else []


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2))


def main(sentence_id=None):
    rows = load(QUERIES)
    rows = [r for r in rows if sentence_id is None or r['sentence_id'] == sentence_id]
    jobs = []
    candidates = []
    now = int(time.time())
    for row in rows:
        sid = row['sentence_id']
        upsert_job(sid, 'queued')
        jobs.append({'sentence_id': sid, 'job_status': 'queued', 'progress': ['queued'], 'updated_at': now, 'retry_action': None})
        candidates.append({
            'sentence_id': sid,
            'candidate_ladder': [
                {'candidate_id': f'{sid}-cand-1', 'mode': 'direct', 'fulltext_status': 'unknown'},
                {'candidate_id': f'{sid}-cand-2', 'mode': 'mechanism', 'fulltext_status': 'unknown'},
            ]
        })
        subprocess.Popen(['/usr/bin/python3', '/Users/ahnbot/.openclaw/workspace/review_ui_v2/background_sentence_retrieval_worker.py', sid])
    save(JOBS, jobs)
    save(CANDIDATES, candidates)
    print(str(JOBS))
    print(str(CANDIDATES))


if __name__ == '__main__':
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else None)
