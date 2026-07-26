import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)

    data = add_currency_totals(data)

    return columns, data


def get_columns():
    return [
        {"label": "Sales Person", "fieldname": "sales_person", "fieldtype": "Link", "options": "Sales Person", "width": 200},
        {"label": "Ccy", "fieldname": "currency", "fieldtype": "Data", "width": 60},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "options": "currency", "width": 120},
        {"label": "Tax", "fieldname": "tax", "fieldtype": "Currency", "options": "currency", "width": 120},
        {"label": "Disc", "fieldname": "disc", "fieldtype": "Currency", "options": "currency", "width": 120},
        {"label": "Total", "fieldname": "grand_total", "fieldtype": "Currency", "options": "currency", "width": 130}
    ]


def get_data(filters):
    sql = """
        SELECT
            st.sales_person AS sales_person,
            dn.currency AS currency,
            SUM(dn.total) AS amount,
            SUM(dn.total_taxes_and_charges) AS tax,
            SUM(dn.discount_amount) AS disc,
            SUM(dn.grand_total) AS grand_total
        FROM
            `tabDelivery Note` AS dn
        INNER JOIN
            (
                SELECT DISTINCT parent, sales_person
                FROM `tabSales Team`
                WHERE parenttype = 'Delivery Note'
            ) AS st ON st.parent = dn.name
        WHERE
            dn.docstatus = 1
            AND dn.is_return = 0
            AND dn.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY
            st.sales_person, dn.currency
        ORDER BY
            sales_person ASC
    """

    return frappe.db.sql(sql, filters, as_dict=True)


# ======================================================
# ADD TOTAL PER CURRENCY → AGAR BOLD + BACKGROUND DI HTML
# ======================================================
def add_currency_totals(data):
    if not data:
        return data

    totals = {}
    result = []

    for row in data:
        ccy = row.currency

        if ccy not in totals:
            totals[ccy] = {"amount": 0, "tax": 0, "disc": 0, "grand_total": 0}

        totals[ccy]["amount"] += row.amount or 0
        totals[ccy]["tax"] += row.tax or 0
        totals[ccy]["disc"] += row.disc or 0
        totals[ccy]["grand_total"] += row.grand_total or 0

        result.append(row)

    # Tambahkan row total per currency
    for ccy, total in totals.items():
        result.append({
            "sales_person": f"Total ({ccy})",
            "currency": ccy,
            "amount": total["amount"],
            "tax": total["tax"],
            "disc": total["disc"],
            "grand_total": total["grand_total"],
            "is_total_row": 1   # HTML akan bold + background #fafafa
        })

    return result
