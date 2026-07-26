import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)

    data = add_subtotals(data)  # subtotal sesuai HTML (bold)

    return columns, data


def get_columns():
    return [
        {"label": "DO No.", "fieldname": "do_no", "fieldtype": "Link", "options": "Delivery Note", "width": 120},
        {"label": "Date", "fieldname": "date", "fieldtype": "Data", "width": 90},
        {"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 260},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 90},
        {"label": "Ccy", "fieldname": "currency", "fieldtype": "Data", "width": 55},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "options": "currency", "width": 120},
        {"label": "Tax", "fieldname": "tax", "fieldtype": "Currency", "options": "currency", "width": 120},
        {"label": "Disc", "fieldname": "disc", "fieldtype": "Currency", "options": "currency", "width": 120},
        {"label": "Total", "fieldname": "grand_total", "fieldtype": "Currency", "options": "currency", "width": 130}
    ]


def get_data(filters):
    sql = """
        SELECT
            dn.name AS do_no,
            DATE_FORMAT(dn.posting_date, '%%d-%%b-%%y') AS date,
            dn.customer_name,
            dn.status,
            dn.currency,
            dn.total AS amount,
            dn.total_taxes_and_charges AS tax,
            dn.discount_amount AS disc,
            dn.grand_total

        FROM
            `tabDelivery Note` AS dn
        WHERE
            dn.docstatus = 1
            AND dn.is_return = 0
            AND dn.posting_date BETWEEN %(from_date)s AND %(to_date)s
        ORDER BY
            dn.name ASC
    """

    return frappe.db.sql(sql, filters, as_dict=True)


# ======================================================
# SUBTOTAL PER CURRENCY → AGAR BOLD DI HTML
# ======================================================
def add_subtotals(data):
    if not data:
        return data

    subtotal_map = {}
    result = []

    # Hitung subtotal per currency
    for row in data:
        ccy = row.currency

        if ccy not in subtotal_map:
            subtotal_map[ccy] = {"amount": 0, "tax": 0, "disc": 0, "grand_total": 0}

        subtotal_map[ccy]["amount"] += row.amount or 0
        subtotal_map[ccy]["tax"] += row.tax or 0
        subtotal_map[ccy]["disc"] += row.disc or 0
        subtotal_map[ccy]["grand_total"] += row.grand_total or 0

        result.append(row)

    # Tambahkan subtotal → gunakan "is_total_row" agar HTML bold
    for ccy, totals in subtotal_map.items():
        result.append({
            "do_no": f"Total ({ccy})",
            "date": "",
            "customer_name": "",
            "status": "",
            "currency": ccy,
            "amount": totals["amount"],
            "tax": totals["tax"],
            "disc": totals["disc"],
            "grand_total": totals["grand_total"],

            # HTML akan otomatis bold baris ini
            "is_total_row": 1  
        })

    return result
