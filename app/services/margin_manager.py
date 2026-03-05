from app.models.models import CustomerType, Product
from app.services.cost_calculator import calculate_cost, calculate_selling_price

# 고객 유형별 목표 마진율
MARGIN_TARGETS: dict[CustomerType, float] = {
    CustomerType.LARGE_CORP: 0.18,  # 대기업 18%
    CustomerType.MID_CORP:   0.25,  # 중견기업 25%
    CustomerType.RESEARCH:   0.35,  # 연구소 35%
}

# 목표 마진 대비 이 수치 이상 하락 시 알림
MARGIN_ALERT_DROP = 0.05


def get_target_margin(customer_type: CustomerType) -> float:
    return MARGIN_TARGETS[customer_type]


def calculate_pricing(
    product: Product,
    exchange_rate: float,
    customer_type: CustomerType,
) -> dict:
    """
    제품·환율·고객유형을 받아 원가, 판매가, 마진 정보를 반환한다.
    환율이 변동되면 자동으로 판매가가 재계산된다.
    """
    cost_info = calculate_cost(product, exchange_rate)
    target_margin = get_target_margin(customer_type)
    selling_price = calculate_selling_price(cost_info["total_cost_krw"], target_margin)

    actual_margin = (selling_price - cost_info["total_cost_krw"]) / selling_price
    margin_alert = actual_margin < (target_margin - MARGIN_ALERT_DROP)

    return {
        **cost_info,
        "customer_type": customer_type,
        "target_margin": target_margin,
        "selling_price_krw": selling_price,
        "actual_margin": round(actual_margin, 4),
        "margin_alert": margin_alert,
    }


def check_all_margin_alerts(products: list[Product], exchange_rate: float) -> list[dict]:
    """모든 제품·고객유형 조합에서 마진 하락 알림 목록을 반환한다."""
    alerts = []
    for product in products:
        for customer_type in CustomerType:
            result = calculate_pricing(product, exchange_rate, customer_type)
            if result["margin_alert"]:
                alerts.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "customer_type": customer_type,
                    "target_margin": result["target_margin"],
                    "actual_margin": result["actual_margin"],
                    "selling_price_krw": result["selling_price_krw"],
                })
    return alerts
