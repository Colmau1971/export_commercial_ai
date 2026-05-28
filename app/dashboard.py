import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import markdown
from weasyprint import HTML

st.set_page_config(
    page_title="Export Commercial AI",
    layout="wide"
)

st.title("Export Commercial AI")
st.subheader("Proforma Generator")

excel_file = "data/Factura Proforma.xlsx"

customers = pd.read_excel(
    excel_file,
    sheet_name="Clientes"
)

prices = pd.read_excel(
    excel_file,
    sheet_name="Precios"
)

prices["CODIGO"] = (
    prices["CODIGO"]
    .astype(str)
    .str.zfill(3)
)

available_customers = customers["Cliente"].dropna().unique()

customer = st.selectbox(
    "Customer",
    sorted(available_customers)
)

customer_row = customers[
    customers["Cliente"] == customer
].iloc[0]

lista_p = customer_row["LISTA P"]

customer_prices = prices[
    prices["LISTA"] == lista_p
]

st.markdown("---")
st.subheader("Products")

order_lines = []

for _, row in customer_prices.iterrows():

    sku = row["CODIGO"]

    col1, col2, col3, col4 = st.columns(
        [2, 4, 2, 2]
    )

    with col1:
        st.write(sku)

    with col2:
        st.write(
            f"{row['MARCA']} - {row['Descripcion']}"
        )

    with col3:
        st.write(
            f"CIF USD {row['Precio CIF']}"
        )

    with col4:
        cases = st.number_input(
            f"Cases {sku}",
            min_value=0,
            value=0,
            step=1,
            key=f"cases_{sku}"
        )

    if cases > 0:

        price_usd = float(row["Precio CIF"])

        order_lines.append({
            "sku": sku,
            "brand": row["MARCA"],
            "product": row["Descripcion"],
            "presentation": f"{row['GRAMOS']} g",
            "cases": cases,
            "price_usd": price_usd,
            "total_usd": cases * price_usd
        })

st.markdown("---")

if order_lines:

    df_order = pd.DataFrame(order_lines)

    st.subheader("Order Summary")

    st.dataframe(
        df_order,
        width="stretch"
    )

    total = df_order["total_usd"].sum()

    st.metric(
        "Total CIF USD",
        f"{total:,.2f}"
    )

    if st.button("Generate Proforma PDF"):

        date_str = datetime.now().strftime("%Y%m%d")

        output_dir = Path("outputs")
        pdf_dir = Path("outputs/pdf")

        output_dir.mkdir(exist_ok=True)
        pdf_dir.mkdir(exist_ok=True)

        existing_files = list(
            output_dir.glob(f"proforma_{date_str}_*.md")
        )

        sequence = str(len(existing_files) + 1).zfill(3)

        proforma_number = f"PF-{date_str}-{sequence}"

        rows_md = []

        for _, row in df_order.iterrows():

            rows_md.append(
                f"| {row['sku']} | "
                f"{row['brand']} | "
                f"{row['product']} | "
                f"{row['presentation']} | "
                f"{row['cases']} | "
                f"{row['price_usd']:.2f} | "
                f"{row['total_usd']:.2f} |"
            )

        product_table = "\n".join(rows_md)

        proforma_text = f"""
# PROFORMA INVOICE

## General Information

- Proforma: {proforma_number}
- Customer: {customer}
- Customer Price List: {lista_p}
- Incoterm: CIF
- Currency: USD

---

## Product Detail

| SKU | Brand | Product | Presentation | Cases | CIF Unit Price USD | CIF Total USD |
|---|---|---|---|---:|---:|---:|
{product_table}

---

## Total

**Total CIF USD:** {total:,.2f}

---

## Commercial Conditions

- Prices are CIF and already include freight and insurance.
- Prices subject to final confirmation.
- Subject to inventory availability.
"""

        md_output_path = f"outputs/proforma_{date_str}_{sequence}.md"
        pdf_output_path = f"outputs/pdf/proforma_{date_str}_{sequence}.pdf"

        with open(
            md_output_path,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(proforma_text)

        html_body = markdown.markdown(
            proforma_text,
            extensions=["tables"]
        )

        logo_uri = Path("assets/logo.png").resolve().as_uri()

        html_content = f"""
<html>
<head>
<style>
body {{
    font-family: Arial, sans-serif;
    padding: 40px;
    color: #222;
}}
.logo {{
    width: 220px;
    margin-bottom: 30px;
}}
h1, h2 {{
    color: #003B75;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
}}
th {{
    background-color: #003B75;
    color: white;
    padding: 10px;
    border: 1px solid #ccc;
}}
td {{
    padding: 8px;
    border: 1px solid #ccc;
}}
strong {{
    font-size: 18px;
}}
</style>
</head>
<body>
<img src="{logo_uri}" class="logo">
{html_body}
</body>
</html>
"""

        HTML(
            string=html_content,
            base_url="."
        ).write_pdf(pdf_output_path)

        st.success(
            f"Proforma generated: {proforma_number}"
        )

        with open(pdf_output_path, "rb") as pdf_file:

            st.download_button(
                label="Download PDF",
                data=pdf_file,
                file_name=f"{proforma_number}.pdf",
                mime="application/pdf"
            )

else:

    st.info(
        "Select quantities to build the proforma."
    )