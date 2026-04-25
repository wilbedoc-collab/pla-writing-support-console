#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / 'public'
STATE = ROOT / 'state'
DATA_ROOT = Path('/Users/ahnbot/.openclaw/workspace/thesis_foundry')
DOCS = {
    'deepevidence-v1': DATA_ROOT / '35_deepevidence_fulltext_acquisition_and_reading_v1',
    'followup-v1': DATA_ROOT / '34_hypothesis_claim_deepevidence_followup_v1',
}
STATE.mkdir(parents=True, exist_ok=True)
SESSION_FILE = STATE / 'user_session_state.json'
OVERRIDES_FILE = STATE / 'sentence_overrides.json'
PAPER_METADATA_FILE = STATE / 'paper_metadata_overrides.json'
SENTENCE_BINDING_FILE = STATE / 'sentence_level_binding_deepevidence_v1.json'
VALIDATION_FILE = STATE / 'sentence_level_binding_validation_v1.json'
SALVAGE_FILE = STATE / 'sentence_zero_evidence_salvage_v1.json'
DEEPENING_FILE = STATE / 'sentence_targeted_deepening_v1.json'
REWRITE_FILE = STATE / 'sentence_rewrite_recommendations_v1.json'
STRENGTH_FILE = STATE / 'sentence_evidence_strength_labels_v1.json'
REFRESH_JOBS_FILE = STATE / 'refresh_jobs_status.json'
REWRITE_OPTIONS_FILE = STATE / 'recommended_sentence_options_v1.json'
TRANSITION_FILE = STATE / 'sentence_transition_validation_v1.json'
CITATION_FILE = STATE / 'sentence_citation_slots_v1.json'
CONSOLE_STATE_FILE = STATE / 'console_state_index.json'


def load_json(path, default=None):
    if not path.exists():
        return default if default is not None else {}
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def load_overrides():
    return load_json(OVERRIDES_FILE, {'by_document': {}})


def save_override(doc_id, sentence_id, verdict):
    data = load_overrides()
    data.setdefault('by_document', {})
    data['by_document'].setdefault(doc_id, {})
    data['by_document'][doc_id][sentence_id] = {
        'verdict': verdict,
        'updated_at': int(time.time()),
    }
    save_json(OVERRIDES_FILE, data)
    return data['by_document'][doc_id][sentence_id]


def next_fractional_order(existing_keys, base_value):
    if not existing_keys:
        return base_value + 0.5
    return max(existing_keys) + 0.25


def load_paper_metadata():
    return load_json(PAPER_METADATA_FILE, {})


def load_sentence_level_binding():
    rows = load_json(SENTENCE_BINDING_FILE, [])
    return {row.get('sentence_id'): row for row in rows}


def load_rows_by_sentence(path):
    rows = load_json(path, [])
    return {row.get('sentence_id'): row for row in rows}


def tokenize_koreanish(text):
    raw = normalize_sentence_text(text).lower()
    for ch in '.,;:!?()[]{}*"\'':
        raw = raw.replace(ch, ' ')
    return {tok for tok in raw.split() if len(tok) >= 2}


