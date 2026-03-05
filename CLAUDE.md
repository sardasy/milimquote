# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# 의존성 설치
pip install -r requirements.txt

# FastAPI 백엔드 실행 (포트 8000)
uvicorn app.main:app --reload

# Streamlit 대시보드 실행 (포트 8501)
streamlit run dashboard/app.py

# API 문서
open http://localhost:8000/docs
```

## Architecture

```
환율 API → ExchangeRate DB → 원가 계산 → 마진 조정 → 견적 생성(Excel)
```

**백엔드** (`app/`): FastAPI + SQLAlchemy 2.0 + PostgreSQL
**대시보드** (`dashboard/app.py`): Streamlit이 `http://localhost:8000/api`를 직접 호출

### 데이터 흐름

1. **환율 수집**: `app/services/exchange_rate.py` → `POST /api/exchange-rates/refresh`로 즉시 갱신 가능. `app/main.py`의 APScheduler가 `EXCHANGE_RATE_UPDATE_INTERVAL`(기본 3600초)마다 자동 갱신.

2. **원가 계산** (`app/services/cost_calculator.py`):
   - `원가(KRW) = 공급가(USD) × 환율`
   - `총 원가 = 원가 × (1 + 운임율 + 관세율)`
   - `판매가 = 총 원가 / (1 - 목표 마진율)`

3. **마진 관리** (`app/services/margin_manager.py`):
   - 고객 유형별 목표 마진: 대기업 18% / 중견기업 25% / 연구소 35%
   - 환율 변동 시 판매가는 항상 최신 환율로 재계산 (저장된 고정가격 없음)
   - 목표 마진 대비 5% 이상 하락 시 `margin_alert=True` 반환

4. **견적 생성** (`app/services/quote_generator.py`): `Quote` ORM 객체를 받아 openpyxl로 Excel bytes 반환. `GET /api/quotes/{id}/download`로 직접 다운로드.

### 핵심 모델 관계

```
Customer (1) ──── (N) Quote (N) ──── (N) QuoteItem (N) ──── (1) Product
                       │
                       └── ExchangeRate  ← 견적 생성 시점의 환율 스냅샷
```

Quote는 생성 시점의 `exchange_rate_id`를 고정 저장하여 과거 견적의 환율을 보존한다.

### 환경 설정

`.env` 파일 생성 (`.env.example` 참고):
```
DATABASE_URL=postgresql://user:password@localhost:5432/pricing_db
EXCHANGE_RATE_UPDATE_INTERVAL=3600
```

앱 시작 시 `Base.metadata.create_all()`로 테이블이 자동 생성된다.
