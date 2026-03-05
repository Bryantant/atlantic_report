import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)

    data = add_currency_totals(data)

    return columns, data


def get_columns():
    return [
        {"label": "SR No.", "fieldname": "sr_no", "fieldtype": "Data", "width": 120},
        {"label": "Date", "fieldname": "date", "fieldtype": "Data", "width": 100},
        {"label": "Return Against DO No.", "fieldname": "return_against", "fieldtype": "Data", "width": 150},
        {"label": "Return Against Date", "fieldname": "return_against_date", "fieldtype": "Data", "width": 100},
        {"label": "Salesman", "fieldname": "salesman", "fieldtype": "Data", "width": 140},
        {"label": "Customer Name", "fieldname": "customer", "fieldtype": "Data", "width": 180},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": "Ccy", "fieldname": "currency", "fieldtype": "Data", "width": 50},
        {"label": "Total", "fieldname": "total", "fieldtype": "Currency", "options": "currency", "width": 120},
        {"label": "Total Taxes and Charges", "fieldname": "taxes", "fieldtype": "Currency", "options": "currency", "width": 120},
        {"label": "Disc", "fieldname": "disc", "fieldtype": "Currency", "options": "currency", "width": 120},
        {"label": "Grand Total", "fieldname": "grand_total", "fieldtype": "Currency", "options": "currency", "width": 140}
    ]


def get_data(filters):
    sql = """
        SELECT
            dn.name AS sr_no,
            DATE_FORMAT(dn.posting_date, '%%d-%%b-%%y') AS date,
            dn.return_against AS return_against,
            DATE_FORMAT(dn_orig.posting_date, '%%d-%%b-%%y') AS return_against_date,
            st.sales_person AS salesman,
            dn.customer_name AS customer,
            dn.status AS status,
            dn.currency AS currency,
            dn.total AS total,
            dn.total_taxes_and_charges AS taxes,
            dn.discount_amount AS disc,
            dn.grand_total AS grand_total
        FROM
            `tabDelivery Note` AS dn
        LEFT JOIN
            `tabSales Team` AS st ON st.parent = dn.name
        LEFT JOIN
            `tabDelivery Note` AS dn_orig ON dn_orig.name = dn.return_against
        WHERE
            dn.docstatus = 1
            AND dn.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND dn.is_return = 1
        ORDER BY
            dn.posting_date ASC
    """

    return frappe.db.sql(sql, filters, as_dict=True)


# ======================================================
#   TOTAL PER CURRENCY → Auto-bold + background di HTML
# ======================================================
def add_currency_totals(data):
    if not data:
        return data

    totals = {}
    result = []

    for row in data:
        ccy = row.currency

        if ccy not in totals:
            totals[ccy] = {
                "total": 0,
                "taxes": 0,
                "disc": 0,
                "grand_total": 0
            }

        totals[ccy]["total"] += row.total or 0
        totals[ccy]["taxes"] += row.taxes or 0
        totals[ccy]["disc"] += row.disc or 0
        totals[ccy]["grand_total"] += row.grand_total or 0

        result.append(row)

    # Tambahkan row total
    for ccy, t in totals.items():
        result.append({
            "sr_no": f"Total ({ccy})",
            "currency": ccy,
            "total": t["total"],
            "taxes": t["taxes"],
            "disc": t["disc"],
            "grand_total": t["grand_total"],
            "is_total_row": 1   # → HTML akan auto-bold + background #fafafa
        })

    return result
