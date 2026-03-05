import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)

    data = add_currency_totals(data)

    return columns, data


def get_columns():
    return [
        {"label": "DO No.", "fieldname": "do_no", "fieldtype": "Link", "options": "Delivery Note", "width": 100},
        {"label": "DO Date", "fieldname": "do_date", "fieldtype": "Data", "width": 90},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 280},
        {"label": "Invoice No.", "fieldname": "inv_no", "fieldtype": "Link", "options": "Sales Invoice", "width": 100},
        {"label": "Inv. Date", "fieldname": "inv_date", "fieldtype": "Data", "width": 90},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": "Ccy", "fieldname": "currency", "fieldtype": "Data", "width": 50},
        {"label": "Total", "fieldname": "total", "fieldtype": "Currency", "options": "currency", "width": 140}
    ]


def get_data(filters):
    sql = """
        SELECT
            dn.name AS do_no,
            DATE_FORMAT(dn.posting_date, '%%d-%%b-%%y') AS do_date,
            dn.customer_name AS customer,
            si.name AS inv_no,
            DATE_FORMAT(si.posting_date, '%%d-%%b-%%y') AS inv_date,
            dn.status AS status,
            dn.currency AS currency,
            dn.grand_total AS total
        FROM
            `tabDelivery Note` AS dn
        LEFT JOIN
            `tabSales Invoice Item` AS si_item ON si_item.delivery_note = dn.name
        LEFT JOIN
            `tabSales Invoice` AS si ON si.name = si_item.parent AND si.docstatus = 1
        WHERE
            dn.docstatus = 1
            AND dn.is_return = 0
            AND dn.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY
            dn.name
        ORDER BY
            dn.posting_date ASC, dn.name ASC
    """

    return frappe.db.sql(sql, filters, as_dict=True)


# ======================================================
#  TOTAL PER CURRENCY
# ======================================================
def add_currency_totals(data):
    if not data:
        return data

    totals = {}
    result = []

    # Hitung total per currency
    for row in data:
        ccy = row.currency

        if ccy not in totals:
            totals[ccy] = {"total": 0}

        totals[ccy]["total"] += row.total or 0

        result.append(row)

    # Tambahkan baris total per currency
    for ccy, total in totals.items():
        result.append({
            "do_no": f"Total ({ccy})",
            "currency": ccy,
            "total": total["total"],
            "is_total_row": 1     # auto-bold + background #fafafa sesuai HTML
        })

    return result
