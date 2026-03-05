import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.database import Base


class CustomerType(str, enum.Enum):
    LARGE_CORP = "대기업"
    MID_CORP = "중견기업"
    RESEARCH = "연구소"


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    currency_pair = Column(String(10), nullable=False)  # e.g. "USD/KRW"
    exchange_rate = Column(Float, nullable=False)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    customer_type = Column(Enum(CustomerType), nullable=False)
    contact_name = Column(String(50))
    contact_email = Column(String(100))

    quotes = relationship("Quote", back_populates="customer")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    supplier_price_usd = Column(Float, nullable=False)
    freight_rate = Column(Float, default=0.05)   # 운임율 (기본 5%)
    customs_rate = Column(Float, default=0.08)   # 관세율 (기본 8%)
    description = Column(Text)

    quote_items = relationship("QuoteItem", back_populates="product")


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    quote_number = Column(String(20), unique=True, nullable=False)  # e.g. QT-2026-0001
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    exchange_rate_id = Column(Integer, ForeignKey("exchange_rates.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    delivery_days = Column(Integer, default=30)
    notes = Column(Text)

    customer = relationship("Customer", back_populates="quotes")
    exchange_rate_ref = relationship("ExchangeRate")
    items = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")


class QuoteItem(Base):
    __tablename__ = "quote_items"

    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_cost_krw = Column(Float, nullable=False)   # 총 원가/개
    unit_price_krw = Column(Float, nullable=False)  # 판매가/개
    margin_rate = Column(Float, nullable=False)      # 적용 마진율

    quote = relationship("Quote", back_populates="items")
    product = relationship("Product", back_populates="quote_items")
