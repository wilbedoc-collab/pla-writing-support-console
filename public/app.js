const state = {
  docId: 'deepevidence-v1',
  selectedSentenceId: null,
  activeTab: 'evidence',
  mobileMode: 'read',
  mobileScreen: 'home',
  debug: false,
  overview: null,
  sentences: [],
  sentenceDetail: null,
  evidence: [],
  refutation: null,
  pending: [],
  alerts: [],
  overrides: {},
  session: {},
};

async function api(path, options={}) {
  const res = await fetch(path, {headers:{'Content-Type':'application/json'}, ...options});
  if (!res.ok) throw new Error(`API ${path} ${res.status}`);
  return res.json();
}

function qs(sel){return document.querySelector(sel)}
function ce(tag, cls, text){const el=document.createElement(tag); if(cls) el.className=cls; if(text!==undefined) el.textContent=text; return el;}
function isMobile(){ return document.body.classList.contains('force-mobile'); }

function applyViewportMode(){
  const mobile = window.innerWidth <= 900 || /Android|iPhone|iPad|Mobile/i.test(navigator.userAgent);
  document.body.classList.toggle('force-mobile', mobile);
}

async function loadDocuments(){
  const docs = await api('/api/debug/documents');
  const select = qs('#docSelect');
  select.innerHTML='';
  docs.documents.forEach(id=>{
    const opt = ce('option','',id); opt.value=id; if(id===state.docId) opt.selected=true; select.appendChild(opt);
  });
}

async function loadSession(){
  state.session = await api('/api/session');
  if (state.session.current_document_id) state.docId = state.session.current_document_id;
  if (state.session.selected_sentence_id) state.selectedSentenceId = state.session.selected_sentence_id;
  if (state.session.active_right_pane_tab) state.activeTab = state.session.active_right_pane_tab;
  if (state.session.mobile_mode) state.mobileMode = state.session.mobile_mode;
}

async function saveSession(){
  state.session = {
    current_document_id: state.docId,
    selected_sentence_id: state.selectedSentenceId,
    current_filters: {
      status: qs('#statusFilter')?.value || '',
      risk: qs('#riskFilter')?.value || '',
    },
    sort_mode: 'sentence_order',
    active_right_pane_tab: state.activeTab,
    last_view_timestamp: Date.now(),
    mobile_or_desktop_last_mode: isMobile() ? 'mobile' : 'desktop',
    mobile_mode: state.mobileMode,
  };
  await api('/api/session', {method:'POST', body: JSON.stringify(state.session)});
}

async function loadOverview(){
  state.overview = await api(`/api/document/${state.docId}/overview`);
  const box = qs('#overview');
  if (!box) return;
  box.innerHTML = `
    <div><strong>${state.docId}</strong></div>
    <div class="muted">doc status: ${state.overview.document_status}</div>
    <div class="muted">sentences: ${state.overview.sentence_count}</div>
    <div class="muted">pending: ${state.overview.pending_count} / unavailable: ${state.overview.unavailable_count}</div>
  `;
}

async function loadOverrides(){
  const data = await api('/api/overrides');
  state.overrides = data.by_document?.[state.docId] || {};
}

async function loadSentences(){
  const params = new URLSearchParams();
  if (qs('#statusFilter')?.value) params.set('status', qs('#statusFilter').value);
  if (qs('#riskFilter')?.value) params.set('risk', qs('#riskFilter').value);
  const data = await api(`/api/document/${state.docId}/sentences?${params.toString()}`);
  state.sentences = data.items;
  renderSentenceList();
  renderFullTextView();
  renderMobileHome();
}

function renderSentenceCard(item, onClick){
  const card = ce('div', 'sentence-card' + (item.sentence_id === state.selectedSentenceId ? ' active' : ''));
  card.onclick = onClick;
  card.appendChild(ce('div','sentence-id',item.sentence_id));
  card.appendChild(ce('div','',item.preview_text));
  const badges = ce('div','badges');
  badges.appendChild(renderKoBadge(item.claim_badge, 'claim_type', {titleRaw:true}));
  badges.appendChild(renderKoBadge(item.support_badge, 'support_badge', {titleRaw:true}));
  const risk = renderKoBadge(item.risk_color, 'risk', {titleRaw:true});
  risk.classList.add('risk-' + item.risk_color);
  badges.appendChild(risk);
  if(item.override_verdict){ const ov=ce('span','badge'); ov.textContent=`판정:${item.override_verdict}`; badges.appendChild(ov); }
  card.appendChild(badges);
  return card;
}

