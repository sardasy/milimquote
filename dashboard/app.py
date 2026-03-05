"""
Streamlit 내부 대시보드
실행: streamlit run dashboard/app.py
"""

import pandas as pd
import requests
import streamlit as st

API_BASE = "http://localhost:8000/api"

st.set_page_config(page_title="원가 관리 시스템", page_icon="💱", layout="wide")


# ── 공통 유틸 ─────────────────────────────────────────────────────────────────

def api_get(path: str) -> dict | list | None:
    try:
        res = requests.get(f"{API_BASE}{path}", timeout=5)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"API 오류: {e}")
        return None


def api_post(path: str, data: dict) -> dict | None:
    try:
        res = requests.post(f"{API_BASE}{path}", json=data, timeout=5)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"API 오류: {e}")
        return None


# ── 사이드바 네비게이션 ────────────────────────────────────────────────────────

page = st.sidebar.selectbox(
    "메뉴",
    ["📈 환율 현황", "📦 제품 관리", "👥 고객 관리", "📄 견적 생성", "🔔 마진 알림"],
)

# ── 페이지: 환율 현황 ─────────────────────────────────────────────────────────

if page == "📈 환율 현황":
    st.title("환율 현황 (USD/KRW)")

    col1, col2 = st.columns([2, 1])

    with col2:
        if st.button("🔄 환율 즉시 갱신", use_container_width=True):
            result = api_post("/exchange-rates/refresh", {})
            if result:
                st.success(f"갱신 완료: 1 USD = {result['exchange_rate']:,.2f} KRW")
                st.rerun()

    latest = api_get("/exchange-rates/latest")
    if latest:
        with col1:
            st.metric(
                label="현재 환율 (USD/KRW)",
                value=f"{latest['exchange_rate']:,.2f} 원",
                delta=None,
            )
            st.caption(f"업데이트: {latest['timestamp']}")

    history = api_get("/exchange-rates/history?limit=30")
    if history:
        df = pd.DataFrame(history)[["timestamp", "exchange_rate"]]
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")
        st.line_chart(df.set_index("timestamp")["exchange_rate"], height=300)

        st.subheader("환율 이력")
        df_display = df.copy()
        df_display["exchange_rate"] = df_display["exchange_rate"].map("{:,.2f}".format)
        st.dataframe(df_display.rename(columns={"timestamp": "시간", "exchange_rate": "환율(KRW)"}),
                     use_container_width=True, hide_index=True)

# ── 페이지: 제품 관리 ─────────────────────────────────────────────────────────

elif page == "📦 제품 관리":
    st.title("제품 관리")

    tab_list, tab_add, tab_price = st.tabs(["제품 목록", "제품 등록", "판매가 조회"])

    with tab_list:
        products = api_get("/products/")
        if products:
            df = pd.DataFrame(products)
            df["freight_rate"] = df["freight_rate"].map("{:.1%}".format)
            df["customs_rate"] = df["customs_rate"].map("{:.1%}".format)
            df["supplier_price_usd"] = df["supplier_price_usd"].map("$ {:,.2f}".format)
            st.dataframe(
                df[["id", "name", "supplier_price_usd", "freight_rate", "customs_rate", "description"]]
                .rename(columns={
                    "id": "ID", "name": "제품명", "supplier_price_usd": "공급가(USD)",
                    "freight_rate": "운임율", "customs_rate": "관세율", "description": "설명",
                }),
                use_container_width=True, hide_index=True,
            )

    with tab_add:
        with st.form("add_product"):
            name = st.text_input("제품명")
            supplier_price_usd = st.number_input("공급가 (USD)", min_value=0.0, step=0.01)
            freight_rate = st.slider("운임율 (%)", 0, 30, 5) / 100
            customs_rate = st.slider("관세율 (%)", 0, 30, 8) / 100
            description = st.text_area("설명")
            submitted = st.form_submit_button("등록")

        if submitted and name:
            result = api_post("/products/", {
                "name": name,
                "supplier_price_usd": supplier_price_usd,
                "freight_rate": freight_rate,
                "customs_rate": customs_rate,
                "description": description,
            })
            if result:
                st.success(f"제품 '{result['name']}' 등록 완료 (ID: {result['id']})")

    with tab_price:
        products = api_get("/products/")
        if products:
            product_map = {p["name"]: p["id"] for p in products}
            selected = st.selectbox("제품 선택", list(product_map.keys()))
            if selected and st.button("판매가 조회"):
                pricing = api_get(f"/products/{product_map[selected]}/pricing")
                if pricing:
                    st.metric("적용 환율", f"{pricing['exchange_rate']:,.2f} KRW/USD")
                    c1, c2 = st.columns(2)
                    c1.metric("기본 원가", f"{pricing['base_cost_krw']:,.0f} 원")
                    c2.metric("총 원가 (운임·관세 포함)", f"{pricing['total_cost_krw']:,.0f} 원")

                    st.subheader("고객 유형별 판매가")
                    price_df = pd.DataFrame([
                        {"고객 유형": k, "판매가(원)": f"{v:,.0f}"}
                        for k, v in pricing["prices_by_customer"].items()
                    ])
                    st.dataframe(price_df, use_container_width=True, hide_index=True)

# ── 페이지: 고객 관리 ─────────────────────────────────────────────────────────

