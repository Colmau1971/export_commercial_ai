import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import markdown
from weasyprint import HTML
import warnings

warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="openpyxl"
)

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

purchase_order = st.text_input(
    "Orden de compra del cliente",
    placeholder="Ej: OC-12345"
)

customer_row = customers[
    customers["Cliente"] == customer
].iloc[0]

lista_p = customer_row["LISTA_PRECIOS"]

customer_prices = prices[
    prices["LISTA_PRECIOS"] == lista_p
]

st.markdown("### Customer Information")

col1, col2 = st.columns(2)

with col1:
    st.write(f"**Customer:** {customer_row['Cliente']}")
    st.write(f"**NIF:** {customer_row['NIF:']}")

with col2:
    st.write(f"**Contact:** {customer_row['Contacto:']}")
    st.write(f"**Phone:** {customer_row['NUMERO']}")

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
            f"CIF USD {float(row['Precio CIF']):,.2f}"
        )

    with col4:
        cases = st.number_input(
            f"Cases {sku}",
            min_value=0,
            value=0,
            step=1,
            key=f"cases_{sku}_{row['ORIGEN']}"
        )

    if cases > 0:

        price_usd = float(row["Precio CIF"])

        order_lines.append({
            "sku": sku,
            "brand": row["MARCA"],
            "product": row["Descripcion"],
            "origin": row["ORIGEN"],
            "presentation": str(row["GRAMOS"]),
            "cases": cases,
            "price_usd": price_usd,
            "total_usd": cases * price_usd
        })

st.markdown("---")

