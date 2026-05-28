import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Export Commercial AI",
    layout="wide"
)

st.title("Export Commercial AI")
st.subheader("Proforma Generator")

customers = pd.read_csv("data/customers/customers_master.csv")
products = pd.read_csv("data/products/products_master.csv", dtype={"sku": str})
prices = pd.read_csv("commercial/pricing/customer_price_list.csv", dtype={"sku": str})

products["sku"] = products["sku"].str.zfill(3)
prices["sku"] = prices["sku"].str.zfill(3)

country = st.selectbox(
    "Country",
    sorted(prices["country"].unique())
)

available_customers = prices[
    prices["country"] == country
]["customer"].unique()

customer = st.selectbox(
    "Customer",
    sorted(available_customers)
)

customer_prices = prices[
    (prices["country"] == country) &
    (prices["customer"] == customer)
]

st.markdown("---")
st.subheader("Products")

order_lines = []

for _, row in customer_prices.iterrows():
    sku = row["sku"]
    product = products[products["sku"] == sku].iloc[0]

    col1, col2, col3, col4 = st.columns([2, 3, 2, 2])

    with col1:
        st.write(sku)

    with col2:
        st.write(f"{product['brand']} - {product['product']}")

    with col3:
        st.write(f"CIF USD {row['price_usd']}")

    with col4:
        cases = st.number_input(
            f"Cases {sku}",
            min_value=0,
            value=0,
            step=1,
            key=f"cases_{sku}"
        )

    if cases > 0:
        order_lines.append({
            "sku": sku,
            "brand": product["brand"],
            "product": product["product"],
            "presentation": product["presentation"],
            "cases": cases,
            "price_usd": float(row["price_usd"]),
            "total_usd": cases * float(row["price_usd"])
        })

st.markdown("---")

if order_lines:
    df_order = pd.DataFrame(order_lines)
    st.subheader("Order Summary")
    st.dataframe(df_order, use_container_width=True)

    total = df_order["total_usd"].sum()
    st.metric("Total CIF USD", f"{total:,.2f}")
else:
    st.info("Select quantities to build the proforma.")