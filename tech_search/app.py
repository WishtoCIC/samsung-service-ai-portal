"""
Samsung Service Tech Portal — Galaxy S26 Ultra 최적화 모바일 앱
3-Agent 구조: DocAgent | FeedbackAgent | StatusAgent
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import plotly.graph_objects as go

from search_engine import load_documents, search, highlight
from agents.doc_agent import DocAgent
from agents.feedback_agent import FeedbackAgent, STATUS_FLOW, CATEGORY_MAP
from agents.status_agent import StatusAgent

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  페이지 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="Tech Portal",
    page_icon="🔧",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Galaxy S26 Ultra 최적화 CSS
#  뷰포트: ~412 × 932 px  / 화면 비율 19.3:9
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
/* ── 전역 리셋 & 폰트 ── */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

html, body, [class*="css"] {
  font-family: 'Noto Sans KR', sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* ── 컨테이너 ── */
.block-container {
  max-width: 430px !important;
  padding: 0 12px 80px !important;
  margin: 0 auto !important;
}

/* ── 헤더 ── */
.mobile-header {
  background: linear-gradient(135deg, #1428A0 0%, #0b1f8a 100%);
  color: white;
  padding: 16px 18px 14px;
  border-radius: 0 0 20px 20px;
  margin: -12px -12px 16px;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(20,40,160,0.3);
}
.mobile-header .brand { font-size: 0.72rem; opacity: 0.75; letter-spacing: 1px; text-transform: uppercase; }
.mobile-header h1    { font-size: 1.25rem; font-weight: 700; margin: 2px 0 4px; color: white; }
.mobile-header .sub  { font-size: 0.73rem; opacity: 0.82; }

/* ── 카드 ── */
.card {
  background: white;
  border-radius: 16px;
  padding: 14px 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.07);
  border: 1px solid #f0f2f8;
}
.card-title {
  font-size: 0.82rem;
  font-weight: 700;
  color: #1428A0;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* ── 검색 결과 카드 ── */
.result-card {
  background: white;
  border-radius: 14px;
  padding: 14px;
  margin-bottom: 10px;
  border-left: 4px solid #1428A0;
  box-shadow: 0 2px 10px rgba(0,0,0,0.06);
}
.result-title { font-weight: 700; font-size: 0.92rem; color: #1428A0; margin-bottom: 4px; }
.result-meta  { font-size: 0.72rem; color: #888; margin-bottom: 8px; }
.result-chunk { font-size: 0.83rem; color: #333; line-height: 1.65; }

/* ── 배지 ── */
.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 0.68rem;
  font-weight: 600;
  margin-right: 4px;
  white-space: nowrap;
}
.b-blue   { background: #e8ecff; color: #1428A0; }
.b-green  { background: #e6f9ee; color: #1a7f3c; }
.b-orange { background: #fff3e0; color: #e65c00; }
.b-red    { background: #ffeaea; color: #c0392b; }
.b-gray   { background: #f0f0f4; color: #666; }
.b-yellow { background: #fff8e1; color: #b8860b; }
.b-teal   { background: #e0f7fa; color: #00695c; }

/* ── 요청 카드 ── */
.req-card {
  background: white;
  border-radius: 14px;
  padding: 14px;
  margin-bottom: 10px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.06);
  border: 1px solid #f0f2f8;
}
.req-id   { font-size: 0.68rem; color: #999; font-family: monospace; }
.req-title{ font-weight: 700; font-size: 0.9rem; color: #1428A0; margin: 4px 0; }
.req-body { font-size: 0.82rem; color: #444; line-height: 1.55; margin-top: 6px; }
.req-time { font-size: 0.70rem; color: #bbb; }

/* ── 피드백 댓글 ── */
.comment {
  padding: 10px 12px;
  border-radius: 12px;
  margin-bottom: 8px;
  font-size: 0.83rem;
  line-height: 1.55;
}
.comment-engineer { background: #f0f2ff; border-left: 3px solid #1428A0; }
.comment-manager  { background: #f0fff4; border-left: 3px solid #1a7f3c; }
.comment-author   { font-weight: 700; font-size: 0.72rem; margin-bottom: 4px; }
.comment-time     { font-size: 0.68rem; color: #aaa; float: right; }

/* ── 첨부 이미지 썸네일 ── */
.thumb-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
.thumb-row img {
  width: 72px; height: 72px; object-fit: cover;
  border-radius: 10px; border: 1px solid #e0e0e0;
}

/* ── 구분선 ── */
.divider { height: 1px; background: #f0f2f8; margin: 12px 0; }

/* ── 메트릭 그리드 ── */
.metric-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px; }
.metric-cell {
  background: white;
  border-radius: 14px;
  padding: 14px 12px;
  text-align: center;
  box-shadow: 0 2px 10px rgba(0,0,0,0.06);
}
.metric-value { font-size: 1.6rem; font-weight: 700; color: #1428A0; }
.metric-label { font-size: 0.72rem; color: #888; margin-top: 2px; }

/* ── 빠른검색 버튼 ── */
div[data-testid="stHorizontalBlock"] .stButton > button {
  font-size: 0.73rem !important;
  padding: 6px 8px !important;
  border-radius: 20px !important;
  white-space: nowrap;
}

/* ── 기본 버튼 크기 (터치 최적화) ── */
.stButton > button {
  min-height: 48px;
  border-radius: 12px !important;
  font-size: 0.9rem !important;
}

/* ── 탭 ── */
.stTabs [data-baseweb="tab-list"] {
  gap: 4px;
  background: #f4f6ff;
  padding: 6px;
  border-radius: 14px;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 10px !important;
  font-size: 0.78rem !important;
  padding: 8px 10px !important;
}
.stTabs [aria-selected="true"] {
  background: white !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

/* ── 에이전트 상태 표시 ── */
.agent-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: #f4f6ff;
  border: 1px solid #dde2ff;
  border-radius: 20px;
  padding: 4px 12px;
  font-size: 0.72rem;
  color: #1428A0;
  font-weight: 600;
}
.agent-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #22c55e;
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%,100% { opacity: 1; }
  50%      { opacity: 0.4; }
}

/* ── 입력창 ── */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
  border-radius: 12px !important;
  font-size: 0.88rem !important;
}

/* ── 진행 스텝 ── */
.step-bar {
  display: flex;
  align-items: center;
  gap: 0;
  margin: 12px 0;
  overflow-x: auto;
  padding-bottom: 4px;
}
.step {
  display: flex; align-items: center; gap: 4px;
  font-size: 0.68rem; white-space: nowrap;
}
.step-dot {
  width: 20px; height: 20px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.6rem; font-weight: 700;
}
.step-line { width: 24px; height: 2px; background: #e0e0e0; }
.step-active .step-dot { background: #1428A0; color: white; }
.step-done  .step-dot { background: #22c55e; color: white; }
.step-wait  .step-dot { background: #e0e0e0; color: #999; }
.step-label { color: #666; margin-top: 2px; }

/* ── 알림 배너 ── */
.alert-banner {
  background: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 12px;
  padding: 10px 14px;
  margin-bottom: 10px;
  font-size: 0.82rem;
  display: flex; align-items: center; gap: 8px;
}

/* ── SLA 경보 ── */
.sla-over {
  background: #ffeaea;
  border: 1px solid #f87171;
  border-radius: 12px;
  padding: 10px 14px;
  margin-bottom: 10px;
  font-size: 0.82rem;
}

/* ── 스크롤바 숨김 ── */
::-webkit-scrollbar { width: 0; }

/* ── 하단 여백 (navigation 공간) ── */
.footer-space { height: 20px; }
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  에이전트 초기화 (세션 캐시)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@st.cache_resource
def init_agents():
    fa = FeedbackAgent()
    sa = StatusAgent(fa)
    da = DocAgent()
    return da, fa, sa

@st.cache_resource
def load_docs():
    return load_documents()

doc_agent, fb_agent, st_agent = init_agents()
search_docs = load_docs()


def _get_indexed_docs():
    """DocAgent 인덱스에서 search_docs 형식으로 변환"""
    from search_engine import _chunk_text
    result = []
    for entry in doc_agent.index:
        path = Path(entry.get("path", ""))
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        result.append({
            "id": entry["id"],
            "filename": entry.get("filename", ""),
            "text": text,
            "meta": {
                "title": entry.get("title", path.stem),
                "product": entry.get("product_code", "전체"),
                "category": entry.get("category", "기술문서"),
                "doc_no": entry.get("doc_no", "—"),
            },
            "chunks": _chunk_text(text),
        })
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  모바일 헤더
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
stats = fb_agent.get_stats()
urgent_cnt = stats.get("urgent", 0)

st.markdown(f"""
<div class="mobile-header">
  <div class="brand">Samsung Service</div>
  <h1>🔧 Tech Portal</h1>
  <div style="display:flex; align-items:center; justify-content:space-between;">
    <div class="sub">기술정보 통합 검색 · 요청관리</div>
    <div style="display:flex; gap:6px; flex-wrap:wrap;">
      <span class="agent-badge"><span class="agent-dot"></span>DocAgent</span>
      <span class="agent-badge"><span class="agent-dot"></span>FeedbackAgent</span>
      <span class="agent-badge"><span class="agent-dot"></span>StatusAgent</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  탭
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 검색",
    "📄 문서등록",
    "📸 요청접수",
    "💬 피드백",
    "📊 현황",
])

