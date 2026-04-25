const KO_LABELS = {
  status: {
    PASS: '통과', WARN: '주의 필요', BLOCKED: '차단', PENDING: '처리 대기',
    complete: '완료', incomplete: '미완료', unavailable: '근거 확인 불가'
  },
  risk: { low: '낮음', medium: '중간', high: '높음', critical: '최고 경고' },
  claim_type: {
    advocacy_claim: '주장형 문장',
    strong_supported_claim: '강한 근거가 붙은 주장',
    weak_bridge_sentence: '약한 연결 문장',
    definition_claim: '정의형 주장',
    mechanism_claim: '기전 주장',
    therapeutic_claim: '치료적 주장',
    background_sentence: '배경 설명',
    transition_sentence: '전환 문장',
    mixed_claims: '여러 주장이 섞인 문장',
    translational_extension: '확장 해석 문장'
  },
  support_badge: {
    insufficient: '근거 부족',
    proxy_support: '간접 근거',
    mechanism_support: '기전 근거',
    in_vitro: '세포·실험실 근거',
    ex_vivo: '체외 실험 근거',
    animal: '동물 근거',
    translational: '중개 근거',
    human_observational: '사람 관찰 근거',
    human_clinical: '사람 임상 근거',
    direct_human: '직접 사람 근거',
    caveat: '제한/주의 필요',
    complete_refutation: '강한 반박 경고',
    direct_support: '직접 근거',
    none: '없음'
  },
  reason_code: {
    keyword_only_match: '키워드만 일치',
    no_direct_support: '직접 근거 없음',
    weak_directness: '직접성 약함',
    proxy_only: '간접 근거뿐',
    human_evidence_missing: '사람 근거 없음',
    overclaim_risk: '과장 위험',
    therapeutic_leap: '치료 효과로 비약',
    evidence_conflict: '근거 충돌',
    counter_evidence_found: '반대 근거 있음',
    mixed_claims: '여러 주장이 섞임',
    unsupported_definition: '정의 근거 부족',
    off_topic_domain_drift: '논문 방향 불일치',
    shared_pool_contamination: '공유 근거풀 오염 가능성',
    entropy_overextension: '엔트로피 논리 과확장',
    no_attachable_support: '붙일 수 있는 근거 없음',
    direct_quote_match: '직접 인용 일치',
    mechanism_support_only: '기전 근거만 있음',
    same_paper_redundant: '같은 논문 반복',
    indirect_but_relevant: '간접이지만 관련 있음',
    entropy_paper_outside_entropy_sentence: '엔트로피 논문 과적용'
  },
  action: {
    direct_support_search: '직접 근거 검색',
    mechanism_backfill_search: '기전 근거 보강',
    counter_limit_search: '반론·한계 근거 검색',
    adjacent_domain_search: '인접 분야 근거 검색',
    stronger_human_first: '사람 근거 우선 검색',
    split_sentence_into_two_claims: '두 문장으로 분리',
    weaken_claim: '표현 약화',
    narrow_scope: '범위 축소',
    convert_to_mechanism_sentence: '기전 설명문으로 전환',
    abandon_claim: '현재 주장 포기',
    salvage_with_caveat: '주의 문구 붙여 유지',
    rerun_binding: '근거 연결 재검토'
  },
  rewrite: {
    split_sentence_into_two_claims: '두 문장으로 분리 권고',
    soften_definition: '정의 표현 약화',
    add_guardrail_phrase: '주의 문구 추가',
    convert_to_hypothesis: '가설형 표현으로 전환',
    convert_to_mechanistic_framing: '기전 중심 표현으로 전환',
    remove_or_replace: '삭제 또는 대체 권고',
    soften_claim: '표현 약화',
    narrow_scope: '범위 축소',
    convert_to_mechanistic_statement: '기전 중심 표현으로 전환',
    require_citation_split: '인용 분리 필요'
  },
  citation: {
    single_primary: '대표 논문 1개 중심',
    multi_support: '복수 근거 병렬',
    mechanism_cluster: '기전 논문 묶음',
    human_plus_mechanism: '사람 근거 + 기전 근거',
    citation_not_recommended: '인용보다 문장 수정 우선',
    no_citation_recommended_until_salvaged: '인용보다 보강/수정 우선'
  }
};

const KO_EXPLANATIONS = {
  support_badge: {
    complete_refutation: {
      label: '강한 반박 경고',
      short: '문장 핵심 주장과 충돌하는 근거가 감지되었습니다.',
      long: '이 문장은 단순히 근거가 부족한 것이 아니라, 현재 형태의 핵심 주장 방향이 깨질 수 있습니다. 반박 근거를 확인한 뒤 삭제, 약화, 범위 축소, 문장 분리, 또는 기전문장 전환 여부를 결정해야 합니다.'
    }
  }
};

function formatKo(value, category) {
  const raw = String(value ?? '');
  const group = KO_LABELS[category] || {};
  if (group[raw]) return group[raw];
  console.warn('[ko_labels] missing key', category, raw);
  return raw.replaceAll('_', ' ').toUpperCase() + ' (미정의)';
}

function formatKoList(values, category) {
  return (values || []).map(v => formatKo(v, category));
}

function getKoExplanation(value, category) {
  return KO_EXPLANATIONS?.[category]?.[value] || null;
}

function renderKoBadge(value, category, options = {}) {
  const raw = String(value ?? '');
  const span = document.createElement('span');
  span.className = `badge badge-${raw}`;
  span.dataset.rawValue = raw;
  span.dataset.category = category;
  span.textContent = formatKo(raw, category);
  if (options.titleRaw) span.title = raw;
  return span;
}
