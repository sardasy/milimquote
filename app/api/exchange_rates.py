from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.schemas.schemas import ExchangeRateOut
from app.services import exchange_rate as svc

router = APIRouter(prefix="/exchange-rates", tags=["환율"])


@router.get("/latest", response_model=ExchangeRateOut)
def get_latest(db: Session = Depends(get_db)):
    """DB에 저장된 최신 환율을 반환한다."""
    rate = svc.get_latest_rate(db)
    if not rate:
        raise HTTPException(status_code=404, detail="환율 데이터가 없습니다. /refresh를 먼저 호출하세요.")
    return rate


@router.post("/refresh", response_model=ExchangeRateOut)
def refresh(db: Session = Depends(get_db)):
    """API에서 최신 환율을 즉시 수집하여 저장한다."""
    try:
        return svc.update_exchange_rate(db)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"환율 API 호출 실패: {e}")


@router.get("/history", response_model=list[ExchangeRateOut])
def history(limit: int = 30, db: Session = Depends(get_db)):
    """최근 환율 이력을 반환한다."""
    return svc.get_rate_history(db, limit=limit)