# URL ?tab=N 파라미터로 탭 자동 이동 (0=검색, 1=문서등록, 2=요청접수, 3=피드백, 4=현황)
_tab_idx = int(st.query_params.get("tab", "0"))
if _tab_idx > 0:
    components.html(f"""
    <script>
    (function() {{
        function clickTab() {{
            var tabs = window.parent.document.querySelectorAll('[role="tab"]');
            if (tabs.length > {_tab_idx}) {{
                tabs[{_tab_idx}].click();
                return true;
            }}
            return false;
        }}
        if (!clickTab()) {{
            setTimeout(clickTab, 800);
        }}
    }})();
    </script>
    """, height=0)


# ════════════════════════════════════════════════════
# TAB 1 — 기술정보 검색
# ════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="card-title">🔍 기술정보 검색</div>', unsafe_allow_html=True)

    # 검색창
    query = st.text_input(
        "검색어",
        placeholder="증상·부품코드·알람코드 검색  예) 냉방불량, E6, EEV",
        label_visibility="collapsed",
        key="search_q",
    )

    # 제품 필터
    prod_col1, prod_col2, prod_col3, prod_col4 = st.columns(4)
    prod_map = {"전체": "전체", "HAC": "HAC", "SRA": "SRA", "CAC": "CAC"}
    sel_prod = st.session_state.get("prod_sel", "전체")

    if prod_col1.button("전체", use_container_width=True,
                         type="primary" if sel_prod=="전체" else "secondary"):
        st.session_state["prod_sel"] = "전체"; sel_prod = "전체"
    if prod_col2.button("HAC", use_container_width=True,
                         type="primary" if sel_prod=="HAC" else "secondary"):
        st.session_state["prod_sel"] = "HAC"; sel_prod = "HAC"
    if prod_col3.button("SRA", use_container_width=True,
                         type="primary" if sel_prod=="SRA" else "secondary"):
        st.session_state["prod_sel"] = "SRA"; sel_prod = "SRA"
    if prod_col4.button("CAC", use_container_width=True,
                         type="primary" if sel_prod=="CAC" else "secondary"):
        st.session_state["prod_sel"] = "CAC"; sel_prod = "CAC"

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # 빠른 검색
    st.markdown('<div style="font-size:0.75rem;color:#888;margin-bottom:6px;">빠른 검색</div>',
                unsafe_allow_html=True)
    quick_cols = st.columns(3)
    quick_terms = ["냉방불량", "소음", "누수", "냉매 충전", "알람코드", "점검주기"]
    for i, term in enumerate(quick_terms):
        if quick_cols[i % 3].button(term, key=f"q{i}", use_container_width=True):
            query = term

    if query:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        # 전체 docs (등록 문서 + 기존 txt)
        all_docs = search_docs + _get_indexed_docs()
        filtered = all_docs if sel_prod == "전체" else [
            d for d in all_docs if sel_prod in d.get("meta", {}).get("product", "")]
        results = search(query, filtered, top_k=5)

        if results:
            st.markdown(f'<div style="font-size:0.78rem;color:#1428A0;margin-bottom:8px;">'
                        f'<b>{len(results)}건</b> 검색됨</div>', unsafe_allow_html=True)
            for i, r in enumerate(results):
                score = r["score"]
                rel = ("b-blue", "관련도 높음") if score >= 4 else \
                      ("b-green", "관련도 보통") if score >= 2 else ("b-gray", "참고")
                chunk_hl = highlight(r["chunk"][:500], query)
                prod_b = f'<span class="badge b-orange">{r["product"][:3]}</span>' if r.get("product") else ""

                st.markdown(f"""
                <div class="result-card">
                  <div class="result-title">{r['title']}</div>
                  <div class="result-meta">
                    <span class="badge {rel[0]}">{rel[1]}</span>
                    {prod_b}
                    <span class="badge b-gray">{r.get('category','—')}</span>
                  </div>
                  <div class="result-chunk">{chunk_hl}</div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("전체 문서 보기"):
                    st.text(r["full_text"])
        else:
            st.markdown("""
            <div class="card">
              <div style="text-align:center;padding:20px 0;color:#aaa;">
                <div style="font-size:2rem;">🔎</div>
                <div style="font-size:0.88rem;margin-top:8px;">검색 결과가 없습니다</div>
                <div style="font-size:0.78rem;margin-top:4px;">다른 키워드로 검색하거나 문서를 등록해주세요</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        # 등록 문서 목록
        st.markdown('<div style="font-size:0.78rem;color:#888;margin-bottom:8px;">📚 등록된 기술 문서</div>',
                    unsafe_allow_html=True)
        all_docs = search_docs + _get_indexed_docs()
        for doc in all_docs:
            prod = doc.get("meta", {}).get("product", "—")
            bc = "b-blue" if "HAC" in prod else "b-green" if "SRA" in prod else \
                 "b-orange" if "CAC" in prod else "b-gray"
            title = doc.get("meta", {}).get("title", doc.get("id", "—"))
            doc_no = doc.get("meta", {}).get("doc_no", "—")
            st.markdown(f"""
            <div class="req-card">
              <span class="badge {bc}">{prod[:3] if prod!='—' else '전체'}</span>
              <span style="font-size:0.85rem;font-weight:600;">{title}</span>
              <div style="font-size:0.72rem;color:#aaa;margin-top:3px;">{doc_no}</div>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════
# TAB 2 — 문서 등록 (DocAgent)
# ════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="card-title">📄 기술 문서 등록</div>', unsafe_allow_html=True)

    # 에이전트 소개
    st.markdown("""
    <div class="card" style="background:#f4f6ff;border:1px solid #dde2ff;">
      <div style="font-size:0.78rem;color:#1428A0;">
        <b>🤖 DocAgent</b><br>
        PDF·TXT 파일을 업로드하면 자동으로 분석합니다<br>
        제품코드 · 모델명 · 고장증상 · 수리방법을 추출하여 검색 인덱스에 등록합니다
      </div>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "PDF 또는 TXT 파일 업로드",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        help="수리 가이드, 제품 사양서, 사양 변경 이력 등",
    )

    if uploaded:
        for uf in uploaded:
            st.markdown(f'<div class="card"><b>📎 {uf.name}</b> ({uf.size:,} bytes)</div>',
                        unsafe_allow_html=True)

        if st.button("📥 분석 및 등록", use_container_width=True, type="primary"):
            for uf in uploaded:
                with st.spinner(f"🤖 DocAgent 분석 중: {uf.name}"):
                    result = doc_agent.process_upload(uf.read(), uf.name)

                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success(f"✅ 등록 완료: {result['id']}")
                    st.markdown(f"""
                    <div class="card">
                      <div class="card-title">🤖 DocAgent 분석 결과</div>
                      <table style="width:100%;font-size:0.82rem;border-collapse:collapse;">
                        <tr><td style="color:#888;padding:3px 0;width:90px;">📋 문서번호</td><td><b>{result.get('doc_no','—')}</b></td></tr>
                        <tr><td style="color:#888;padding:3px 0;">📌 제목</td><td>{result.get('title','—')}</td></tr>
                        <tr><td style="color:#888;padding:3px 0;">🏷️ 제품코드</td><td><span class="badge b-blue">{result.get('product_code','—')}</span></td></tr>
                        <tr><td style="color:#888;padding:3px 0;">🔩 모델명</td><td>{result.get('model_name','—')}</td></tr>
                        <tr><td style="color:#888;padding:3px 0;">📅 출시/작성일</td><td>{result.get('release_date','—')}</td></tr>
                        <tr><td style="color:#888;padding:3px 0;">⚠️ 고장증상</td><td>{', '.join(result.get('symptoms',[]) or ['—'])}</td></tr>
                        <tr><td style="color:#888;padding:3px 0;">🔧 수리방법</td><td>{', '.join(result.get('repair_types',[]) or ['—'])}</td></tr>
                        <tr><td style="color:#888;padding:3px 0;">📝 글자수</td><td>{result.get('char_count',0):,}자</td></tr>
                      </table>
                    </div>
                    """, unsafe_allow_html=True)
            st.cache_resource.clear()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # 등록 현황
    da_stats = doc_agent.get_stats()
    st.markdown(f"""
    <div class="metric-grid">
      <div class="metric-cell">
        <div class="metric-value">{da_stats['total']}</div>
        <div class="metric-label">등록 문서</div>
      </div>
      <div class="metric-cell">
        <div class="metric-value">{len(search_docs)}</div>
        <div class="metric-label">기본 문서</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if doc_agent.index:
        st.markdown('<div style="font-size:0.78rem;color:#888;margin-bottom:6px;">최근 등록 문서</div>',
                    unsafe_allow_html=True)
        for entry in reversed(doc_agent.index[-5:]):
            pc = entry.get("product_code", "—")
            bc = "b-blue" if pc=="HAC" else "b-green" if pc=="SRA" else \
                 "b-orange" if pc=="CAC" else "b-gray"
            st.markdown(f"""
            <div class="req-card">
              <div class="req-id">{entry['id']} · {entry['registered_at']}</div>
              <div class="req-title">{entry.get('title','—')}</div>
              <span class="badge {bc}">{pc}</span>
              <span class="badge b-gray">{entry.get('model_name','—')}</span>
              <div style="font-size:0.78rem;color:#aaa;margin-top:4px;">
                증상: {', '.join(entry.get('symptoms',[]) or ['—'])}
              </div>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════
# TAB 3 — 요청 접수 (FeedbackAgent 입력)
# ════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="card-title">📸 요청 접수</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card" style="background:#f0fff4;border:1px solid #bbf7d0;">
      <div style="font-size:0.78rem;color:#1a7f3c;">
        <b>🤖 FeedbackAgent</b><br>
        사진·동영상을 첨부하여 현장 상황을 담당자에게 전달하세요<br>
        접수 후 피드백 탭에서 답변을 확인할 수 있습니다
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("req_form", clear_on_submit=True):
        name    = st.text_input("이름 *", placeholder="홍길동")
        region  = st.selectbox("지역 *",
            ["서울", "부산", "인천", "대구", "광주", "대전", "울산", "수원", "창원", "고양", "기타"])
        product = st.selectbox("제품군 *",
            ["HAC (가정용 에어컨)", "SRA (시스템 에어컨)", "CAC (상업용 에어컨)", "기타"])
        category = st.selectbox("요청 유형 *", list(CATEGORY_MAP.keys()))
        model   = st.text_input("모델명 / 부품코드", placeholder="예: AF17B6574WGN, E6 알람")
        priority = st.radio("우선순위", ["일반", "긴급 (당일 처리 요청)"], horizontal=True)
        content = st.text_area(
            "요청 내용 *",
            placeholder="증상, 조치 이력, 현재 상태 등을 상세히 작성해주세요",
            height=100,
        )
        imgs = st.file_uploader(
            "사진/동영상 첨부 (선택)",
            type=["jpg", "jpeg", "png", "gif", "webp", "mp4", "mov"],
            accept_multiple_files=True,
        )

        submitted = st.form_submit_button("📤 요청 접수", use_container_width=True, type="primary")

    if submitted:
        if not name or not content:
            st.error("이름과 요청 내용은 필수입니다.")
        else:
            req = fb_agent.create_request(
                name=name, region=region, product=product,
                category=category, priority=priority,
                model=model, content=content,
                image_files=imgs if imgs else None,
            )
            att_cnt = len(req.get("attachments", []))
            st.success(f"✅ 접수완료  |  {req['id']}")
            if att_cnt:
                st.info(f"📎 첨부파일 {att_cnt}개 저장됨")
            if "긴급" in priority:
                st.warning("🚨 긴급 요청 — 담당자에게 즉시 알림 발송")
            st.balloons()


# ════════════════════════════════════════════════════
# TAB 4 — 피드백 스레드 (FeedbackAgent 관리)
# ════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="card-title">💬 피드백 스레드</div>', unsafe_allow_html=True)

    all_reqs = fb_agent.get_all()

    if not all_reqs:
        st.markdown("""
        <div class="card" style="text-align:center;padding:30px 0;">
          <div style="font-size:2rem;">💬</div>
          <div style="font-size:0.88rem;color:#aaa;margin-top:8px;">접수된 요청이 없습니다</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 필터
        status_filter = st.selectbox(
            "상태 필터", ["전체"] + STATUS_FLOW, label_visibility="collapsed",
            key="fb_status_filter"
        )
        filtered_reqs = [r for r in all_reqs
                         if status_filter == "전체" or r["status"] == status_filter]

        for req in filtered_reqs[:10]:
            bg, tc = st_agent.status_style(req["status"])
            icon = fb_agent.get_category_icon(req["category"])
            sla_over, elapsed_h = st_agent.check_sla(req)
            att_cnt = len(req.get("attachments", []))
            fb_cnt  = len(req.get("feedback_thread", []))

            with st.expander(
                f"{icon} {req['id']}  |  {req['name']} ({req['region']})  "
                f"|  💬{fb_cnt}  📎{att_cnt}",
                expanded=False,
            ):
                # 상태 배지 + 진행 스텝
                step_html = ""
                for j, s in enumerate(STATUS_FLOW):
                    cur_idx  = STATUS_FLOW.index(req["status"])
                    if j < cur_idx:
                        cls = "step-done"
                        dot_txt = "✓"
                    elif j == cur_idx:
                        cls = "step-active"
                        dot_txt = str(j+1)
                    else:
                        cls = "step-wait"
                        dot_txt = str(j+1)
                    sep = '<div class="step-line"></div>' if j < len(STATUS_FLOW)-1 else ""
                    step_html += f"""
                    <div class="step {cls}">
                      <div class="step-dot">{dot_txt}</div>
                    </div>{sep}"""

                st.markdown(f"""
                <div class="step-bar">{step_html}</div>
                <div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:8px;">
                  <span class="badge" style="background:{bg};color:{tc};">{req['status']}</span>
                  <span class="badge {'b-red' if '긴급' in req['priority'] else 'b-gray'}">{req['priority'][:2]}</span>
                  <span class="badge b-orange">{req['product'][:3]}</span>
                  {'<span class="badge b-red">⏰ SLA 초과</span>' if sla_over else ''}
                </div>
                <div style="font-size:0.82rem;color:#444;margin-bottom:8px;">{req['content']}</div>
                """, unsafe_allow_html=True)

                # 첨부 이미지
                if req.get("attachments"):
                    thumb_html = '<div class="thumb-row">'
                    for att in req["attachments"]:
                        if att["type"] == "image" and Path(att["path"]).exists():
                            import base64
                            img_b64 = base64.b64encode(
                                Path(att["path"]).read_bytes()).decode()
                            ext = Path(att["path"]).suffix[1:]
                            thumb_html += f'<img src="data:image/{ext};base64,{img_b64}" />'
                        else:
                            thumb_html += f'<span class="badge b-gray">🎥 {att["filename"]}</span>'
                    thumb_html += '</div>'
                    st.markdown(thumb_html, unsafe_allow_html=True)

                st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

                # 피드백 스레드
                for fb in req.get("feedback_thread", []):
                    role_cls = "comment-manager" if fb["role"] == "담당자" else "comment-engineer"
                    st.markdown(f"""
                    <div class="comment {role_cls}">
                      <div class="comment-author">
                        {'👨‍💼 담당자' if fb['role'] == '담당자' else '🔧 엔지니어'} · {fb['author']}
                        <span class="comment-time">{fb['at']}</span>
                      </div>
                      {fb['message']}
                    </div>
                    """, unsafe_allow_html=True)

                # 피드백 입력
                st.markdown('<div style="font-size:0.78rem;color:#888;margin-top:8px;">피드백 추가</div>',
                            unsafe_allow_html=True)
                fb_col1, fb_col2 = st.columns([2, 1])
                fb_author = fb_col1.text_input("이름", key=f"fb_author_{req['id']}", label_visibility="collapsed",
                                                placeholder="이름")
                fb_role   = fb_col2.selectbox("역할", ["엔지니어", "담당자"],
                                               key=f"fb_role_{req['id']}", label_visibility="collapsed")
                fb_msg    = st.text_area("내용", key=f"fb_msg_{req['id']}", label_visibility="collapsed",
                                         placeholder="피드백 내용을 입력하세요", height=70)

                fbcol1, fbcol2 = st.columns(2)
                if fbcol1.button("💬 피드백 전송", key=f"fb_send_{req['id']}", use_container_width=True):
                    if fb_author and fb_msg:
                        fb_agent.add_feedback(req["id"], fb_author, fb_role, fb_msg)
                        st.success("전송 완료"); st.rerun()

                # 상태 변경
                next_s = st_agent.next_status(req["status"])
                if next_s and fbcol2.button(f"→ {next_s}", key=f"st_btn_{req['id']}", use_container_width=True):
                    fb_agent.update_status(req["id"], next_s)
                    st.success(f"상태 변경: {next_s}"); st.rerun()


# ════════════════════════════════════════════════════
# TAB 5 — 현황 대시보드 (StatusAgent)
# ════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="card-title">📊 진행 현황</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card" style="background:#fff8e1;border:1px solid #fde68a;">
      <div style="font-size:0.78rem;color:#b8860b;">
        <b>🤖 StatusAgent</b><br>
        요청 라이프사이클 · SLA 모니터링 · 처리 통계를 자동으로 관리합니다
      </div>
    </div>
    """, unsafe_allow_html=True)

    report = st_agent.build_report()

    # 핵심 메트릭
    st.markdown(f"""
    <div class="metric-grid">
      <div class="metric-cell">
        <div class="metric-value">{report['total']}</div>
        <div class="metric-label">전체 요청</div>
      </div>
      <div class="metric-cell">
        <div class="metric-value" style="color:#22c55e;">{report['resolved']}</div>
        <div class="metric-label">해결완료</div>
      </div>
      <div class="metric-cell">
        <div class="metric-value" style="color:#f59e0b;">{report['unresolved']}</div>
        <div class="metric-label">미해결</div>
      </div>
      <div class="metric-cell">
        <div class="metric-value" style="color:#ef4444;">{report['sla_breach']}</div>
        <div class="metric-label">SLA 초과</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # SLA 경보
    urgent_list = st_agent.get_urgent_list()
    if urgent_list:
        st.markdown('<div style="font-size:0.78rem;color:#ef4444;font-weight:600;margin-bottom:6px;">🚨 긴급/SLA 초과</div>',
                    unsafe_allow_html=True)
        for u in urgent_list[:3]:
            cls = "sla-over" if u["sla_over"] else "alert-banner"
            st.markdown(f"""
            <div class="{cls}">
              {'⏰' if u['sla_over'] else '🚨'} <b>{u['id']}</b>
              · {u['name']} ({u['region']}) · 경과 {u['elapsed_h']}h
              <span class="badge {'b-red' if u['sla_over'] else 'b-yellow'} ">{u['status']}</span>
            </div>
            """, unsafe_allow_html=True)

    if report["total"] > 0:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # 상태별 차트
        by_status = report["by_status"]
        if by_status:
            colors_map = {
                "접수완료": "#1428A0", "검토중": "#f59e0b",
                "피드백완료": "#22c55e", "처리중": "#3b82f6",
                "해결완료": "#16a34a", "보류": "#ef4444",
            }
            fig_s = go.Figure(go.Bar(
                x=list(by_status.keys()),
                y=list(by_status.values()),
                marker_color=[colors_map.get(k, "#999") for k in by_status],
                text=list(by_status.values()),
                textposition="outside",
            ))
            fig_s.update_layout(
                margin=dict(l=0, r=0, t=20, b=0),
                height=180,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                xaxis=dict(tickfont=dict(size=10)),
                yaxis=dict(showgrid=False, visible=False),
                font=dict(family="Noto Sans KR", size=10),
            )
            st.plotly_chart(fig_s, use_container_width=True, config={"displayModeBar": False})

        # 제품별 파이
        by_prod = report["by_product"]
        if by_prod:
            fig_p = go.Figure(go.Pie(
                labels=list(by_prod.keys()),
                values=list(by_prod.values()),
                hole=0.55,
                marker_colors=["#1428A0", "#22c55e", "#f59e0b"],
                textinfo="label+percent",
                textfont=dict(size=11),
            ))
            fig_p.update_layout(
                margin=dict(l=0, r=0, t=20, b=0),
                height=200,
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                font=dict(family="Noto Sans KR"),
            )
            st.markdown('<div style="font-size:0.78rem;color:#888;margin:4px 0;">제품군별 요청 비중</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(fig_p, use_container_width=True, config={"displayModeBar": False})

        # 해결률 + 평균 처리시간
        st.markdown(f"""
        <div class="metric-grid">
          <div class="metric-cell">
            <div class="metric-value" style="font-size:1.4rem;">{report['resolution_rate']}%</div>
            <div class="metric-label">해결률</div>
          </div>
          <div class="metric-cell">
            <div class="metric-value" style="font-size:1.4rem;">{report['avg_resolve_h']}h</div>
            <div class="metric-label">평균 처리시간</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="card" style="text-align:center;padding:30px 0;">
          <div style="font-size:2rem;">📊</div>
          <div style="font-size:0.88rem;color:#aaa;margin-top:8px;">
            아직 데이터가 없습니다<br>요청을 접수하면 통계가 표시됩니다
          </div>
        </div>
        """, unsafe_allow_html=True)

    # 전체 요청 목록 (접기)
    with st.expander(f"전체 요청 목록 ({report['total']}건)"):
        for req in fb_agent.get_all():
            bg, tc = st_agent.status_style(req["status"])
            sla_over, elapsed_h = st_agent.check_sla(req)
            st.markdown(f"""
            <div class="req-card">
              <div class="req-id">{req['id']} · {req['created_at']}</div>
              <div class="req-title">{req['name']} ({req['region']}) · {req['product'][:3]}</div>
              <span class="badge" style="background:{bg};color:{tc};">{req['status']}</span>
              {'<span class="badge b-red">⏰ SLA초과</span>' if sla_over else ''}
              <div class="req-body">{req['content'][:80]}{"..." if len(req['content'])>80 else ""}</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown('<div class="footer-space"></div>', unsafe_allow_html=True)
