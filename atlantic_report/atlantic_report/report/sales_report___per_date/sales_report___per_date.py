import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)

    data = add_currency_totals(data)

    return columns, data


def get_columns():
    return [
        {"label": "Date", "fieldname": "date", "fieldtype": "Data", "width": 100},
        {"label": "Ccy", "fieldname": "currency", "fieldtype": "Data", "width": 60},
        {"label": "No of DO", "fieldname": "no_of_do", "fieldtype": "Int", "width": 90},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "options": "currency", "width": 120},
        {"label": "Tax", "fieldname": "tax", "fieldtype": "Currency", "options": "currency", "width": 120},
        {"label": "Disc", "fieldname": "disc", "fieldtype": "Currency", "options": "currency", "width": 120},
        {"label": "Total", "fieldname": "grand_total", "fieldtype": "Currency", "options": "currency", "width": 130}
    ]


def get_data(filters):
    sql = """
        SELECT
            DATE_FORMAT(dn.posting_date, '%%d-%%b-%%y') AS date,
            dn.currency AS currency,
            COUNT(dn.name) AS no_of_do,
            SUM(dn.total) AS amount,
            SUM(dn.total_taxes_and_charges) AS tax,
            SUM(dn.discount_amount) AS disc,
            SUM(dn.grand_total) AS grand_total

        FROM
            `tabDelivery Note` dn
        WHERE
            dn.docstatus = 1
            AND dn.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY
            dn.posting_date, dn.currency
        ORDER BY
            dn.posting_date ASC
    """

    return frappe.db.sql(sql, filters, as_dict=True)


# ======================================================
# TAMBAHKAN TOTAL PER CURRENCY (Total (IDR), Total (USD))
# ======================================================
def add_currency_totals(data):
    if not data:
        return data

    totals = {}
    result = []

    # Akumulasi total per currency
    for row in data:
        ccy = row.currency

        if ccy not in totals:
            totals[ccy] = {"no_of_do": 0, "amount": 0, "tax": 0, "disc": 0, "grand_total": 0}

        totals[ccy]["no_of_do"] += row.no_of_do or 0
        totals[ccy]["amount"] += row.amount or 0
        totals[ccy]["tax"] += row.tax or 0
        totals[ccy]["disc"] += row.disc or 0
        totals[ccy]["grand_total"] += row.grand_total or 0

        result.append(row)

    # Tambahkan baris total
    for ccy, total in totals.items():
        result.append({
            "date": f"Total ({ccy})",    # Label sesuai permintaan
            "currency": ccy,
            "no_of_do": total["no_of_do"],
            "amount": total["amount"],
            "tax": total["tax"],
            "disc": total["disc"],
            "grand_total": total["grand_total"],
            "is_total_row": 1            # Agar HTML auto-bold
        })

    return result
