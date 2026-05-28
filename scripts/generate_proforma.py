import pandas as pd
from datetime import datetime

products = pd.read_csv(
    "data/products/products_master.csv",
    dtype={"sku": str}
)

products["sku"] = products["sku"].str.zfill(3)

customers = pd.read_csv(
    "data/customers/customers_master.csv"
)

prices = pd.read_csv(
    "commercial/pricing/customer_price_list.csv",
    dtype={"sku": str}
)

prices["sku"] = prices["sku"].str.zfill(3)

COUNTRY = "Aruba"
CUSTOMER_NAME = "Super Food Aruba"

customer_match = customers[
    customers["customer"] == CUSTOMER_NAME
]

if customer_match.empty:
    raise ValueError(
        f"Customer not found: {CUSTOMER_NAME}"
    )

customer = customer_match.iloc[0]
customer_name = customer["customer"]

order_lines = [
    {"sku": "001", "cases": 500},
    {"sku": "002", "cases": 300},
    {"sku": "003", "cases": 200},
]

rows = []
subtotal = 0

for line in order_lines:

    sku = line["sku"]

    product_match = products[
        products["sku"] == sku
    ]

    price_match = prices[
        (prices["country"] == COUNTRY) &
        (prices["customer"] == customer_name) &
        (prices["sku"] == sku)
    ]

    if product_match.empty:
        raise ValueError(
            f"SKU not found: {sku}"
        )

    if price_match.empty:
        raise ValueError(
            f"Price not found for {customer_name} | {sku}"
        )

    product = product_match.iloc[0]

    price_usd = float(
        price_match.iloc[0]["price_usd"]
    )

    total = line["cases"] * price_usd

    subtotal += total

    rows.append(
        f"| {sku} | "
        f"{product['brand']} | "
        f"{product['product']} | "
        f"{product['presentation']} | "
        f"{line['cases']} | "
        f"{price_usd:.2f} | "
        f"{total:.2f} |"
    )

date_str = datetime.now().strftime("%Y%m%d")

from pathlib import Path

output_dir = Path("outputs")
output_dir.mkdir(exist_ok=True)

existing_files = list(
    output_dir.glob(f"proforma_{date_str}_*.md")
)

next_number = len(existing_files) + 1

sequence = str(next_number).zfill(3)

proforma_number = f"PF-{date_str}-{sequence}"

product_table = "\n".join(rows)

proforma_text = f"""
# PROFORMA INVOICE

## General Information

- Proforma: {proforma_number}
- Customer: {customer['customer']}
- Country: {COUNTRY}
- Incoterm: CIF
- Currency: USD
- Payment Terms: {customer['payment_terms']}

---

## Product Detail

| SKU | Brand | Product | Presentation | Cases | CIF Unit Price USD | CIF Total USD |
|---|---|---|---|---:|---:|---:|
{product_table}

---

## Total

**Total CIF USD:** {subtotal:.2f}

---

## Commercial Conditions

- Prices are CIF and already include freight and insurance.
- Prices subject to final confirmation.
- Subject to inventory availability.
"""

output_path = (
    f"outputs/proforma_{date_str}_{sequence}.md"
)

with open(
    output_path,
    "w",
    encoding="utf-8"
) as f:

    f.write(proforma_text)

print(
    f"Proforma generated: {output_path}"
)