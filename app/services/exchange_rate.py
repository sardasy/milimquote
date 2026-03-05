import logging

import requests
from sqlalchemy.orm import Session

from app.config import settings
from app.models.models import ExchangeRate

logger = logging.getLogger(__name__)


def fetch_usd_krw_rate() -> float:
    """exchangerate.host API에서 USD/KRW 환율을 가져온다."""
    response = requests.get(
        settings.EXCHANGE_RATE_API_URL,
        params={"base": "USD", "symbols": "KRW"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    if not data.get("success", True):  # 일부 버전은 success 필드 없음
        raise ValueError(f"API 오류: {data}")

    rate = data["rates"]["KRW"]
    logger.info("환율 수신: 1 USD = %.2f KRW", rate)
    return rate


def update_exchange_rate(db: Session) -> ExchangeRate:
    """최신 환율을 API에서 받아 DB에 저장하고 반환한다."""
    rate = fetch_usd_krw_rate()
    record = ExchangeRate(currency_pair="USD/KRW", exchange_rate=rate)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_latest_rate(db: Session) -> ExchangeRate | None:
    """DB에서 가장 최근 USD/KRW 환율 레코드를 반환한다."""
    return (
        db.query(ExchangeRate)
        .filter(ExchangeRate.currency_pair == "USD/KRW")
        .order_by(ExchangeRate.timestamp.desc())
        .first()
    )


def get_rate_history(db: Session, limit: int = 30) -> list[ExchangeRate]:
    """최근 환율 이력을 반환한다."""
    return (
        db.query(ExchangeRate)
        .filter(ExchangeRate.currency_pair == "USD/KRW")
        .order_by(ExchangeRate.timestamp.desc())
        .limit(limit)
        .all()
    )
