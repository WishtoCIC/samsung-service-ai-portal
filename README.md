# Samsung Service AI Portal

[![GitHub](https://img.shields.io/badge/GitHub-samsung--service--ai--portal-blue?logo=github)](https://github.com/WishtoCIC/samsung-service-ai-portal)

삼성전자서비스 AI TF 사내공모 지원을 위해 개발한 프로토타입 2종입니다.

## 프로토타입 구성

### ① 서비스 수요예측 대시보드 (`service_forecast/`)
기상청 공공데이터(기온·폭염일수) × 에어컨 서비스 이력 데이터를 연계해  
월별 수요 패턴을 분석·시각화하는 대시보드.

**주요 기능**
- 제품코드(HAC·SRA·CAC)별 월별 서비스 건수 트렌드
- 지역 GPS 분포 히트맵
- 날씨 상관관계 분석 (r = 0.66)
- 불편·수리 유형 분포
- 처리시간 분포 분석 (평균 31.1h)

```bash
cd service_forecast
streamlit run app.py --server.port 8502
```

---

### ② 기술정보 통합 검색 앱 (`tech_search/`)
수리 매뉴얼·제품 사양 등 분산된 기술 자료를 통합 검색하고,  
현장 엔지니어의 요청을 관리하는 3-Agent 기반 웹 앱.

**3-Agent 구조**

| Agent | 역할 |
|---|---|
| DocAgent | PDF·TXT 업로드 → 자동 분석 → 검색 인덱스 등록 |
| FeedbackAgent | 요청 접수(사진 첨부) → 피드백 스레드 → 상태 추적 |
| StatusAgent | SLA 경보(긴급 8h / 일반 48h) → 처리 통계 |

**주요 기능**
- TF-IDF 기반 키워드 검색 + 제품군 필터
- PDF/TXT 업로드 시 제품코드·증상·수리방법 자동 추출
- 엔지니어 요청 접수 및 담당자 피드백 스레드
- SLA 모니터링 및 주간 트렌드 대시보드
- Galaxy S26 Ultra 화면 최적화 (430px 모바일 UI)

```bash
cd tech_search
streamlit run app.py --server.port 8503
```

---

## 설치

```bash
pip install streamlit pdfplumber plotly pandas
```

## 특징

- **외부 API 없이 로컬 동작** → 사내 보안 환경 즉시 적용 가능
- TF 합류 시 Gemma4 온프레미스 LLM 연동으로 확장 예정
- JSON 파일 기반 영속성 → 별도 DB 설치 불필요

## 파일 구조

```
├── tech_search/
│   ├── app.py
│   ├── search_engine.py
│   ├── agents/
│   │   ├── doc_agent.py
│   │   ├── feedback_agent.py
│   │   └── status_agent.py
│   └── docs/              # 샘플 기술문서 6종
├── service_forecast/
│   ├── app.py
│   ├── data_generator.py
│   ├── data_importer.py
│   └── data_schema.py
└── create_application.py  # 지원서 생성 스크립트
```
