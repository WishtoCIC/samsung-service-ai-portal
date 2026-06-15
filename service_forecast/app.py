"""
서비스 물량 예측 대시보드 v2
샘플 데이터 / 실제 파일 업로드 선택 가능
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data_generator import generate_service_records, get_weather_df
from data_importer import read_file, column_mapping_ui, apply_mapping, show_data_preview
from data_schema import PRODUCT_CODE_MAP, COMPLAINT_TYPES, REPAIR_TYPES

st.set_page_config(
    page_title='서비스 물량 예측 대시보드',
    page_icon='🔧',
    layout='wide',
)

MONTH_LABELS = {i: f'{i}월' for i in range(1, 13)}

# ── 캐시 ──────────────────────────────────────────────
@st.cache_data
def load_sample():
    df = generate_service_records()
    df['product_label'] = df['product_code'].map(PRODUCT_CODE_MAP).fillna(df['product_code'])
    return df

@st.cache_data
def load_weather():
    return get_weather_df()

# ════════════════════════════════════════════════════
# 사이드바 — 데이터 소스 선택
# ════════════════════════════════════════════════════
with st.sidebar:
    st.title('🔧 대시보드 설정')
    st.divider()

    data_source = st.radio(
        '데이터 소스',
        ['📦 샘플 데이터', '📂 파일 업로드'],
        help='샘플 데이터는 실제 구조와 동일한 시뮬레이션 데이터입니다.'
    )

    st.divider()

    if data_source == '📦 샘플 데이터':
        service_df = load_sample()
        st.success(f'샘플 데이터 로드됨\n\n총 {len(service_df):,}건')

    else:
        uploaded = st.file_uploader(
            '서비스 이력 파일 업로드',
            type=['csv', 'xlsx', 'xls'],
            help='CSV 또는 엑셀 파일을 업로드하세요.'
        )
        if uploaded:
            raw_df = read_file(uploaded)
            if raw_df is not None:
                st.success(f'{len(raw_df):,}행 읽기 완료')
                service_df = None  # 매핑 후 설정
            else:
                service_df = load_sample()
        else:
            st.info('파일을 업로드해 주세요.\n\n업로드 전까지 샘플 데이터로 미리보기됩니다.')
            service_df = load_sample()
            uploaded = None
            raw_df = None

    st.divider()

    # 필터 (데이터 로드된 경우)
    if 'service_df' in locals() and service_df is not None and len(service_df) > 0:
        years_avail = sorted(service_df['year'].dropna().unique().astype(int).tolist())
        sel_year = st.selectbox('분석 연도', years_avail, index=len(years_avail)-1)

        prod_codes = sorted(service_df['product_code'].dropna().unique().tolist())
        sel_prod = st.multiselect(
            '제품코드',
            prod_codes,
            default=prod_codes,
            help='HAC=가정용, SRA=시스템, CAC=상업용'
        )

    st.divider()
    st.caption('📡 공공 데이터 출처')
    st.caption('• 기상청 기상자료개방포털')
    st.caption('• 행안부 주민등록 인구통계')
    st.caption('• 서비스 이력: 사내 데이터 업로드')

# ════════════════════════════════════════════════════
# 파일 업로드 — 컬럼 매핑 화면
# ════════════════════════════════════════════════════
if data_source == '📂 파일 업로드' and uploaded and raw_df is not None:
    st.title('📂 데이터 업로드 및 컬럼 매핑')
    st.caption(f'업로드 파일: **{uploaded.name}** | {len(raw_df):,}행 × {len(raw_df.columns)}열')
    st.divider()

    with st.expander('원본 파일 미리보기 (상위 5행)', expanded=True):
        st.dataframe(raw_df.head(5), use_container_width=True)

    st.divider()
    mapping = column_mapping_ui(raw_df)

    if st.button('✅ 매핑 적용 및 분석 시작', type='primary', use_container_width=True):
        mapped = apply_mapping(raw_df, mapping)
        if mapped is not None:
            st.session_state['mapped_df'] = mapped
            st.session_state['use_mapped'] = True
            st.rerun()

    if st.session_state.get('use_mapped'):
        service_df = st.session_state['mapped_df']
        show_data_preview(service_df)

    if 'service_df' not in locals() or service_df is None:
        st.stop()

# ════════════════════════════════════════════════════
# 메인 대시보드
# ════════════════════════════════════════════════════
st.title('🔧 서비스 물량 분석 대시보드')
st.caption('공공데이터(날씨·인구) × 사내 서비스 이력 — 프로세스 혁신 파일럿')

is_sample = (data_source == '📦 샘플 데이터') or not st.session_state.get('use_mapped', False)
if is_sample:
    st.info('현재 **샘플 데이터**로 표시 중입니다. 실제 데이터 업로드 후 자동으로 전환됩니다.', icon='ℹ️')

st.divider()

# 필터 적용
svc = service_df.copy()
if sel_prod:
    svc = svc[svc['product_code'].isin(sel_prod)]
svc_year = svc[svc['year'] == sel_year]

# KPI 카드
total   = len(svc_year)
peak_m  = svc_year.groupby('month').size().idxmax() if total > 0 else '-'
avg_lt  = svc_year['lead_time_hours'].mean() if 'lead_time_hours' in svc_year.columns else 0
top_cmp = svc_year['complaint_type'].value_counts().idxmax() if total > 0 else '-'

k1, k2, k3, k4 = st.columns(4)
k1.metric('연간 총 서비스 건수', f'{total:,}건')
k2.metric('최대 수요 월', f'{peak_m}월')
k3.metric('평균 처리 시간', f'{avg_lt:.1f}h')
k4.metric('최다 불편 유형', top_cmp)

st.divider()

# 탭 구성
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    '📅 월별 트렌드',
    '🗺️ 지역·GPS 분석',
    '🌡️ 날씨 상관관계',
    '🔍 불편·수리 유형',
    '⏱️ 처리시간 분석',
])

weather_df = load_weather()

# ── TAB 1: 월별 트렌드 ────────────────────────────────
with tab1:
    st.subheader(f'{sel_year}년 월별 서비스 건수 & 기온 추이')

    monthly = svc_year.groupby(['month','product_code']).size().reset_index(name='count')
    monthly_total = svc_year.groupby('month').size().reset_index(name='count')
    monthly_tmp = weather_df[weather_df['year']==sel_year].groupby('month')['avg_temp'].mean().reset_index()
    monthly_heat = weather_df[weather_df['year']==sel_year].groupby('month')['heat_days'].mean().reset_index()

    monthly_total['month_label'] = monthly_total['month'].map(MONTH_LABELS)
    merged = monthly_total.merge(monthly_tmp, on='month').merge(monthly_heat, on='month')

    fig = make_subplots(specs=[[{'secondary_y': True}]])
    colors = {'HAC': '#1f77b4', 'SRA': '#2ca02c', 'CAC': '#ff7f0e'}
    for prod in svc_year['product_code'].unique():
        d = monthly[monthly['product_code']==prod]
        d = d.set_index('month').reindex(range(1,13), fill_value=0).reset_index()
        d['month_label'] = d['month'].map(MONTH_LABELS)
        label = PRODUCT_CODE_MAP.get(prod, prod)
        fig.add_trace(go.Bar(
            x=d['month_label'], y=d['count'],
            name=f'{prod} ({label})',
            marker_color=colors.get(prod, '#999'),
            opacity=0.85,
        ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=merged['month_label'], y=merged['avg_temp'],
        name='월평균기온(℃)', mode='lines+markers',
        line=dict(color='#d62728', width=2.5), marker=dict(size=7),
    ), secondary_y=True)
    fig.add_trace(go.Scatter(
        x=merged['month_label'], y=merged['heat_days'],
        name='폭염일수(일)', mode='lines+markers',
        line=dict(color='orange', width=2, dash='dot'), marker=dict(size=6),
    ), secondary_y=True)

    fig.update_layout(
        barmode='stack', height=430,
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        plot_bgcolor='white',
    )
    fig.update_yaxes(title_text='서비스 건수', secondary_y=False, showgrid=True, gridcolor='#eee')
    fig.update_yaxes(title_text='기온(℃) / 폭염일수(일)', secondary_y=True, showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

    # 연도별 비교
    st.subheader('연도별 월별 추이 비교')
    ym = svc[svc['product_code'].isin(sel_prod)].groupby(['year','month']).size().reset_index(name='count')
    ym['month_label'] = ym['month'].map(MONTH_LABELS)
    fig2 = px.line(ym, x='month_label', y='count', color='year',
                   markers=True,
                   labels={'count':'서비스 건수','month_label':'월','year':'연도'})
    fig2.update_layout(height=340, plot_bgcolor='white')
    st.plotly_chart(fig2, use_container_width=True)

# ── TAB 2: 지역·GPS 분석 ─────────────────────────────
with tab2:
    st.subheader(f'{sel_year}년 지역별 서비스 건수 & GPS 분포')

    c1, c2 = st.columns([1, 1])

    region_cnt = svc_year.groupby('region').size().reset_index(name='count').sort_values('count', ascending=False)
    with c1:
        fig3 = px.bar(region_cnt, x='count', y='region', orientation='h',
                      color='count', color_continuous_scale='Blues',
                      labels={'count':'서비스 건수','region':'지역'},
                      title='지역별 연간 서비스 건수')
        fig3.update_layout(height=400, plot_bgcolor='white', coloraxis_showscale=False,
                           yaxis=dict(categoryorder='total ascending'))
        st.plotly_chart(fig3, use_container_width=True)

    # 지역×월 히트맵
    region_month = svc_year.groupby(['region','month']).size().reset_index(name='count')
    region_month['month_label'] = region_month['month'].map(MONTH_LABELS)
    pivot = region_month.pivot(index='region', columns='month_label', values='count').fillna(0)
    month_order = [f'{i}월' for i in range(1,13)]
    pivot = pivot[[c for c in month_order if c in pivot.columns]]
    with c2:
        fig4 = px.imshow(pivot, color_continuous_scale='YlOrRd',
                         text_auto=True, aspect='auto',
                         title='지역 × 월별 히트맵')
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)

    # GPS 산점도 지도
    st.subheader('완결 위치 GPS 분포')
    gps_df = svc_year.dropna(subset=['lat','lng'])
    if len(gps_df) > 0:
        sample_gps = gps_df.sample(min(3000, len(gps_df)), random_state=42)
        fig5 = px.scatter_mapbox(
            sample_gps,
            lat='lat', lon='lng',
            color='product_code',
            color_discrete_map={'HAC':'#1f77b4','SRA':'#2ca02c','CAC':'#ff7f0e'},
            hover_data=['product_name','complaint_type','repair_type'],
            zoom=6, height=480,
            labels={'product_code':'제품코드'},
            title=f'서비스 완결 위치 (최대 3,000건 표시)',
        )
        fig5.update_layout(mapbox_style='open-street-map')
        fig5.update_layout(margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info('GPS 데이터가 없습니다.')

# ── TAB 3: 날씨 상관관계 ─────────────────────────────
with tab3:
    st.subheader('날씨 지표 × 서비스 건수 상관분석')

    month_svc = svc_year.groupby('month').size().reset_index(name='service_count')
    month_weather = weather_df[weather_df['year']==sel_year].groupby('month').agg(
        avg_temp=('avg_temp','mean'), heat_days=('heat_days','mean')
    ).reset_index()
    corr_base = month_svc.merge(month_weather, on='month')

    c3, c4 = st.columns(2)
    with c3:
        fig6 = px.scatter(corr_base, x='avg_temp', y='service_count',
                          trendline='ols', text='month',
                          labels={'avg_temp':'월평균기온(℃)','service_count':'서비스 건수'},
                          title='월평균기온 vs 서비스 건수')
        fig6.update_traces(textposition='top center')
        fig6.update_layout(height=380, plot_bgcolor='white')
        st.plotly_chart(fig6, use_container_width=True)

    with c4:
        fig7 = px.scatter(corr_base, x='heat_days', y='service_count',
                          trendline='ols', text='month',
                          labels={'heat_days':'폭염일수(일)','service_count':'서비스 건수'},
                          title='폭염일수 vs 서비스 건수')
        fig7.update_traces(textposition='top center')
        fig7.update_layout(height=380, plot_bgcolor='white')
        st.plotly_chart(fig7, use_container_width=True)

    corr_temp = corr_base['service_count'].corr(corr_base['avg_temp'])
    corr_heat = corr_base['service_count'].corr(corr_base['heat_days'])
    m1, m2 = st.columns(2)
    m1.metric('기온 상관계수', f'{corr_temp:.3f}')
    m2.metric('폭염일수 상관계수', f'{corr_heat:.3f}')

# ── TAB 4: 불편·수리 유형 ─────────────────────────────
with tab4:
    st.subheader(f'{sel_year}년 고객불편 유형 및 수리유형 분석')

    c5, c6 = st.columns(2)
    with c5:
        cmp_cnt = svc_year['complaint_type'].value_counts().reset_index()
        cmp_cnt.columns = ['유형','건수']
        fig8 = px.pie(cmp_cnt, values='건수', names='유형',
                      title='고객불편 유형 분포',
                      color_discrete_sequence=px.colors.qualitative.Set3)
        fig8.update_traces(textposition='inside', textinfo='percent+label')
        fig8.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig8, use_container_width=True)

    with c6:
        rep_cnt = svc_year['repair_type'].value_counts().reset_index()
        rep_cnt.columns = ['유형','건수']
        fig9 = px.bar(rep_cnt, x='건수', y='유형', orientation='h',
                      color='건수', color_continuous_scale='Greens',
                      title='수리유형별 건수')
        fig9.update_layout(height=400, plot_bgcolor='white',
                           coloraxis_showscale=False,
                           yaxis=dict(categoryorder='total ascending'))
        st.plotly_chart(fig9, use_container_width=True)

    # 제품코드 × 불편유형 크로스탭
    st.subheader('제품코드 × 고객불편 유형 크로스탭')
    cross = pd.crosstab(svc_year['product_code'], svc_year['complaint_type'])
    fig10 = px.imshow(cross, text_auto=True, aspect='auto',
                      color_continuous_scale='Blues',
                      title='제품코드별 불편유형 분포')
    fig10.update_layout(height=300)
    st.plotly_chart(fig10, use_container_width=True)

# ── TAB 5: 처리시간 분석 ──────────────────────────────
with tab5:
    st.subheader(f'{sel_year}년 서비스 처리시간 분석')

    if 'lead_time_hours' not in svc_year.columns:
        st.info('처리시간 데이터가 없습니다. (접수/완료 일시 필요)')
    else:
        c7, c8 = st.columns(2)
        with c7:
            fig11 = px.histogram(svc_year, x='lead_time_hours',
                                 nbins=30, color='product_code',
                                 labels={'lead_time_hours':'처리시간(시간)','count':'건수'},
                                 title='처리시간 분포 (시간)')
            fig11.update_layout(height=380, plot_bgcolor='white')
            st.plotly_chart(fig11, use_container_width=True)

        with c8:
            lt_by_prod = svc_year.groupby('product_code')['lead_time_hours'].agg(
                평균='mean', 중앙값='median', 최대='max'
            ).round(1).reset_index()
            lt_by_prod.columns = ['제품코드','평균(h)','중앙값(h)','최대(h)']
            st.dataframe(lt_by_prod, use_container_width=True, hide_index=True)

            lt_by_cmp = svc_year.groupby('complaint_type')['lead_time_hours'].mean().round(1).sort_values(ascending=False)
            fig12 = px.bar(lt_by_cmp.reset_index(), x='lead_time_hours', y='complaint_type',
                           orientation='h', color='lead_time_hours',
                           color_continuous_scale='Reds',
                           labels={'lead_time_hours':'평균 처리시간(h)','complaint_type':'불편유형'},
                           title='불편유형별 평균 처리시간')
            fig12.update_layout(height=320, plot_bgcolor='white', coloraxis_showscale=False,
                                yaxis=dict(categoryorder='total ascending'))
            st.plotly_chart(fig12, use_container_width=True)

        # 월별 평균 처리시간 추이
        lt_monthly = svc_year.groupby('month')['lead_time_hours'].mean().reset_index()
        lt_monthly['month_label'] = lt_monthly['month'].map(MONTH_LABELS)
        fig13 = px.line(lt_monthly, x='month_label', y='lead_time_hours',
                        markers=True,
                        labels={'lead_time_hours':'평균 처리시간(h)','month_label':'월'},
                        title='월별 평균 처리시간 추이')
        fig13.update_layout(height=300, plot_bgcolor='white')
        st.plotly_chart(fig13, use_container_width=True)
