from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.models import CustomerType, Product
from app.schemas.schemas import ProductCreate, ProductOut, ProductPricingOut
from app.services import exchange_rate as rate_svc
from app.services.margin_manager import MARGIN_TARGETS, calculate_pricing

router = APIRouter(prefix="/products", tags=["제품"])


@router.get("/", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


@router.post("/", response_model=ProductOut, status_code=201)
def create_product(body: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**body.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다.")
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, body: ProductCreate, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다.")
    for key, value in body.model_dump().items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다.")
    db.delete(product)
    db.commit()


@router.get("/{product_id}/pricing", response_model=ProductPricingOut)
def get_pricing(product_id: int, db: Session = Depends(get_db)):
    """최신 환율 기준으로 고객 유형별 판매가를 계산해 반환한다."""
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다.")

    latest = rate_svc.get_latest_rate(db)
    if not latest:
        raise HTTPException(status_code=404, detail="환율 데이터가 없습니다.")

    exchange_rate = latest.exchange_rate
    prices_by_customer = {
        ct.value: calculate_pricing(product, exchange_rate, ct)["selling_price_krw"]
        for ct in CustomerType
    }

    from app.services.cost_calculator import calculate_cost
    cost = calculate_cost(product, exchange_rate)

    return ProductPricingOut(
        product=product,
        exchange_rate=exchange_rate,
        base_cost_krw=cost["base_cost_krw"],
        total_cost_krw=cost["total_cost_krw"],
        prices_by_customer=prices_by_customer,
    )