function renderSentenceList(){
  const wrap = qs('#sentenceList');
  if(!wrap) return;
  wrap.innerHTML = '';
  state.sentences.forEach(item => wrap.appendChild(renderSentenceCard(item, ()=>selectSentence(item.sentence_id))));
}

function renderFullTextView(){
  const wrap = qs('#fullTextView');
  if(!wrap) return;
  wrap.innerHTML = '';
  state.sentences.forEach(item => {
    const card = ce('div','fulltext-sentence-card');
    card.onclick = () => selectSentence(item.sentence_id);
    card.appendChild(ce('div','sentence-id',item.sentence_id));
    card.appendChild(ce('div','fulltext-text',item.preview_text));
    wrap.appendChild(card);
  });
}

function renderMobileHome(){
  const readBtn = qs('#modeReadAll');
  const reviewBtn = qs('#modeReview');
  const fullTextView = qs('#fullTextView');
  const sentenceList = qs('#sentenceList');
  if(!readBtn || !reviewBtn || !fullTextView || !sentenceList) return;
  readBtn.classList.toggle('active', state.mobileMode === 'read');
  reviewBtn.classList.toggle('active', state.mobileMode === 'review');
  if(!isMobile()){
    fullTextView.style.display = 'none';
    sentenceList.style.display = '';
    return;
  }
  const showHome = state.mobileScreen === 'home';
  fullTextView.style.display = showHome && state.mobileMode === 'read' ? 'block' : 'none';
  sentenceList.style.display = showHome && state.mobileMode === 'review' ? 'block' : 'none';
  qs('#mobileDetailPage')?.classList.toggle('hidden', state.mobileScreen !== 'detail');
}

async function selectSentence(sentenceId){
  state.selectedSentenceId = sentenceId;
  await saveSession();
  state.sentenceDetail = await api(`/api/document/${state.docId}/sentence/${sentenceId}`);
  state.evidence = (await api(`/api/document/${state.docId}/sentence/${sentenceId}/evidence`)).items;
  state.refutation = await api(`/api/document/${state.docId}/sentence/${sentenceId}/refutation`);
  renderSentenceList();
  renderDetail();
  renderRightPane();
  if (isMobile()) {
    state.mobileScreen = 'detail';
    renderMobileDetailPage();
    renderMobileHome();
  }
}

async function saveVerdict(verdict){
  if(!state.selectedSentenceId) return;
  await api('/api/override', {
    method:'POST',
    body: JSON.stringify({
      document_id: state.docId,
      sentence_id: state.selectedSentenceId,
      verdict,
    })
  });
  state.overrides[state.selectedSentenceId] = { verdict };
  if(state.sentenceDetail) state.sentenceDetail.override_verdict = verdict;
  await loadSentences();
  renderDetail();
  renderMobileDetailPage();
}


async function runRefresh(){
  if(!state.selectedSentenceId) return;
  await api('/api/deepen', { method:'POST', body: JSON.stringify({ sentence_id: state.selectedSentenceId }) });
  const detail = qs('#sentenceDetail');
  if(detail){
    const box = document.createElement('div');
    box.className = 'meta-box stacked-box';
    box.innerHTML = `<div class="muted">async refresh 안내</div><div class="stacked-value">현재 v2에서는 refresh job artifact를 생성해두었고, 이 문장은 sentence-local refresh 대상으로 등록되어 있습니다. 상세 refresh status는 상단 메타에서 확인하세요.</div>`;
    detail.appendChild(box);
  }
  if(isMobile()) renderMobileDetailPage();
}

async function runInsertSentence(){
  if(!state.selectedSentenceId) return;
  const text = window.prompt('삽입할 새 문장을 입력하세요.');
  if(!text || !text.trim()) return;
  await api('/api/insert-sentence', {
    method:'POST',
    body: JSON.stringify({ insert_after_sentence_id: state.selectedSentenceId, text: text.trim() })
  });
  const detail = qs('#sentenceDetail');
  if(detail){
    const box = document.createElement('div');
    box.className = 'meta-box stacked-box';
    box.innerHTML = `<div class="muted">사용자 삽입 문장</div><div class="stacked-value">${text.trim()}</div>`;
    detail.appendChild(box);
  }
  if(isMobile()) renderMobileDetailPage();
}

