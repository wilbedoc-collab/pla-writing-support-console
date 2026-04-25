#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import time
from pathlib import Path

STATE = Path('/Users/ahnbot/.openclaw/workspace/review_ui_v2/state')
JOBS = STATE / 'refresh_jobs_status.json'
STAGES = ['queued','building_queries','searching','screening_candidates','checking_fulltext','extracting_passages','refreshing_binding','completed']


def load_jobs():
    return json.loads(JOBS.read_text()) if JOBS.exists() else []


def save_jobs(rows):
    JOBS.write_text(json.dumps(rows, ensure_ascii=False, indent=2))


def upsert_job(sentence_id, job_status='queued', fail_reason=None, retry_action=None):
    rows = load_jobs()
    now = int(time.time())
    found = False
    for row in rows:
        if row.get('sentence_id') == sentence_id:
            row['job_status'] = job_status
            row['updated_at'] = now
            row['fail_reason'] = fail_reason
            row['retry_action'] = retry_action
            row.setdefault('progress', [])
            if job_status not in row['progress']:
                row['progress'].append(job_status)
            found = True
            break
    if not found:
        rows.append({
            'sentence_id': sentence_id,
            'job_status': job_status,
            'progress': [job_status],
            'updated_at': now,
            'fail_reason': fail_reason,
            'retry_action': retry_action,
        })
    save_jobs(rows)
    return rows