if order_lines:

    df_order = pd.DataFrame(order_lines)

    orders_by_origin = {
        origin: data
        for origin, data in df_order.groupby("origin")
    }

    origins = df_order["origin"].unique()

    if len(origins) > 1:
        st.warning(
            f"Multiple origins detected: {', '.join(origins)}. "
            "Separate proformas will be generated."
        )

    st.subheader("Order Summary")

    st.dataframe(
        df_order,
        width="stretch"
    )

    total = df_order["total_usd"].sum()

    st.metric(
        "TOTAL CIF USD",
        f"${total:,.2f}"
    )
    st.markdown("---")
    st.subheader("Commercial Tracking")

    col1, col2, col3 = st.columns(3)

    with col1:
        proforma_status = st.selectbox(
            "Status",
            ["Draft", "Sent", "Approved", "Rejected", "Closed"]
        )

    with col2:
        delivered_to_customer = st.selectbox(
            "Delivered?",
            ["No", "Yes"]
        )

    with col3:
        final_value_usd = st.number_input(
            "Final Value USD",
            min_value=0.0,
            value=float(total),
            step=100.0
        )

    commercial_comments = st.text_area(
        "Comments",
        placeholder="Ej: Sent by email, pending customer approval..."
    )
    if st.button("Generate Proforma PDF"):

        if not purchase_order:
            st.error(
                "Debes ingresar la orden de compra del cliente."
            )
            st.stop()

        date_str = datetime.now().strftime("%Y%m%d")

        output_dir = Path("outputs")
        pdf_dir = Path("outputs/pdf")

        output_dir.mkdir(exist_ok=True)
        pdf_dir.mkdir(exist_ok=True)

        existing_files = list(
            output_dir.glob(f"proforma_{date_str}_*.md")
        )

        base_sequence = len(existing_files) + 1

        generated_files = []
        st.session_state["generated_files"] = []
       

        for index, (origin, origin_df) in enumerate(
            orders_by_origin.items(),
            start=0
        ):

            sequence = str(
                base_sequence + index
            ).zfill(3)

            origin_clean = (
                str(origin)
                .replace(" ", "_")
                .replace("/", "-")
                .upper()
            )

            proforma_number = (
                f"PF-{date_str}-{sequence}-{origin_clean}"
            )

            origin_total = origin_df["total_usd"].sum()

            rows_md = []

            for _, row in origin_df.iterrows():

                rows_md.append(
                    f"| {row['sku']} | "
                    f"{row['brand']} | "
                    f"{row['product']} | "
                    f"{row['origin']} | "
                    f"{row['presentation']} | "
                    f"{row['cases']:,} | "
                    f"{row['price_usd']:,.2f} | "
                    f"{row['total_usd']:,.2f} |"
                )

            product_table = "\n".join(rows_md)

            proforma_text = f"""
# PROFORMA INVOICE

## General Information

- Proforma: {proforma_number}
- Customer: {customer}
- Customer PO: {purchase_order}
- NIF: {customer_row['NIF:']}
- Contact: {customer_row['Contacto:']}
- Phone: {customer_row['NUMERO']}
- Origin: {origin}
- Price List: {lista_p}
- Incoterm: CIF
- Currency: USD

---

## Product Detail

| SKU | Brand | Product | Origin | Presentation | Cases | CIF Unit Price USD | CIF Total USD |
|---|---|---|---|---|---:|---:|---:|
{product_table}

---

## Total

**Total CIF USD:** {origin_total:,.2f}

---

## Commercial Conditions

- Prices are CIF and already include freight and insurance.
- Prices subject to final confirmation.
- Subject to inventory availability.
"""

            md_output_path = (
                f"outputs/proforma_{date_str}_{sequence}_{origin_clean}.md"
            )

            pdf_output_path = (
                f"outputs/pdf/proforma_{date_str}_{sequence}_{origin_clean}.pdf"
            )

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

            logo_uri = Path(
                "assets/logo.png"
            ).resolve().as_uri()

            html_content = f"""
<html>
<head>
<style>

@page {{
    size: A4 landscape;
    margin: 20px;
}}

body {{
    font-family: Arial, sans-serif;
    padding: 20px;
    color: #222;
    font-size: 11px;
    line-height: 1.2;
}}

.logo {{
    width: 140px;
    margin-bottom: 10px;
}}

h1 {{
    color: #003B75;
    font-size: 24px;
    margin-bottom: 8px;
}}

h2 {{
    color: #003B75;
    font-size: 16px;
    margin-top: 12px;
    margin-bottom: 6px;
}}

p {{
    margin: 2px 0;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
}}

th {{
    background-color: #003B75;
    color: white;
    padding: 6px;
    border: 1px solid #ccc;
}}

td {{
    padding: 5px;
    font-size: 10px;
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

            generated_files.append({
                "proforma_number": proforma_number,
                "pdf_output_path": pdf_output_path,
                "origin": origin
            })

            history_dir = Path("outputs/history")
            history_dir.mkdir(exist_ok=True)

            history_path = history_dir / "proformas_log.xlsx"

        
            log_row = pd.DataFrame([{
                "date": date_str,
                "proforma_number": proforma_number,
                "customer": customer,
                "purchase_order": purchase_order,
                "origin": origin,
                "price_list": lista_p,
                "total_cif_usd": origin_total,

                "status": proforma_status,
                "delivered_to_customer": delivered_to_customer,
                "final_value_usd": final_value_usd,
                "comments": commercial_comments,

                "pdf_file": pdf_output_path
            }])
            if history_path.exists():
                existing_log = pd.read_excel(history_path)
                updated_log = pd.concat(
                    [existing_log, log_row],
                    ignore_index=True
                )
            else:
                updated_log = log_row

            updated_log.to_excel(
                history_path,
                index=False
            )

        st.session_state["generated_files"] = generated_files

        st.success(
            f"{len(generated_files)} proforma(s) generated."
        )
    if "generated_files" in st.session_state:

        st.markdown("### Generated Proformas")

        for generated in st.session_state["generated_files"]:

            with open(
                generated["pdf_output_path"],
                "rb"
            ) as pdf_file:

                st.download_button(
                    label=f"Download PDF - {generated['origin']}",
                    data=pdf_file,
                    file_name=f"{generated['proforma_number']}.pdf",
                    mime="application/pdf",
                    key=f"download_{generated['proforma_number']}_{generated['origin']}"
                )
    
st.markdown("---")
st.subheader("📊 Proforma History")
history_path = Path(
        "outputs/history/proformas_log.xlsx"
)
if history_path.exists():

    history_df = pd.read_excel(history_path)

    history_df = history_df.rename(columns={
        "date": "Fecha",
        "proforma_number": "Proforma",
        "customer": "Cliente",
        "purchase_order": "OC Cliente",
        "origin": "Origen",
        "price_list": "Lista Precio",
        "total_cif_usd": "Total CIF USD",

        "status": "Status",
        "delivered_to_customer": "Delivered",
        "final_value_usd": "Final Value USD",
        "comments": "Comments",

        "pdf_file": "Archivo PDF"
    })
    customer_filter = st.selectbox(
        "Customer Filter",
        ["All"] + sorted(
            history_df["Cliente"]
            .dropna()
            .unique()
            .tolist()
        )
    )

    if customer_filter != "All":
        history_df = history_df[
            history_df["Cliente"] == customer_filter
        ]

    col1, col2, col3 = st.columns(3)

    col1.metric("Proformas", len(history_df))
    col2.metric("Customers", history_df["Cliente"].nunique())
    col3.metric(
        "USD Generated",
        f"${history_df['Total CIF USD'].sum():,.0f}"
    )
    with open(history_path, "rb") as history_file:
        st.download_button(
            label="⬇️ Download History Excel",
            data=history_file,
            file_name="proformas_log.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    st.dataframe(
        history_df.sort_values(
            by="Fecha",
            ascending=False
        ),
        width="stretch"
    )

else:
    st.info("No proforma history yet. Generate a proforma first.")