def score_passage_for_sentence(sentence_text, passage):
    sentence_tokens = tokenize_koreanish(sentence_text)
    support_tokens = tokenize_koreanish(passage.get('what_it_actually_supports', ''))
    passage_tokens = tokenize_koreanish(passage.get('key_passage_text', ''))
    paper_tokens = tokenize_koreanish(passage.get('paper_id', ''))
    overlap = len(sentence_tokens & support_tokens) * 4
    overlap += len(sentence_tokens & passage_tokens) * 2
    overlap += len(sentence_tokens & paper_tokens)

    sentence_lower = normalize_sentence_text(sentence_text).lower()
    support_lower = normalize_sentence_text(passage.get('what_it_actually_supports', '')).lower()
    if 'bm-msc' in support_lower or 'msc' in support_lower:
        if 'msc' in sentence_lower or 'bm-msc' in sentence_lower or '중간엽' in sentence_lower or '줄기세포' in sentence_lower:
            overlap += 5
        else:
            overlap -= 4
    if 'niche' in support_lower:
        if 'niche' in sentence_lower or '니치' in sentence_lower or '줄기세포' in sentence_lower:
            overlap += 4
        else:
            overlap -= 3
    if 'dermal fibroblast' in support_lower or 'fibroblast' in support_lower:
        if '섬유아세포' in sentence_lower or 'fibroblast' in sentence_lower or '콜라겐' in sentence_lower:
            overlap += 4
    if 'entropy' in passage.get('paper_id', '').lower() and '엔트로피' not in sentence_lower and 'entropy' not in sentence_lower:
        overlap -= 6
    if 'integrin' in passage.get('paper_id', '').lower() and '인테그린' in sentence_lower:
        overlap += 5
    if 'foxo' in passage.get('paper_id', '').lower() and ('foxo' in sentence_lower or 'nrf2' in sentence_lower or '장수' in sentence_lower):
        overlap += 5
    return overlap


def select_sentence_local_passages(sentence_text, items, max_items=4):
    scored = []
    for item in items:
        score = score_passage_for_sentence(sentence_text, item)
        scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    deduped = []
    seen = set()
    for score, item in scored:
        key = (item.get('paper_id'), item.get('what_it_actually_supports'))
        if key in seen:
            continue
        seen.add(key)
        deduped.append((score, item))
    positive = [item for score, item in deduped if score > 0]
    if positive:
        return positive[:max_items]
    return [item for _, item in deduped[:min(max_items, len(deduped))]]


def normalize_sentence_text(text):
    return ' '.join(str(text or '').split())


def should_merge_with_previous(prev_text, curr_text):
    prev = normalize_sentence_text(prev_text)
    curr = normalize_sentence_text(curr_text)
    if not prev or not curr:
        return False
    if len(curr) <= 2:
        return True
    if len(curr.split()) == 1 and not any(ch in curr for ch in '.!?:;'):
        return True
    if len(curr.split()) <= 3 and not any(ch in curr for ch in '.!?') and any(ch.isalpha() for ch in curr):
        return True
    if prev.endswith('보다'):
        return True
    if prev.endswith('여성보다'):
        return True
    if prev.endswith('무결한 피브릴보다'):
        return True
    if prev.endswith(':'):
        return True
    return False


def is_outline_like(text):
    stripped = normalize_sentence_text(text)
    if not stripped:
        return False
    outline_markers = ['구분', '주요 성분', '기능적 특성', '위치', '핵심 성분']
    marker_hits = sum(1 for marker in outline_markers if marker in stripped)
    if marker_hits >= 2 and '.' not in stripped and '입니다' not in stripped and '합니다' not in stripped:
        return True
    if '위치' in stripped and '핵심 성분' in stripped and '기능적 특성' in stripped:
        return True
    if '사이의 경계부' in stripped and 'Interstitial space' in stripped and 'Laminin' in stripped:
        return True
    if len(stripped.split()) >= 10 and stripped.count('(') >= 2 and stripped.count(')') >= 2 and '.' not in stripped:
        return True
    return False


def merge_sentence_items(items):
    merged = []
    for item in items:
        current = dict(item)
        current['text'] = normalize_sentence_text(current.get('text', ''))
        if not current['text']:
            continue
        if merged and should_merge_with_previous(merged[-1].get('text', ''), current['text']):
            merged[-1]['text'] = (merged[-1]['text'] + ' ' + current['text']).strip()
            continue
        merged.append(current)
    return merged


def cleanup_sentence_tail(text):
    stripped = normalize_sentence_text(text)
    for tail in [' [표] ECM의 주요', ' 주요']:
        if stripped.endswith(tail):
            stripped = stripped[:-len(tail)].rstrip()
    for tail in [' 1.', ' 2.', ' 3.', ' 4.', ' 5.']:
        if stripped.endswith(tail):
            stripped = stripped[:-len(tail)].rstrip()
    return stripped


