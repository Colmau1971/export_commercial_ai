import pandas as pd
from datetime import datetime

# LOAD DATA
products = pd.read_csv(
    "data/products/products_master.csv"
)

customers = pd.read_csv(
    "data/customers/customers_master.csv"
)

# SAMPLE SELECTION
product = products.iloc[0]
customer = customers.iloc[0]

# BASIC VALUES
cases = 500
price = 12.50

total = cases * price

# PROFORMA NUMBER
date_str = datetime.now().strftime("%Y%m%d")

proforma_text = f"""
# PROFORMA INVOICE

## General Information

- Proforma: PF-{date_str}-001
- Customer: {customer['customer']}
- Country: {customer['country']}
- Incoterm: {customer['incoterm']}
- Currency: USD

---

## Product Detail

| Product | Cases | Price USD | Total USD |
|---|---:|---:|---:|
| {product['product']} | {cases} | {price} | {total} |

---

## Total

USD {total}
"""

output_path = (
    f"outputs/proforma_{date_str}_001.md"
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