elif page == "👥 고객 관리":
    st.title("고객 관리")

    tab_list, tab_add = st.tabs(["고객 목록", "고객 등록"])

    with tab_list:
        customers = api_get("/customers/")
        if customers:
            st.dataframe(
                pd.DataFrame(customers)[["id", "name", "customer_type", "contact_name", "contact_email"]]
                .rename(columns={
                    "id": "ID", "name": "고객사명", "customer_type": "유형",
                    "contact_name": "담당자", "contact_email": "이메일",
                }),
                use_container_width=True, hide_index=True,
            )

    with tab_add:
        with st.form("add_customer"):
            name = st.text_input("고객사명")
            customer_type = st.selectbox("고객 유형", ["대기업", "중견기업", "연구소"])
            contact_name = st.text_input("담당자명")
            contact_email = st.text_input("이메일")
            submitted = st.form_submit_button("등록")

        if submitted and name:
            result = api_post("/customers/", {
                "name": name,
                "customer_type": customer_type,
                "contact_name": contact_name,
                "contact_email": contact_email,
            })
            if result:
                st.success(f"고객사 '{result['name']}' 등록 완료")

# ── 페이지: 견적 생성 ─────────────────────────────────────────────────────────

elif page == "📄 견적 생성":
    st.title("견적 생성")

    tab_create, tab_history = st.tabs(["견적 생성", "견적 이력"])

    with tab_create:
        customers = api_get("/customers/") or []
        products = api_get("/products/") or []

        if not customers:
            st.warning("먼저 고객을 등록하세요.")
        elif not products:
            st.warning("먼저 제품을 등록하세요.")
        else:
            customer_map = {c["name"]: c["id"] for c in customers}
            product_map = {p["name"]: p["id"] for p in products}

            with st.form("create_quote"):
                selected_customer = st.selectbox("고객사", list(customer_map.keys()))
                selected_products = st.multiselect("제품 선택", list(product_map.keys()))
                quantities = {}
                for pname in selected_products:
                    quantities[pname] = st.number_input(f"{pname} 수량", min_value=1, value=1, key=pname)
                delivery_days = st.number_input("납기 (일)", min_value=1, value=30)
                notes = st.text_area("비고")
                submitted = st.form_submit_button("견적 생성")

            if submitted and selected_products:
                items = [
                    {"product_id": product_map[pname], "quantity": quantities[pname]}
                    for pname in selected_products
                ]
                result = api_post("/quotes/", {
                    "customer_id": customer_map[selected_customer],
                    "items": items,
                    "delivery_days": delivery_days,
                    "notes": notes,
                })
                if result:
                    st.success(f"견적 생성 완료: {result['quote_number']}")
                    st.info(f"Excel 다운로드: GET /api/quotes/{result['id']}/download")

    with tab_history:
        quotes = api_get("/quotes/") or []
        if quotes:
            rows = []
            for q in quotes:
                total = sum(i["unit_price_krw"] * i["quantity"] for i in q["items"])
                rows.append({
                    "견적번호": q["quote_number"],
                    "고객사": q["customer"]["name"],
                    "유형": q["customer"]["customer_type"],
                    "적용환율": f"{q['exchange_rate_ref']['exchange_rate']:,.0f}",
                    "총금액(원)": f"{total:,.0f}",
                    "생성일": q["created_at"][:10],
                    "ID": q["id"],
                })
            df = pd.DataFrame(rows)
            st.dataframe(df.drop(columns=["ID"]), use_container_width=True, hide_index=True)

            selected_id = st.selectbox("견적 선택 (Excel 다운로드)", df["ID"].tolist(),
                                       format_func=lambda i: df[df["ID"] == i]["견적번호"].values[0])
            if st.button("📥 Excel 다운로드"):
                try:
                    res = requests.get(f"{API_BASE}/quotes/{selected_id}/download", timeout=10)
                    res.raise_for_status()
                    quote_num = df[df["ID"] == selected_id]["견적번호"].values[0]
                    st.download_button(
                        label="파일 저장",
                        data=res.content,
                        file_name=f"{quote_num}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                except Exception as e:
                    st.error(f"다운로드 실패: {e}")

# ── 페이지: 마진 알림 ─────────────────────────────────────────────────────────

elif page == "🔔 마진 알림":
    st.title("마진 하락 알림")
    st.caption("목표 마진 대비 5% 이상 하락한 제품·고객 조합을 표시합니다.")

    alerts = api_get("/quotes/margin-alerts")
    if alerts is None:
        pass
    elif not alerts:
        st.success("✅ 현재 마진 하락 알림이 없습니다.")
    else:
        st.warning(f"⚠️ {len(alerts)}건의 마진 하락 알림이 있습니다.")
        df = pd.DataFrame(alerts)
        df["target_margin"] = df["target_margin"].map("{:.1%}".format)
        df["actual_margin"] = df["actual_margin"].map("{:.1%}".format)
        df["selling_price_krw"] = df["selling_price_krw"].map("{:,.0f}".format)
        st.dataframe(
            df.rename(columns={
                "product_name": "제품명", "customer_type": "고객유형",
                "target_margin": "목표마진", "actual_margin": "실제마진",
                "selling_price_krw": "현재판매가(원)",
            }).drop(columns=["product_id"]),
            use_container_width=True, hide_index=True,
        )