SECTION_PREFIXES = [
    '강의 도입:',
    '노화에 따른 ECM의 구조적 퇴화와 기능적 손실',
    '최종당화산물(AGEs)과 기질의 기계적 경직화',
    '기질 파편화의 악순환과 DDR 수용체의 오작동',
    '장기별 ECM 변성과 성별에 따른 차이(Sexual Dimorphism)',
    '실험 데이터 분석: BM-MSCs의 접착 표현형 변화와 전략적 함의',
    '분자적 기전: 인테그린 신호 전달과 기계적 항상성의 붕괴',
    '인테그린 수용체 발현 및 성숙의 지연',
    '배양 기간에 따른 단백질별 접착 친화도 분석',
    '대조군(MG-63)과의 비교 분석 및 전략적 통찰',
    '양방향 신호 전달과 어댑터 단백질의 결함',
    '미래 전략: 마트레오타입(Matreotype) 기반의 장수 중재 전략',
    '마트레오타입(Matreotype): 진단과 치료의 서명(Signature)',
    '장수 중재법의 공통 분모: ECM 항상성 유지',
    '결론: 재생의학의 새로운 지평',
]


def cleanup_sentence_prefix(text):
    stripped = normalize_sentence_text(text)
    for prefix in ['[핵심 제언]']:
        if stripped.startswith(prefix):
            stripped = stripped[len(prefix):].strip()
    for prefix in SECTION_PREFIXES:
        if stripped.startswith(prefix + ' '):
            return stripped[len(prefix):].strip()
    return stripped


