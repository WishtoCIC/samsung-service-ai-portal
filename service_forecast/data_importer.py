"""
파일 업로드 및 컬럼 매핑 모듈
CSV / XLSX 파일을 읽어 내부 스키마로 변환
"""
import pandas as pd
import streamlit as st
from data_schema import REQUIRED_COLUMNS, AUTO_DETECT, PRODUCT_CODE_MAP


def detect_column(df_cols: list, field: str) -> str:
    """키워드 매칭으로 컬럼 자동 감지"""
    keywords = AUTO_DETECT.get(field, [])
    for col in df_cols:
        for kw in keywords:
            if kw.lower() in col.lower():
                return col
    return df_cols[0]


def read_file(uploaded_file) -> pd.DataFrame | None:
    """업로드된 파일을 DataFrame으로 읽기"""
    try:
        name = uploaded_file.name.lower()
        if name.endswith('.csv'):
            # 인코딩 자동 감지 (UTF-8, EUC-KR 시도)
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='euc-kr')
        elif name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            st.error('CSV 또는 XLSX 파일만 지원합니다.')
            return None
        return df
    except Exception as e:
        st.error(f'파일 읽기 오류: {e}')
        return None


def column_mapping_ui(df: pd.DataFrame) -> dict | None:
    """컬럼 매핑 UI — 자동 감지 후 수동 수정 가능"""
    cols = list(df.columns)
    st.subheader('📋 컬럼 매핑')
    st.caption('업로드된 파일의 컬럼을 분석 항목에 연결해 주세요. 자동으로 감지한 값을 확인 후 수정하세요.')

    mapping = {}
    col1, col2 = st.columns(2)

    fields = list(REQUIRED_COLUMNS.items())
    half = len(fields) // 2

    for i, (field, label) in enumerate(fields):
        default = detect_column(cols, field)
        default_idx = cols.index(default) if default in cols else 0
        target_col = col1 if i < half else col2
        with target_col:
            mapping[field] = st.selectbox(
                label,
                options=cols,
                index=default_idx,
                key=f'map_{field}'
            )

    return mapping


def apply_mapping(df: pd.DataFrame, mapping: dict) -> pd.DataFrame | None:
    """매핑 적용 후 내부 스키마로 변환"""
    try:
        result = pd.DataFrame()

        for internal_col, source_col in mapping.items():
            result[internal_col] = df[source_col]

        # 일시 파싱
        for dt_col in ['receipt_dt', 'complete_dt']:
            if result[dt_col].dtype == object:
                result[dt_col] = pd.to_datetime(result[dt_col], errors='coerce')

        # GPS 숫자 변환
        result['lat'] = pd.to_numeric(result['lat'], errors='coerce')
        result['lng'] = pd.to_numeric(result['lng'], errors='coerce')

        # 파생 컬럼 추가
        result['year']  = result['receipt_dt'].dt.year
        result['month'] = result['receipt_dt'].dt.month
        result['lead_time_hours'] = (
            (result['complete_dt'] - result['receipt_dt'])
            .dt.total_seconds() / 3600
        ).round(1)

        # 제품코드 레이블
        result['product_label'] = result['product_code'].map(PRODUCT_CODE_MAP).fillna(result['product_code'])

        # 결측치 리포트
        null_counts = result.isnull().sum()
        critical_nulls = null_counts[null_counts > 0]
        if not critical_nulls.empty:
            st.warning(f'결측치 발견: {critical_nulls.to_dict()}')

        return result

    except Exception as e:
        st.error(f'데이터 변환 오류: {e}')
        return None


def show_data_preview(df: pd.DataFrame):
    """데이터 미리보기 및 품질 리포트"""
    st.subheader('📊 데이터 미리보기')

    m1, m2, m3, m4 = st.columns(4)
    m1.metric('총 레코드', f'{len(df):,}건')
    m2.metric('제품 종류', f"{df['product_code'].nunique()}개")

    if 'year' in df.columns:
        year_range = f"{df['year'].min()}~{df['year'].max()}"
        m3.metric('기간', year_range)

    if 'lead_time_hours' in df.columns:
        avg_lead = df['lead_time_hours'].mean()
        m4.metric('평균 처리시간', f'{avg_lead:.1f}h')

    st.dataframe(df.head(10), use_container_width=True)

    with st.expander('컬럼별 데이터 타입 및 결측치 현황'):
        info_df = pd.DataFrame({
            '타입': df.dtypes.astype(str),
            '결측치': df.isnull().sum(),
            '결측률': (df.isnull().sum() / len(df) * 100).round(1).astype(str) + '%',
            '고유값 수': df.nunique(),
        })
        st.dataframe(info_df, use_container_width=True)
