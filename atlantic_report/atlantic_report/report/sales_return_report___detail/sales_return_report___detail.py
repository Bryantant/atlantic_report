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
        {"label": "Customer Name", "fieldname": "customer", "fieldtype": "Data", "width": 180},
        {"label": "Salesman", "fieldname": "salesman", "fieldtype": "Data", "width": 140},
        {"label": "Return Against DO No.", "fieldname": "return_against", "fieldtype": "Data", "width": 140},
        {"label": "Return Against Date", "fieldname": "return_against_date", "fieldtype": "Data", "width": 100},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 160},
        {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 70},
        {"label": "UOM", "fieldname": "uom", "fieldtype": "Data", "width": 60},
        {"label": "Ccy", "fieldname": "currency", "fieldtype": "Data", "width": 50},
        {"label": "Price", "fieldname": "price", "fieldtype": "Currency", "options": "currency", "width": 100},
        {"label": "Disc", "fieldname": "disc", "fieldtype": "Currency", "options": "currency", "width": 100},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "options": "currency", "width": 120}
    ]


def get_data(filters):
    sql = """
        SELECT
            dn.name AS sr_no,
            DATE_FORMAT(dn.posting_date, '%%d-%%b-%%y') AS date,
            dn.customer_name AS customer,
            st.sales_person AS salesman,
            dn.return_against AS return_against,
            DATE_FORMAT(dn_orig.posting_date, '%%d-%%b-%%y') AS return_against_date,
            dni.item_name AS item_name,
            dni.qty AS qty,
            dni.uom AS uom,
            dn.currency AS currency,
            dni.rate AS price,
            dni.discount_amount AS disc,
            dni.amount AS amount
        FROM
            `tabDelivery Note` AS dn
        LEFT JOIN
            `tabDelivery Note Item` AS dni ON dni.parent = dn.name
        LEFT JOIN
            `tabSales Team` AS st ON st.parent = dn.name
        LEFT JOIN
            `tabDelivery Note` AS dn_orig ON dn_orig.name = dn.return_against
        WHERE
            dn.docstatus = 1
            AND dn.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND dn.is_return = 1
        ORDER BY
            dn.name ASC
    """

    return frappe.db.sql(sql, filters, as_dict=True)


# ======================================================
#  ADD CURRENCY TOTALS
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
                "qty": 0,
                "price": 0,
                "disc": 0,
                "amount": 0
            }

        totals[ccy]["qty"] += row.qty or 0
        totals[ccy]["price"] += row.price or 0
        totals[ccy]["disc"] += row.disc or 0
        totals[ccy]["amount"] += row.amount or 0

        result.append(row)

    # Tambahkan TOTAL ({{currency}})
    for ccy, total in totals.items():
        result.append({
            "sr_no": f"Total ({ccy})",
            "currency": ccy,
            "qty": total["qty"],
            "price": total["price"],
            "disc": total["disc"],
            "amount": total["amount"],
            "is_total_row": 1  # → HTML auto-bold + background #fafafa
        })

    return result
