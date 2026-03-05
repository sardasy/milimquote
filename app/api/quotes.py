from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload

from app.models.database import get_db
from app.models.models import Customer, Product, Quote, QuoteItem
from app.schemas.schemas import MarginAlert, QuoteCreate, QuoteOut
from app.services import exchange_rate as rate_svc
from app.services.margin_manager import check_all_margin_alerts, calculate_pricing
from app.services.quote_generator import generate_quote_excel

router = APIRouter(prefix="/quotes", tags=["견적"])


def _next_quote_number(db: Session) -> str:
    year = datetime.utcnow().year
    count = db.query(Quote).filter(Quote.quote_number.like(f"QT-{year}-%")).count()
    return f"QT-{year}-{count + 1:04d}"


def _load_quote(db: Session, quote_id: int) -> Quote:
    quote = (
        db.query(Quote)
        .options(
            joinedload(Quote.customer),
            joinedload(Quote.exchange_rate_ref),
            joinedload(Quote.items).joinedload(QuoteItem.product),
        )
        .filter(Quote.id == quote_id)
        .first()
    )
    if not quote:
        raise HTTPException(status_code=404, detail="견적을 찾을 수 없습니다.")
    return quote


@router.post("/", response_model=QuoteOut, status_code=201)
def create_quote(body: QuoteCreate, db: Session = Depends(get_db)):
    """최신 환율로 원가·판매가를 계산하여 견적을 생성한다."""
    customer = db.get(Customer, body.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="고객을 찾을 수 없습니다.")

    latest_rate = rate_svc.get_latest_rate(db)
    if not latest_rate:
        raise HTTPException(status_code=404, detail="환율 데이터가 없습니다. /exchange-rates/refresh를 먼저 호출하세요.")

    quote = Quote(
        quote_number=_next_quote_number(db),
        customer_id=body.customer_id,
        exchange_rate_id=latest_rate.id,
        delivery_days=body.delivery_days,
        notes=body.notes,
    )
    db.add(quote)
    db.flush()  # quote.id 확보

    for item_req in body.items:
        product = db.get(Product, item_req.product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"제품 ID {item_req.product_id}를 찾을 수 없습니다.")

        pricing = calculate_pricing(product, latest_rate.exchange_rate, customer.customer_type)

        db.add(QuoteItem(
            quote_id=quote.id,
            product_id=product.id,
            quantity=item_req.quantity,
            unit_cost_krw=pricing["total_cost_krw"],
            unit_price_krw=pricing["selling_price_krw"],
            margin_rate=pricing["target_margin"],
        ))

    db.commit()
    return _load_quote(db, quote.id)


@router.get("/", response_model=list[QuoteOut])
def list_quotes(db: Session = Depends(get_db)):
    quotes = (
        db.query(Quote)
        .options(
            joinedload(Quote.customer),
            joinedload(Quote.exchange_rate_ref),
            joinedload(Quote.items).joinedload(QuoteItem.product),
        )
        .order_by(Quote.created_at.desc())
        .all()
    )
    return quotes


@router.get("/margin-alerts", response_model=list[MarginAlert])
def margin_alerts(db: Session = Depends(get_db)):
    """현재 환율 기준으로 마진 하락 알림 목록을 반환한다."""
    latest_rate = rate_svc.get_latest_rate(db)
    if not latest_rate:
        raise HTTPException(status_code=404, detail="환율 데이터가 없습니다.")

    products = db.query(Product).all()
    alerts = check_all_margin_alerts(products, latest_rate.exchange_rate)
    return alerts


@router.get("/{quote_id}", response_model=QuoteOut)
def get_quote(quote_id: int, db: Session = Depends(get_db)):
    return _load_quote(db, quote_id)


@router.get("/{quote_id}/download")
def download_quote(quote_id: int, db: Session = Depends(get_db)):
    """Excel 견적서를 다운로드한다."""
    quote = _load_quote(db, quote_id)
    excel_bytes = generate_quote_excel(quote)
    filename = f"{quote.quote_number}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
