import pandas as pd
from datetime import datetime

products = pd.read_csv(
    "data/products/products_master.csv",
    dtype={"sku": str}
)
products["sku"] = products["sku"].str.zfill(3)
customers = pd.read_csv("data/customers/customers_master.csv")

customer = customers.iloc[0]

order_lines = [
    {"sku": "001", "cases": 500, "price_usd": 12.50},
    {"sku": "002", "cases": 300, "price_usd": 18.75},
    {"sku": "003", "cases": 200, "price_usd": 9.90},
]

rows = []
subtotal = 0

for line in order_lines:
    product = products[products["sku"] == line["sku"]].iloc[0]

    total = line["cases"] * line["price_usd"]
    subtotal += total

    rows.append(
        f"| {line['sku']} | {product['brand']} | {product['product']} | "
        f"{product['presentation']} | {line['cases']} | "
        f"{line['price_usd']:.2f} | {total:.2f} |"
    )

date_str = datetime.now().strftime("%Y%m%d")
proforma_number = f"PF-{date_str}-001"

product_table = "\n".join(rows)

proforma_text = f"""
# PROFORMA INVOICE

## General Information

- Proforma: {proforma_number}
- Customer: {customer['customer']}
- Country: {customer['country']}
- Incoterm: {customer['incoterm']}
- Currency: {customer['currency']}
- Payment Terms: {customer['payment_terms']}

---

## Product Detail

| SKU | Brand | Product | Presentation | Cases | Price USD | Total USD |
|---|---|---|---|---:|---:|---:|
{product_table}

---

## Total

**Subtotal USD:** {subtotal:.2f}

---

## Commercial Conditions

- Prices subject to final confirmation.
- Freight not included unless specified.
- Subject to inventory availability.
- Estimated lead time: 15-20 days.
"""

output_path = f"outputs/proforma_{date_str}_001.md"

with open(output_path, "w", encoding="utf-8") as f:
    f.write(proforma_text)

print(f"Proforma generated: {output_path}")