def build_doc_index(doc_root):
    sentence_index = load_json(doc_root / '01_preprocess_argument' / 'sentence_index.json', load_json(doc_root / '01_followup_structure' / 'sentence_index.json', {'items': []}))
    queue = load_json(doc_root / '02_claim_queue' / 'claim_followup_queue.json', load_json(doc_root / '02_followup_claims' / 'claim_followup_queue.json', []))
    strategies = load_json(doc_root / '03_strategy' / 'followup_strategy_map.json', load_json(doc_root / '03_followup_strategy' / 'followup_strategy_map.json', []))
    bindings = load_json(doc_root / '09_evidence_interpretation' / 'claim_evidence_binding.json', load_json(doc_root / '08_claim_binding' / 'claim_evidence_binding.json', []))
    suggestions = load_json(doc_root / '10_local_suggestions' / 'local_reinforcement_suggestions.json', load_json(doc_root / '09_local_suggestions' / 'local_reinforcement_suggestions.json', []))
    passages = load_json(doc_root / '08_fulltext_read' / 'fulltext_key_passage_bank.json', load_json(doc_root / '07_fulltext_read' / 'fulltext_key_passage_bank.json', []))
    pending = load_json(doc_root / '06_fulltext_acquisition' / 'pending_fulltext_queue.json', [])
    unavailable = load_json(doc_root / '07_unavailable_fulltext' / 'unavailable_fulltext_list.json', [])
    status = load_json(doc_root / 'status_decision.json', load_json(doc_root / 'keep_or_review_decision.json', {'status': 'WARN'}))

    sentence_items = []
    for item in merge_sentence_items(sentence_index.get('items', [])):
        cleaned = dict(item)
        cleaned['text'] = cleanup_sentence_tail(cleanup_sentence_prefix(cleaned.get('text', '')))
        if not cleaned['text']:
            continue
        if is_outline_like(cleaned['text']):
            continue
        sentence_items.append(cleaned)
    queue_by_sentence = {x['sentence_id']: x for x in queue}
    strat_by_claim = {x['claim_id']: x for x in strategies}
    binding_by_claim = {x['claim_id']: x for x in bindings}
    suggestions_by_claim = {}
    for s in suggestions:
        key = s.get('target_claim_id') or s.get('claim_id')
        if key:
            suggestions_by_claim.setdefault(key, []).append(s)

    overview_sentences = []
    for item in sentence_items:
        sentence_id = item['sentence_id']
        q = queue_by_sentence.get(sentence_id)
        claim_id = q['claim_id'] if q else None
        b = binding_by_claim.get(claim_id, {}) if claim_id else {}
        support_grade = b.get('support_grade', '')
        risk = q.get('risk_level', 'low') if q else 'low'
        claim_type = q.get('claim_type', 'strong_supported_claim') if q else 'strong_supported_claim'
        status_label = 'strong'
        if support_grade == 'complete_refutation':
            status_label = 'refutation-review'
        elif risk == 'high':
            status_label = 'risky'
        elif support_grade in ['proxy_support', 'mechanism_support']:
            status_label = 'weak'
        elif support_grade == 'caveat':
            status_label = 'caveat-needed'
        elif b.get('insufficiency_reason') == 'fulltext_pending':
            status_label = 'pending-evidence'
        overview_sentences.append({
            'sentence_id': sentence_id,
            'preview_text': item['text'][:180],
            'claim_badge': claim_type,
            'support_badge': support_grade or 'none',
            'risk_color': risk,
            'icons': {
                'direct': support_grade == 'direct_support',
                'mechanism': support_grade == 'mechanism_support',
                'proxy': support_grade == 'proxy_support',
                'caveat': support_grade == 'caveat',
                'refutation': support_grade == 'complete_refutation',
                'pending': b.get('insufficiency_reason') == 'fulltext_pending',
            },
            'sentence_status': status_label,
        })
    return {
        'doc_status': status.get('status', 'WARN'),
        'sentence_items': sentence_items,
        'queue_by_sentence': queue_by_sentence,
        'strat_by_claim': strat_by_claim,
        'binding_by_claim': binding_by_claim,
        'suggestions_by_claim': suggestions_by_claim,
        'passages': passages,
        'pending': pending,
        'unavailable': unavailable,
        'overview_sentences': overview_sentences,
        'debug': {
            'queue': queue,
            'strategies': strategies,
            'bindings': bindings,
            'suggestions': suggestions,
        }
    }


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed = urlparse(path)
        clean = parsed.path.lstrip('/') or 'index.html'
        return str(PUBLIC / clean)

    def _send_json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)
        if path.startswith('/api/'):
            return self.handle_api(path, qs)
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/session'):
            length = int(self.headers.get('Content-Length', '0'))
            body = self.rfile.read(length) if length else b'{}'
            payload = json.loads(body.decode('utf-8'))
            save_json(SESSION_FILE, payload)
            return self._send_json({'ok': True})
        if parsed.path.startswith('/api/override'):
            length = int(self.headers.get('Content-Length', '0'))
            body = self.rfile.read(length) if length else b'{}'
            payload = json.loads(body.decode('utf-8'))
            negative_buttons = {'틀림', '과민판정', '근거약함', '버려라'}
            if payload.get('verdict') in negative_buttons and not payload.get('reason_tag'):
                return self._send_json({'ok': False, 'error': 'reason_tag_required'}, 400)
            saved = save_override(payload['document_id'], payload['sentence_id'], payload['verdict'])
            if payload.get('reason_tag'):
                saved['reason_tag'] = payload.get('reason_tag')
                saved['optional_comment'] = payload.get('optional_comment')
                save_override(payload['document_id'], payload['sentence_id'], payload['verdict'])
            return self._send_json({'ok': True, 'saved': saved})
        if parsed.path.startswith('/api/insert-sentence'):
            length = int(self.headers.get('Content-Length', '0'))
            body = self.rfile.read(length) if length else b'{}'
            payload = json.loads(body.decode('utf-8'))
            rows = load_json(STATE / 'user_inserted_sentences.json', [])
            anchor = payload['insert_after_sentence_id']
            existing = [r for r in rows if r.get('anchor_sentence_id') == anchor]
            display_id = f"{anchor}-{len(existing)+1}"
            try:
                base_num = float(anchor.replace('S', ''))
            except Exception:
                base_num = float(len(rows)+1)
            existing_keys = [float(r.get('display_order_key')) for r in existing if r.get('display_order_key') is not None]
            display_order_key = next_fractional_order(existing_keys, base_num)
            row = {
                'inserted_sentence_id': display_id,
                'anchor_sentence_id': anchor,
                'insert_after_sentence_id': anchor,
                'display_order_key': display_order_key,
                'display_id': display_id,
                'text': payload['text'],
                'created_at': int(time.time()),
                'updated_at': int(time.time()),
                'status': 'saved',
                'source': 'user',
            }
            rows.append(row)
            save_json(STATE / 'user_inserted_sentences.json', rows)
            return self._send_json({'ok': True, 'saved': row})
        if parsed.path.startswith('/api/deepen'):
            length = int(self.headers.get('Content-Length', '0'))
            body = self.rfile.read(length) if length else b'{}'
            payload = json.loads(body.decode('utf-8'))
            deepening_rows = load_rows_by_sentence(DEEPENING_FILE)
            sentence_id = payload.get('sentence_id')
            row = deepening_rows.get(sentence_id, {})
            return self._send_json({'ok': True, 'sentence_id': sentence_id, 'packet': row})
        self.send_error(HTTPStatus.NOT_FOUND)

    def handle_api(self, path, qs):
        if path == '/api/session':
            state = load_json(SESSION_FILE, {
                'current_document_id': 'deepevidence-v1',
                'selected_sentence_id': None,
                'current_filters': {},
                'sort_mode': 'sentence_order',
                'active_right_pane_tab': 'evidence',
                'last_view_timestamp': int(time.time()),
                'mobile_or_desktop_last_mode': 'desktop',
            })
            return self._send_json(state)
        if path == '/api/debug/documents':
            return self._send_json({'documents': list(DOCS.keys())})
        if path == '/api/overrides':
            return self._send_json(load_overrides())
        if path == '/api/refresh-jobs':
            return self._send_json(load_json(REFRESH_JOBS_FILE, []))
        if path == '/api/console-state-index':
            return self._send_json(load_json(CONSOLE_STATE_FILE, []))

        parts = path.strip('/').split('/')
        if len(parts) < 3 or parts[1] != 'document':
            return self._send_json({'error': 'bad_api_path'}, 404)
        doc_id = parts[2]
        doc_root = DOCS.get(doc_id)
        if not doc_root:
            return self._send_json({'error': 'unknown_doc_id'}, 404)
        idx = build_doc_index(doc_root)
        overrides = load_overrides().get('by_document', {}).get(doc_id, {})
        paper_metadata = load_paper_metadata()
        sentence_level_binding = load_sentence_level_binding()
        validation_rows = load_rows_by_sentence(VALIDATION_FILE)
        salvage_rows = load_rows_by_sentence(SALVAGE_FILE)
        deepening_rows = load_rows_by_sentence(DEEPENING_FILE)
        rewrite_rows = load_rows_by_sentence(REWRITE_FILE)
        strength_rows = load_rows_by_sentence(STRENGTH_FILE)
        rewrite_option_rows = load_rows_by_sentence(REWRITE_OPTIONS_FILE)
        transition_rows = load_rows_by_sentence(TRANSITION_FILE)
        citation_rows = load_rows_by_sentence(CITATION_FILE)
        refresh_jobs_rows = load_rows_by_sentence(REFRESH_JOBS_FILE)
        console_state_rows = load_rows_by_sentence(CONSOLE_STATE_FILE)

        if len(parts) == 4 and parts[3] == 'overview':
            return self._send_json({
                'document_id': doc_id,
                'document_status': idx['doc_status'],
                'sentence_count': len(idx['overview_sentences']),
                'pending_count': len(idx['pending']),
                'unavailable_count': len(idx['unavailable']),
            })
        if len(parts) == 4 and parts[3] == 'sentences':
            status_filter = qs.get('status', [''])[0]
            risk_filter = qs.get('risk', [''])[0]
            claim_filter = qs.get('claim', [''])[0]
            items = idx['overview_sentences']
            if status_filter:
                items = [x for x in items if x['sentence_status'] == status_filter]
            if risk_filter:
                items = [x for x in items if x['risk_color'] == risk_filter]
            if claim_filter:
                items = [x for x in items if x['claim_badge'] == claim_filter]
            for item in items:
                item['override_verdict'] = overrides.get(item['sentence_id'], {}).get('verdict')
            return self._send_json({'items': items})
        if len(parts) >= 5 and parts[3] == 'sentence':
            sentence_id = parts[4]
            sentence = next((x for x in idx['sentence_items'] if x['sentence_id'] == sentence_id), None)
            if not sentence:
                return self._send_json({'error': 'unknown_sentence'}, 404)
            q = idx['queue_by_sentence'].get(sentence_id, {})
            claim_id = q.get('claim_id')
            b = idx['binding_by_claim'].get(claim_id, {}) if claim_id else {}
            s = idx['strat_by_claim'].get(claim_id, {}) if claim_id else {}
            if len(parts) == 5:
                claim_type = q.get('claim_type', 'strong_supported_claim')
                claim_type_ko = {
                    'strong_supported_claim': '강한 지지 주장',
                    'advocacy_claim': '주장형 문장',
                    'weak_bridge_sentence': '약한 연결 문장',
                    'mechanism_claim': '기전 주장',
                }.get(claim_type, claim_type)
                support_level = q.get('current_support_level', 'moderate')
                support_level_ko = {
                    'high': '높음',
                    'moderate': '중간',
                    'low': '낮음',
                }.get(support_level, support_level)
                target_level = q.get('target_support_level', '')
                target_level_ko = {
                    'high': '높음',
                    'moderate': '중간',
                    'low': '낮음',
                    '': '',
                }.get(target_level, target_level)
                support_summary = b.get('support_grade', 'none')
                support_summary_ko = {
                    'none': '없음',
                    'insufficient': '불충분',
                    'direct_support': '직접 근거',
                    'mechanism_support': '기전 근거',
                    'proxy_support': '간접 근거',
                    'complete_refutation': '핵심 반박',
                    'caveat': '주의 필요',
                }.get(support_summary, support_summary)
                validation = validation_rows.get(sentence_id, {})
                salvage = salvage_rows.get(sentence_id, {})
                deepening = deepening_rows.get(sentence_id, {})
                rewrite = rewrite_rows.get(sentence_id, {})
                strength = strength_rows.get(sentence_id, {})
                rewrite_option = rewrite_option_rows.get(sentence_id, {})
                transition = transition_rows.get(sentence_id, {})
                citation = citation_rows.get(sentence_id, {})
                refresh_job = refresh_jobs_rows.get(sentence_id, {})
                console_state = console_state_rows.get(sentence_id, {})
                return self._send_json({
                    'sentence_id': sentence_id,
                    'full_sentence_text': sentence['text'],
                    'claim_type': claim_type_ko,
                    'current_support_level': support_level_ko,
                    'target_support_level': target_level_ko,
                    'risk_level': q.get('risk_level', 'low'),
                    'why_flagged': q.get('why_flagged', []),
                    'support_summary': support_summary_ko,
                    'ceiling_note': b.get('ceiling', ''),
                    'key_alerts': [x for x in [b.get('insufficiency_reason'), 'complete_refutation' if b.get('support_grade') == 'complete_refutation' else ''] if x],
                    'recommended_followup': s.get('strategy_list', []),
                    'override_verdict': overrides.get(sentence_id, {}).get('verdict'),
                    'validator_verdict': validation.get('verdict'),
                    'validator_reason_codes': validation.get('reason_codes', []),
                    'strongest_support_label': strength.get('strongest_support_label'),
                    'human_support_present': strength.get('human_support_present'),
                    'salvage_class': salvage.get('salvage_class'),
                    'salvage_next_action': salvage.get('next_action'),
                    'rewrite_recommendation': rewrite.get('recommendation_type'),
                    'rewrite_direction': rewrite.get('suggested_direction'),
                    'deepening_mode': deepening.get('mode'),
                    'recommended_sentence_option': rewrite_option.get('rewritten_candidate'),
                    'citation_strategy': citation.get('citation_strategy'),
                    'citation_primary': citation.get('primary_citation_paper_id'),
                    'paragraph_merge_candidate_ids': citation.get('paragraph_merge_candidate_ids', []),
                    'transition_verdict': transition.get('transition_verdict'),
                    'transition_issue_type': transition.get('issue_type'),
                    'refresh_job_status': refresh_job.get('job_status'),
                    'stale_flags': console_state.get('stale_flags', {}),
                })
            if len(parts) == 6 and parts[5] == 'evidence':
                sentence_binding = sentence_level_binding.get(sentence_id, {})
                selected_evidence = sentence_binding.get('selected_evidence', [])
                items = []
                for row in selected_evidence:
                    items.append({
                        'paper_id': row.get('paper_id'),
                        'passage_id': row.get('passage_id'),
                        'support_or_limit': row.get('support_or_limit'),
                        'what_it_actually_supports': row.get('what_it_actually_supports'),
                        'what_it_does_not_support': row.get('what_it_does_not_support'),
                        'key_passage_text': row.get('key_passage_text'),
                        'claim_ceiling_note': row.get('claim_ceiling_note'),
                        'population_or_context': row.get('population_or_context'),
                    })
                for item in items:
                    meta = paper_metadata.get(item.get('paper_id'), {})
                    item['title_full'] = meta.get('title_full', item.get('paper_id'))
                    item['title_ko'] = meta.get('title_ko', '')
                    item['vancouver_citation'] = meta.get('vancouver_citation', item.get('paper_id'))
                    item['support_ko'] = meta.get('support_ko', {}).get(item.get('what_it_actually_supports', ''), '')
                    item['key_passage_text_ko'] = meta.get('passage_ko', {}).get(item.get('key_passage_text', ''), '')
                return self._send_json({'items': items})
            if len(parts) == 6 and parts[5] == 'suggestions':
                items = idx['suggestions_by_claim'].get(claim_id, []) if claim_id else []
                return self._send_json({'items': items})
            if len(parts) == 6 and parts[5] == 'refutation':
                return self._send_json({
                    'claim_id': claim_id,
                    'support_grade': b.get('support_grade'),
                    'refutation_strength': b.get('refutation_strength'),
                    'refutation_scope': b.get('refutation_scope'),
                    'abandonment_recommended_flag': b.get('abandonment_recommended_flag', False),
                })
        if len(parts) == 4 and parts[3] == 'pending-fulltext':
            return self._send_json({'items': idx['pending']})
        if len(parts) == 4 and parts[3] == 'alerts':
            alerts = []
            for q in idx['queue_by_sentence'].values():
                b = idx['binding_by_claim'].get(q['claim_id'], {})
                if b.get('support_grade') == 'complete_refutation':
                    alerts.append({'sentence_id': q['sentence_id'], 'type': 'complete_refutation', 'claim_id': q['claim_id']})
                elif b.get('insufficiency_reason') == 'fulltext_pending':
                    alerts.append({'sentence_id': q['sentence_id'], 'type': 'pending_fulltext', 'claim_id': q['claim_id']})
            return self._send_json({'items': alerts})
        return self._send_json({'error': 'not_found'}, 404)

    def log_message(self, format, *args):
        return


def main():
    os.chdir(PUBLIC)
    server = ThreadingHTTPServer(('0.0.0.0', 8765), Handler)
    print('Review UI v2 on http://127.0.0.1:8765')
    server.serve_forever()


if __name__ == '__main__':
    main()
