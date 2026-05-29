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

    pipeline_summary = (
        pipeline_df
        .groupby("status", dropna=False)
        .agg(
            proformas=("proforma_number", "count"),
            total_cif_usd=("total_cif_usd", "sum"),
            final_value_usd=("final_value_usd", "sum")
        )
        .reset_index()
    )

    pipeline_summary = pipeline_summary.rename(
        columns={
            "status": "Status",
            "proformas": "Proformas",
            "total_cif_usd": "Pipeline USD",
            "final_value_usd": "Forecast USD"
        }
    )

    st.dataframe(
        pipeline_summary,
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

st.markdown("---")
st.subheader("✏️ Update Proforma Status")

if history_path.exists():

    history_df_edit = pd.read_excel(
        history_path,
        dtype={
            "status": str,
            "delivered_to_customer": str,
            "comments": str
        }
    )

    for col in ["status", "delivered_to_customer", "comments"]:
        history_df_edit[col] = (
            history_df_edit[col]
            .fillna("")
            .astype(str)
        )

    if "final_value_usd" not in history_df_edit.columns:
        history_df_edit["final_value_usd"] = 0.0

    history_df_edit["final_value_usd"] = (
        pd.to_numeric(
            history_df_edit["final_value_usd"],
            errors="coerce"
        )
        .fillna(0.0)
    )
    selected_proforma = st.selectbox(
        "Select Proforma",
        history_df_edit["proforma_number"].dropna().unique()
    )

    selected_row = history_df_edit[
        history_df_edit["proforma_number"] == selected_proforma
    ].iloc[0]

    status_options = ["Draft", "Sent", "Approved", "Rejected", "Closed"]
    delivered_options = ["No", "Yes"]

    current_status = selected_row.get("status", "Draft")
    if pd.isna(current_status) or current_status not in status_options:
        current_status = "Draft"

    current_delivered = selected_row.get("delivered_to_customer", "No")
    if pd.isna(current_delivered) or current_delivered not in delivered_options:
        current_delivered = "No"

    current_final_value = selected_row.get("final_value_usd", 0)
    if pd.isna(current_final_value):
        current_final_value = 0

    current_comments = selected_row.get("comments", "")
    if pd.isna(current_comments):
        current_comments = ""

    col_status, col_delivered, col_value = st.columns(3)

    with col_status:
        new_status = st.selectbox(
            "Status",
            status_options,
            index=status_options.index(current_status),
            key="update_status"
        )

    with col_delivered:
        new_delivered = st.selectbox(
            "Delivered?",
            delivered_options,
            index=delivered_options.index(current_delivered),
            key="update_delivered"
        )

    with col_value:
        new_final_value = st.number_input(
            "Final Value USD",
            min_value=0.0,
            value=float(current_final_value),
            step=100.0,
            key="update_final_value"
        )

    new_comments = st.text_area(
        "Comments",
        value=str(current_comments),
        key="update_comments"
    )

    if st.button("Update Proforma Status"):

        mask = history_df_edit["proforma_number"] == selected_proforma

        history_df_edit.loc[mask, "status"] = str(new_status)
        history_df_edit.loc[mask, "delivered_to_customer"] = str(new_delivered)
        history_df_edit.loc[mask, "final_value_usd"] = new_final_value
        history_df_edit.loc[mask, "comments"] = str(new_comments)
        
        history_df_edit.to_excel(
            history_path,
            index=False
        )

        st.success(
            f"Proforma {selected_proforma} updated."
        )

else:
    st.info("No history available to update.")   

st.markdown("---")
st.subheader("📈 Commercial Pipeline")

if history_path.exists():

    pipeline_df = pd.read_excel(history_path)

    pipeline_df["status"] = (
        pipeline_df["status"]
        .fillna("Draft")
        .replace("None", "Draft")
    )

    pipeline_df["final_value_usd"] = (
        pd.to_numeric(
            pipeline_df["final_value_usd"],
            errors="coerce"
        )
        .fillna(
            pipeline_df["total_cif_usd"]
        )
    )
    pipeline_summary = (
        pipeline_df
        .groupby("status", dropna=False)
        .agg(
            proformas=("proforma_number", "count"),
            total_cif_usd=("total_cif_usd", "sum"),
            final_value_usd=("final_value_usd", "sum")
        )
        .reset_index()
    )

    pipeline_summary = pipeline_summary.rename(
        columns={
            "status": "Status",
            "proformas": "Proformas",
            "total_cif_usd": "Pipeline USD",
            "final_value_usd": "Forecast USD"
        }
    )

    st.dataframe(
            pipeline_summary,
            width="stretch"
    )
    closed_value = pipeline_df[
            pipeline_df["status"] == "Closed"
    ]["final_value_usd"].sum()

    total_pipeline = pipeline_df[
            pipeline_df["status"].isin(
                ["Draft", "Sent", "Approved", "Closed"]
    )
    ]["final_value_usd"].sum()

    closed_count = len(
            pipeline_df[pipeline_df["status"] == "Closed"]
    )

    approved_sent_count = len(
            pipeline_df[
                pipeline_df["status"].isin(
                    ["Sent", "Approved", "Closed"]
                )
            ]
    )

    win_rate = (
            closed_count / approved_sent_count * 100
            if approved_sent_count > 0
            else 0
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
            "Pipeline USD",
            f"${total_pipeline:,.0f}"
    )

    col2.metric(
            "Closed USD",
            f"${closed_value:,.0f}"
    )

    col3.metric(
            "Win Rate",
            f"{win_rate:.1f}%"
    )

else:

   st.info(
        "No history available for pipeline."
)     