async function runDeepening(){
  if(!state.selectedSentenceId) return;
  const res = await api('/api/deepen', {
    method:'POST',
    body: JSON.stringify({ sentence_id: state.selectedSentenceId })
  });
  const packet = res.packet || {};
  const detail = qs('#sentenceDetail');
  if(detail){
    const box = document.createElement('div');
    box.className = 'meta-box stacked-box';
    box.innerHTML = `<div class="muted">sentence-targeted deepening</div>
      <div class="stacked-value">mode: ${packet.mode || '-'}<br>weakness: ${(packet.weakness_profile || []).join(', ') || '-'}<br>targets: ${packet.deepening_targets || '-'}<br>candidates: ${(packet.recommended_candidates || []).join(', ') || '-'}</div>`;
    detail.appendChild(box);
  }
  if(isMobile()) renderMobileDetailPage();
}


function renderDetail(){
  const d = state.sentenceDetail;
  const wrap = qs('#sentenceDetail');
  if(!wrap) return;
  if(!d){ wrap.innerHTML='문장을 선택하세요.'; return; }
  wrap.innerHTML = '';
  wrap.appendChild(ce('div','sentence-id',d.sentence_id));
  wrap.appendChild(ce('div','full-sentence',d.full_sentence_text));
  const grid = ce('div','meta-grid');
  const meta = [
    ['주장 유형', d.claim_type], ['현재 근거 수준', d.current_support_level], ['목표 근거 수준', d.target_support_level], ['리스크', d.risk_level], ['근거 요약', d.support_summary], ['상한 메모', d.ceiling_note || '-'],
    ['검증 판정', d.validator_verdict || '-'], ['최강 근거 라벨', d.strongest_support_label || '-'], ['사람 근거 포함', d.human_support_present === undefined ? '-' : (d.human_support_present ? '있음' : '없음')], ['구제 분류', d.salvage_class || '-'], ['재작성 권고', d.rewrite_recommendation || '-'], ['딥닝 모드', d.deepening_mode || '-'],
    ['추천 문장', d.recommended_sentence_option || '-'], ['citation 전략', d.citation_strategy || '-'], ['citation primary', d.citation_primary || '-'], ['흐름 판정', d.transition_verdict || '-'], ['흐름 이슈', d.transition_issue_type || '-'], ['refresh 상태', d.refresh_job_status || '-']
  ];
  meta.forEach(([k,v])=>{ const box=ce('div','meta-box'); const kDiv=ce('div','muted',k); const vDiv=ce('div','', String(v || '-')); box.appendChild(kDiv); box.appendChild(vDiv); grid.appendChild(box); });
  wrap.appendChild(grid);
  const why = ce('div','meta-box stacked-box');
  why.innerHTML = `
    <div class="muted">문장 경고 이유</div>
    <div class="stacked-value">${(d.why_flagged||[]).join(', ') || '-'}</div>
    <div class="muted" style="margin-top:12px">검증 reason codes</div>
    <div class="stacked-value">${(d.validator_reason_codes||[]).join(', ') || '-'}</div>
    <div class="muted" style="margin-top:12px">권장 후속 작업</div>
    <div class="stacked-value">${(d.recommended_followup||[]).join(', ') || '-'}</div>
    <div class="muted" style="margin-top:12px">다음 액션</div>
    <div class="stacked-value">${d.salvage_next_action || d.rewrite_direction || '-'}</div>
  `;
  wrap.appendChild(why);
  const qa = ce('div','quick-actions action-grid');
  ['맞음','틀림','과민판정','근거약함','더 찾아라','버려라','살려라'].forEach(label=>{
    const btn = ce('button', d.override_verdict === label ? 'active-verdict' : '', label);
    btn.onclick = () => saveVerdict(label);
    qa.appendChild(btn);
  });
  const deepenBtn = ce('button','deepening-button','이 문장 보강');
  deepenBtn.onclick = () => runDeepening();
  qa.appendChild(deepenBtn);
  const refreshBtn = ce('button','deepening-button','근거 재검색');
  refreshBtn.onclick = () => runRefresh();
  qa.appendChild(refreshBtn);
  const insertBtn = ce('button','deepening-button','문장 추가');
  insertBtn.onclick = () => runInsertSentence();
  qa.appendChild(insertBtn);
  wrap.appendChild(qa);
}

function evidenceRoleLabel(v){
  const map = {
    direct_support: '직접 근거',
    mechanism_support: '기전 근거',
    proxy_support: '간접 근거',
    caveat: '주의 근거',
    limit: '제한 근거',
    support: '근거',
  };
  return map[v] || v || '근거';
}

