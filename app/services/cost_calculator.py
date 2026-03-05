from app.models.models import Product


def calculate_cost(product: Product, exchange_rate: float) -> dict:
    """
    원가(KRW) = 공급가(USD) × 환율
    총 원가   = 원가 × (1 + 운임율 + 관세율)
    """
    base_cost_krw = product.supplier_price_usd * exchange_rate
    total_cost_krw = base_cost_krw * (1 + product.freight_rate + product.customs_rate)

    return {
        "base_cost_krw": round(base_cost_krw),
        "total_cost_krw": round(total_cost_krw),
        "exchange_rate": exchange_rate,
        "freight_rate": product.freight_rate,
        "customs_rate": product.customs_rate,
    }


def calculate_selling_price(total_cost_krw: float, target_margin: float) -> float:
    """
    판매가 = 총 원가 / (1 - 목표 마진율)
    """
    if not (0 < target_margin < 1):
        raise ValueError(f"마진율은 0~1 사이여야 합니다: {target_margin}")
    return round(total_cost_krw / (1 - target_margin))
