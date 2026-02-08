# DART 재무제표 분석 대시보드

DART(전자공시시스템) API를 활용하여 원하는 회사의 재무제표를 검색, 수집 및 분석하는 Streamlit 대시보드입니다.

## 주요 기능

- **회사 검색**: DART 등록 회사 전체에서 원하는 회사 검색 및 선택
- **재무 데이터 수집**: 2021-2025년(최근 5년) 재무제표 자동 수집
- **인터랙티브 대시보드**:
  - 매출/영업이익 트렌드 분석
  - 수익성 지표 분석 (영업이익률, 순이익률)
  - 회사별/산업 평균 대비 분석
- **데이터 관리**: 회사 추가/제거, 캐시 관리, CSV/Excel 내보내기

## 프로젝트 구조

```
dart/
├── .env                          # API 키 설정
├── .gitignore                    # Git 제외 파일
├── README.md                     # 프로젝트 문서
├── requirements.txt              # Python 의존성
├── config.py                     # 중앙 설정 모듈
├── data/                         # 데이터 저장소
│   ├── raw/                      # 원본 API 응답
│   ├── processed/                # 가공된 CSV 파일
│   └── cache/                    # API 응답 캐시
├── src/                          # 소스 코드
│   ├── __init__.py
│   ├── dart_client.py            # DART API 클라이언트
│   ├── company_classifier.py     # 회사 분류 로직
│   ├── financial_collector.py    # 재무 데이터 수집
│   └── data_processor.py         # 데이터 가공 및 분석
├── streamlit_app.py              # Streamlit 메인 앱
└── pages/                        # Streamlit 멀티페이지
    ├── 1_회사_개요.py
    ├── 2_재무_분석.py
    └── 3_데이터_관리.py
```

## 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/minsung1013/dart_cos_supplier.git
cd dart_cos_supplier
```

### 2. 가상환경 생성 (선택사항)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env` 파일에 DART API 키를 설정합니다:

```
DART_API=your_api_key_here
```

DART API 키는 [DART Open API](https://opendart.fss.or.kr/) 사이트에서 무료로 발급받을 수 있습니다.

## 사용 방법

### 1. Streamlit 앱 실행

```bash
streamlit run streamlit_app.py
```

브라우저에서 `http://localhost:8501`로 자동 접속됩니다.

### 2. 데이터 수집

1. **데이터 관리** 페이지로 이동
2. **회사 분류 시작** 버튼 클릭 (1-5분 소요)
3. **재무 데이터 수집 시작** 버튼 클릭 (10-30분 소요)

### 3. 대시보드 탐색

- **메인 페이지**: 주요 지표 요약 및 트렌드 차트
- **회사 개요**: 분류된 회사 목록 및 통계
- **재무 분석**: 심층 재무 분석 (트렌드, 수익성, 산업 평균 비교)
- **데이터 관리**: 데이터 수집, 캐시 관리, 내보내기

## 분류 기준

### KSIC 산업 코드
- C20423: 화장품 제조업
- C20412: 기타 기초 유기화학물질 제조업
- C20411: 석유화학계 기초화합물 제조업
- C20421: 비누 및 세제 제조업
- C20422: 화장용 유지류 제조업
- C20429: 기타 화장품 제조업

### 키워드 매칭
- **고우선순위** (3점): 화장품원료, 화장품 원료, cosmetic ingredient, 기능성원료
- **중우선순위** (2점): 화장품, 색소, 향료, 피부, 스킨, 뷰티, 케미칼
- **저우선순위** (1점): 화학, 제조, chemical, 원료

### 분류 임계값
- KSIC 코드 매치: 10점
- 분류 임계값: 5점 이상

## 데이터 출처

- **DART (Data Analysis, Retrieval and Transfer System)**
  - 금융감독원 전자공시시스템 Open API
  - URL: https://opendart.fss.or.kr
  - 제공 데이터: 기업정보, 재무제표, 사업보고서

## 수집 데이터

### 재무 지표
- 매출액
- 영업이익
- 당기순이익
- 자산총계
- 부채총계
- 자본총계

### 계산 지표
- 영업이익률 = 영업이익 / 매출액 × 100
- 순이익률 = 당기순이익 / 매출액 × 100
- 부채비율 = 부채총계 / (자산총계 - 부채총계) × 100
- YoY 성장률 = (당년 - 전년) / 전년 × 100

## Streamlit Cloud 배포

### 1. Secrets 설정

Streamlit Cloud 설정에서 다음과 같이 Secrets를 추가합니다:

```toml
DART_API = "your_api_key_here"
```

### 2. 배포

1. GitHub 저장소를 Streamlit Cloud에 연결
2. Main file: `streamlit_app.py`
3. Deploy 버튼 클릭

## 커스터마이징

### 분류 기준 변경

`config.py` 파일에서 다음 설정을 수정할 수 있습니다:

```python
# KSIC 코드 추가/제거
COSMETIC_KSIC_CODES = ['C20423', 'C20412', ...]

# 키워드 추가/제거
CLASSIFICATION_KEYWORDS = {
    'high_priority': ['화장품원료', ...],
    'medium_priority': ['화장품', ...],
    'low_priority': ['화학', ...]
}

# 임계값 조정 (낮출수록 더 많은 회사 분류)
CLASSIFICATION_THRESHOLD = 5
```

### 데이터 수집 기간 변경

```python
# 수집할 연도 범위
COLLECTION_YEARS = [2021, 2022, 2023, 2024, 2025]
```

## 문제 해결

### API 키 오류
- `.env` 파일이 프로젝트 루트 디렉토리에 있는지 확인
- DART API 키가 올바르게 입력되었는지 확인

### 데이터 수집 실패
- 인터넷 연결 확인
- 캐시 삭제 후 재시도
- `dart_analysis.log` 파일에서 상세 오류 확인

### 분류된 회사가 너무 적음
- `config.py`에서 `CLASSIFICATION_THRESHOLD` 값을 낮춤
- 관련 키워드 추가

### 분류된 회사가 너무 많음
- `config.py`에서 `CLASSIFICATION_THRESHOLD` 값을 높임
- 키워드 정제

## 기술 스택

- **Python 3.9+**
- **Streamlit**: 대시보드 프레임워크
- **Pandas**: 데이터 처리
- **Plotly**: 인터랙티브 차트
- **Requests**: HTTP 통신
- **XMLtoDict**: XML 파싱

## 라이선스

MIT License

## 기여

이슈 및 풀 리퀘스트를 환영합니다!

## 작성자

- GitHub: [@minsung1013](https://github.com/minsung1013)

## 참고 자료

- [DART Open API 문서](https://opendart.fss.or.kr/guide/main.do)
- [Streamlit 문서](https://docs.streamlit.io/)
- [한국표준산업분류(KSIC)](https://kssc.kostat.go.kr/)