function renderEvidence(){
  if(!state.evidence.length) return '<div class="muted">연결된 근거가 아직 없습니다.</div>';
  return state.evidence.map(ev=>`
    <div class="paper-card evidence-readable-card">
      <div class="evidence-section">
        <div class="muted">논문 제목</div>
        <div><strong>${ev.title_full || ev.paper_id || '-'}</strong></div>
      </div>
      <div class="evidence-section">
        <div class="muted">논문 제목 한글</div>
        <div>${ev.title_ko || '-'}</div>
      </div>
      <div class="evidence-section">
        <div class="muted">논문 설명</div>
        <div>${ev.vancouver_citation || ev.paper_id || '-'}</div>
      </div>
      <div class="evidence-section">
        <div class="muted">이 문장에 도움이 되는 핵심</div>
        <div>${ev.what_it_actually_supports || '-'}</div>
      </div>
      <div class="evidence-section">
        <div class="muted">이 문장에 도움이 되는 핵심 한글 번역</div>
        <div>${ev.support_ko || '-'}</div>
      </div>
      <div class="evidence-section">
        <div class="muted">핵심 인용 / 발췌</div>
        <div class="quote-like">${ev.key_passage_text || '-'}</div>
      </div>
      <div class="evidence-section">
        <div class="muted">핵심 인용 / 발췌 한글 번역</div>
        <div class="quote-like">${ev.key_passage_text_ko || '-'}</div>
      </div>
      <div class="evidence-meta-list">
        <div><span class="muted">근거 종류</span><br>${evidenceRoleLabel(ev.support_or_limit)}</div>
        <div><span class="muted">주장 상한</span><br>${ev.claim_ceiling_note || '-'}</div>
      </div>
    </div>
  `).join('');
}


function renderRecommendations(){
  if(!state.sentenceDetail) return '<div class="muted">추천 정보 없음</div>';
  return `<div class="paper-card"><div><strong>추천 문장</strong></div><div>${state.sentenceDetail.recommended_sentence_option || '-'}</div><div class="muted">재작성 권고: ${state.sentenceDetail.rewrite_recommendation || '-'}</div></div>`;
}

function renderCitation(){
  if(!state.sentenceDetail) return '<div class="muted">citation 정보 없음</div>';
  return `<div class="paper-card"><div><strong>citation 전략</strong></div><div>${state.sentenceDetail.citation_strategy || '-'}</div><div class="muted">primary: ${state.sentenceDetail.citation_primary || '-'}</div><div class="muted">paragraph merge: ${(state.sentenceDetail.paragraph_merge_candidate_ids || []).join(', ') || '-'}</div></div>`;
}

function renderTransition(){
  if(!state.sentenceDetail) return '<div class="muted">흐름 정보 없음</div>';
  return `<div class="paper-card"><div><strong>흐름 판정</strong></div><div>${state.sentenceDetail.transition_verdict || '-'}</div><div class="muted">이슈: ${state.sentenceDetail.transition_issue_type || '-'}</div></div>`;
}

function renderFeedback(){
  if(!state.sentenceDetail) return '<div class="muted">피드백 정보 없음</div>';
  return `<div class="paper-card"><div><strong>피드백 저장 규칙</strong></div><div class="muted">부정 피드백은 reason tag가 필요합니다.</div></div>`;
}

function renderRefutation(){
  if(!state.refutation) return '<div class="muted">refutation 정보 없음</div>';
  return `
    <div class="alert-card">
      <div><strong>${formatKo(state.refutation.support_grade || 'none', 'support_badge')}</strong></div>
      <div class="muted">반박 강도: ${formatKo(state.refutation.refutation_strength || '-', 'risk')}</div>
      <div class="muted">반박 범위: ${state.refutation.refutation_scope || '-'}</div>
      <div class="muted">현재 형태 유지 가능 여부: ${state.refutation.abandonment_recommended_flag ? '유지 어려움' : '재검토 후 유지 가능'}</div>
    </div>
  `;
}

async function loadPending(){
  state.pending = (await api(`/api/document/${state.docId}/pending-fulltext`)).items;
  state.alerts = (await api(`/api/document/${state.docId}/alerts`)).items;
}

function renderPending(){
  if(!state.pending.length && !state.alerts.length) return '<div class="muted">pending / alerts 없음</div>';
  let html = '';
  if(state.pending.length){
    html += state.pending.map(p=>`
      <div class="paper-card">
        <div><strong>${p.candidate_id}</strong></div>
        <div class="muted">why needed: ${p.why_needed}</div>
        <div class="muted">required action: ${p.required_action}</div>
        <div class="muted">next retry: ${p.next_retry_condition}</div>
      </div>
    `).join('');
  }
  if(state.alerts.length){
    html += state.alerts.map(a=>`<div class="alert-card"><strong>${a.type}</strong> <div class="muted">${a.sentence_id}</div></div>`).join('');
  }
  return html;
}

