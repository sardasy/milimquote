from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.models import CustomerType


# ── ExchangeRate ──────────────────────────────────────────────────────────────

class ExchangeRateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    currency_pair: str
    exchange_rate: float


# ── Customer ──────────────────────────────────────────────────────────────────

class CustomerCreate(BaseModel):
    name: str
    customer_type: CustomerType
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None


class CustomerOut(CustomerCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


# ── Product ───────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    name: str
    supplier_price_usd: float
    freight_rate: float = 0.05
    customs_rate: float = 0.08
    description: Optional[str] = None


class ProductOut(ProductCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ProductPricingOut(BaseModel):
    """원가 및 고객 유형별 판매가 계산 결과"""
    product: ProductOut
    exchange_rate: float
    base_cost_krw: float      # 기본 원가 (USD × 환율)
    total_cost_krw: float     # 총 원가 (운임·관세 포함)
    prices_by_customer: dict  # CustomerType → selling_price


# ── Quote ─────────────────────────────────────────────────────────────────────

class QuoteItemCreate(BaseModel):
    product_id: int
    quantity: int


class QuoteCreate(BaseModel):
    customer_id: int
    items: list[QuoteItemCreate]
    delivery_days: int = 30
    notes: Optional[str] = None


class QuoteItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product: ProductOut
    quantity: int
    unit_cost_krw: float
    unit_price_krw: float
    margin_rate: float

    @property
    def total_price_krw(self) -> float:
        return self.unit_price_krw * self.quantity


class QuoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quote_number: str
    customer: CustomerOut
    exchange_rate_ref: ExchangeRateOut
    created_at: datetime
    delivery_days: int
    notes: Optional[str]
    items: list[QuoteItemOut]


# ── Margin alert ──────────────────────────────────────────────────────────────

class MarginAlert(BaseModel):
    product_id: int
    product_name: str
    customer_type: CustomerType
    target_margin: float
    actual_margin: float
    selling_price_krw: float
