import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from app.config import settings
from app.models.database import SessionLocal, engine
from app.models.models import Base
from app.services.exchange_rate import update_exchange_rate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _scheduled_rate_update():
    """스케줄러에서 주기적으로 호출되는 환율 업데이트 함수."""
    db = SessionLocal()
    try:
        record = update_exchange_rate(db)
        logger.info("스케줄 환율 업데이트 완료: %s = %.2f", record.currency_pair, record.exchange_rate)
    except Exception as e:
        logger.error("스케줄 환율 업데이트 실패: %s", e)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 테이블 생성
    Base.metadata.create_all(bind=engine)
    logger.info("데이터베이스 테이블 초기화 완료")

    # 환율 자동 수집 스케줄러 시작
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _scheduled_rate_update,
        trigger="interval",
        seconds=settings.EXCHANGE_RATE_UPDATE_INTERVAL,
        id="exchange_rate_update",
    )
    scheduler.start()
    logger.info("환율 스케줄러 시작 (간격: %d초)", settings.EXCHANGE_RATE_UPDATE_INTERVAL)

    yield

    scheduler.shutdown()
    logger.info("환율 스케줄러 종료")


app = FastAPI(
    title="수입 원가 관리 & 견적 자동화 시스템",
    description="환율 연동 원가 계산, 마진 관리, 견적서 자동 생성",
    version="1.0.0",
    lifespan=lifespan,
)

from app.api import customers, exchange_rates, products, quotes  # noqa: E402

app.include_router(exchange_rates.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(customers.router, prefix="/api")
app.include_router(quotes.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