function renderRightPane(){
  const wrap = qs('#rightPaneContent');
  if(!wrap) return;
  if(state.activeTab === 'evidence') wrap.innerHTML = renderEvidence();
  else if(state.activeTab === 'recommendations') wrap.innerHTML = renderRecommendations();
  else if(state.activeTab === 'citation') wrap.innerHTML = renderCitation();
  else if(state.activeTab === 'transition') wrap.innerHTML = renderTransition();
  else if(state.activeTab === 'feedback') wrap.innerHTML = renderFeedback();
  else if(state.activeTab === 'refutation') wrap.innerHTML = renderRefutation();
  else wrap.innerHTML = renderPending();
  renderDebug();
}

function renderMobileDetailPage(){
  const page = qs('#mobileDetailPage');
  const content = qs('#mobileDetailContent');
  const title = qs('#detailPageTitle');
  if(!page || !content || !title) return;
  if(state.mobileScreen !== 'detail' || !state.sentenceDetail){
    page.classList.add('hidden');
    content.innerHTML = '';
    return;
  }
  title.textContent = state.selectedSentenceId || '문장 상세';
  content.innerHTML = qs('#sentenceDetail').innerHTML + '<hr>' + (
    state.activeTab === 'evidence' ? renderEvidence() :
    state.activeTab === 'recommendations' ? renderRecommendations() :
    state.activeTab === 'citation' ? renderCitation() :
    state.activeTab === 'transition' ? renderTransition() :
    state.activeTab === 'feedback' ? renderFeedback() :
    state.activeTab === 'refutation' ? renderRefutation() :
    renderPending()
  );
  page.classList.remove('hidden');
  document.querySelectorAll('[data-mobile-page-tab]').forEach(btn=>{
    btn.classList.toggle('active', btn.dataset.mobilePageTab === state.activeTab);
  });
}

function renderDebug(){
  const panel = qs('#debugPanel');
  if(!panel) return;
  if(!state.debug){ panel.classList.add('hidden'); return; }
  panel.classList.remove('hidden');
  panel.textContent = JSON.stringify({detail: state.sentenceDetail, evidence: state.evidence, refutation: state.refutation}, null, 2);
}

function bindEvents(){
  qs('#docSelect')?.addEventListener('change', async (e)=>{ state.docId = e.target.value; state.selectedSentenceId = null; await saveSession(); await bootDoc(); });
  qs('#statusFilter')?.addEventListener('change', async ()=>{ await loadSentences(); await saveSession(); });
  qs('#riskFilter')?.addEventListener('change', async ()=>{ await loadSentences(); await saveSession(); });
  document.querySelectorAll('.tabs button').forEach(btn=>btn.addEventListener('click', ()=>{
    document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    state.activeTab = btn.dataset.tab;
    renderRightPane();
    renderMobileDetailPage();
    saveSession();
  }));
  qs('#modeReadAll')?.addEventListener('click', ()=>{ state.mobileMode = 'read'; renderMobileHome(); saveSession(); });
  qs('#modeReview')?.addEventListener('click', ()=>{ state.mobileMode = 'review'; renderMobileHome(); saveSession(); });
  document.querySelectorAll('[data-mobile-page-tab]').forEach(btn=>btn.addEventListener('click', ()=>{
    state.activeTab = btn.dataset.mobilePageTab;
    renderMobileDetailPage();
    saveSession();
  }));
  qs('#closeDetailPage')?.addEventListener('click', ()=>{
    state.mobileScreen = 'home';
    state.selectedSentenceId = null;
    state.sentenceDetail = null;
    state.evidence = [];
    state.refutation = null;
    renderMobileDetailPage();
    renderMobileHome();
    saveSession();
  });
  qs('#debugToggle')?.addEventListener('click', ()=>{ state.debug = !state.debug; renderDebug(); });
}

async function bootDoc(){
  state.mobileScreen = 'home';
  await loadOverrides();
  await loadOverview();
  await loadSentences();
  await loadPending();
  renderRightPane();
  renderMobileHome();
  renderMobileDetailPage();
}

async function boot(){
  applyViewportMode();
  window.addEventListener('resize', ()=>{ applyViewportMode(); renderMobileHome(); renderMobileDetailPage(); });
  await loadSession();
  await loadDocuments();
  qs('#docSelect').value = state.docId;
  bindEvents();
  await bootDoc();
  if('serviceWorker' in navigator){ navigator.serviceWorker.register('/sw.js').catch(()=>{}); }
}

boot().catch(err=>{
  console.error(err);
  const target = qs('#sentenceDetail') || document.body;
  target.textContent = 'UI load failed: ' + err.message;
});
