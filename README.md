# MilimQuote

환율 변동에 따라 수입 원가를 자동 계산하고, 목표 마진을 유지하도록 판매가를 자동 조정하며, 고객 견적서를 자동 생성하는 시스템입니다.

## 프로세스

```
환율 API → 원가 자동 계산 → 마진 자동 조정 → 견적 자동 생성 (Excel)
```

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | Python 3.11, FastAPI |
| Dashboard | Streamlit |
| Database | PostgreSQL, SQLAlchemy |
| 주요 라이브러리 | requests, pandas, pydantic, openpyxl, jinja2 |

## 시작하기

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 데이터베이스 정보를 입력합니다.

```env
DATABASE_URL=postgresql://user:password@localhost:5432/pricing_db
EXCHANGE_RATE_UPDATE_INTERVAL=3600
```

### 3. 실행

```bash
# FastAPI 백엔드 (포트 8000)
uvicorn app.main:app --reload

# Streamlit 대시보드 (포트 8501)
streamlit run dashboard/app.py
```

### 4. 첫 환율 수집

```bash
curl -X POST http://localhost:8000/api/exchange-rates/refresh
```

API 문서: http://localhost:8000/docs

## 주요 기능

### 환율 자동 수집
- USD/KRW 환율을 외부 API에서 주기적으로 자동 수집 (기본 1시간)
- `/api/exchange-rates/refresh`로 즉시 갱신 가능

### 원가 자동 계산
```
원가(KRW) = 공급가(USD) × 환율
총 원가   = 원가 × (1 + 운임율 + 관세율)
판매가    = 총 원가 / (1 - 목표 마진율)
```

### 고객 유형별 마진 관리

| 고객 유형 | 목표 마진 |
|-----------|-----------|
| 대기업 | 18% |
| 중견기업 | 25% |
| 연구소 | 35% |

환율 변동 시 판매가 자동 재계산, 목표 마진 대비 5%p 이상 하락 시 알림

### 견적서 자동 생성
- Excel 형식 견적서 자동 생성
- `GET /api/quotes/{id}/download`로 다운로드

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/exchange-rates/latest` | 최신 환율 조회 |
| POST | `/api/exchange-rates/refresh` | 환율 즉시 갱신 |
| GET | `/api/exchange-rates/history` | 환율 이력 |
| GET/POST | `/api/products/` | 제품 목록·등록 |
| GET | `/api/products/{id}/pricing` | 고객 유형별 판매가 |
| GET/POST | `/api/customers/` | 고객 목록·등록 |
| POST | `/api/quotes/` | 견적 생성 |
| GET | `/api/quotes/{id}/download` | Excel 견적서 다운로드 |
| GET | `/api/quotes/margin-alerts` | 마진 하락 알림 |
