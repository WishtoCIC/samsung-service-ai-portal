"""
샘플 데이터 생성기 — 실제 서비스 데이터 구조와 동일한 컬럼으로 생성
실제 파일 업로드 시 이 데이터는 대체됩니다.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_schema import (
    COMPLAINT_TYPES, REPAIR_TYPES, REGION_GPS,
    PRODUCT_CODE_MAP
)

PRODUCT_NAMES = {
    'HAC': ['비스포크 무풍에어컨 2in1', '삼성 무풍에어컨 스탠드', '삼성 벽걸이 에어컨', '무풍갤러리 에어컨'],
    'SRA': ['시스템에어컨 4way', '시스템에어컨 덕트형', '삼성 천장형 에어컨', '시스템에어컨 1way'],
    'CAC': ['DVM S2 인버터', '삼성 중형냉방기', 'DVM Eco2 시스템', '삼성 패키지에어컨'],
}

# 월별 기본 서비스 건수 (제품별, 계절성 반영)
MONTHLY_BASE = {
    'HAC': [8,  10,  20,  45, 120, 380, 820, 780, 220, 40, 12,  8],
    'SRA': [15, 18,  25,  40,  80, 180, 350, 330, 140, 50, 20, 15],
    'CAC': [20, 22,  30,  55, 100, 210, 400, 380, 160, 60, 25, 18],
}

# 시간대별 접수 비율 (업무시간 집중)
HOUR_WEIGHTS = [
    0.01,0.01,0.01,0.01,0.01,0.02,  # 0-5시
    0.03,0.05,0.08,0.10,0.10,0.09,  # 6-11시
    0.08,0.09,0.10,0.09,0.08,0.07,  # 12-17시
    0.06,0.05,0.03,0.02,0.01,0.01   # 18-23시
]

def random_dt(year: int, month: int) -> datetime:
    import random
    day = random.randint(1, 28)
    hour = random.choices(range(24), weights=HOUR_WEIGHTS)[0]
    minute = random.randint(0, 59)
    return datetime(year, month, day, hour, minute)

def random_gps(region: str) -> tuple:
    lat_c, lng_c, r = REGION_GPS[region]
    lat = lat_c + np.random.uniform(-r, r)
    lng = lng_c + np.random.uniform(-r, r)
    return round(lat, 6), round(lng, 6)

def generate_service_records(years=(2022, 2023, 2024), seed=42) -> pd.DataFrame:
    np.random.seed(seed)
    rows = []
    regions = list(REGION_GPS.keys())
    pop_weights = [9.4, 3.35, 2.96, 2.43, 1.49, 1.47, 1.14, 1.20, 1.04, 1.08]

    for year in years:
        for month in range(1, 13):
            for prod_code, monthly_base in MONTHLY_BASE.items():
                base = monthly_base[month - 1]
                # 연도별 성장률 (2022→2024 약 15% 증가)
                growth = 1 + (year - 2022) * 0.07
                total = max(1, int(base * growth))

                for _ in range(total):
                    region = np.random.choice(regions, p=[w/sum(pop_weights) for w in pop_weights])
                    prod_name = np.random.choice(PRODUCT_NAMES[prod_code])
                    complaint = np.random.choice(
                        COMPLAINT_TYPES,
                        p=[0.35, 0.20, 0.12, 0.10, 0.08, 0.10, 0.05]
                    )
                    repair = np.random.choice(
                        REPAIR_TYPES,
                        p=[0.25, 0.20, 0.18, 0.12, 0.15, 0.05, 0.05]
                    )
                    receipt_dt = random_dt(year, month)
                    # 완료까지 1~5일 소요
                    lead_hours = np.random.choice(
                        [4, 8, 24, 48, 72, 96, 120],
                        p=[0.10, 0.25, 0.30, 0.20, 0.10, 0.03, 0.02]
                    )
                    complete_dt = receipt_dt + timedelta(hours=int(lead_hours))
                    lat, lng = random_gps(region)

                    rows.append({
                        'product_code':   prod_code,
                        'product_name':   prod_name,
                        'receipt_dt':     receipt_dt,
                        'complete_dt':    complete_dt,
                        'complaint_type': complaint,
                        'repair_type':    repair,
                        'lat':            lat,
                        'lng':            lng,
                        'region':         region,
                        'year':           year,
                        'month':          month,
                    })

    df = pd.DataFrame(rows)
    df['lead_time_hours'] = (
        (df['complete_dt'] - df['receipt_dt'])
        .dt.total_seconds() / 3600
    ).round(1)
    return df


def get_weather_df(years=(2022, 2023, 2024)):
    """월별 지역 기상 데이터 (기상청 API 구조 동일)"""
    regions = list(REGION_GPS.keys())
    MONTHLY_BASE_TEMP = {
        1:-2.0,2:0.5,3:7.0,4:13.5,5:19.0,6:23.5,
        7:27.5,8:28.0,9:22.0,10:15.0,11:7.5,12:0.5
    }
    MONTHLY_HEAT_DAYS = {
        1:0,2:0,3:0,4:0,5:0.5,6:3.0,
        7:12.0,8:14.0,9:1.5,10:0,11:0,12:0
    }
    rows = []
    for year in years:
        for region in regions:
            lat_c = REGION_GPS[region][0]
            lat_f = (37.57 - lat_c) * 0.4
            for month in range(1, 13):
                rows.append({
                    'year': year, 'month': month, 'region': region,
                    'avg_temp': round(MONTHLY_BASE_TEMP[month] + lat_f + np.random.normal(0, 1.2), 1),
                    'heat_days': round(max(0, MONTHLY_HEAT_DAYS[month] + lat_f * 0.5 + np.random.normal(0, 1.5)), 1),
                })
    return pd.DataFrame(rows)


if __name__ == '__main__':
    df = generate_service_records()
    print(f'총 레코드: {len(df):,}건')
    print(df.head(3).to_string())
    print('\n제품코드별 건수:')
    print(df.groupby(['product_code','year'])['product_code'].count().unstack())
