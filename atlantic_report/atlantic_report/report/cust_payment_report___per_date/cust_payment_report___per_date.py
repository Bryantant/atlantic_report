import frappe
from frappe.utils import flt

def execute(filters=None):
    if not filters:
        filters = frappe._dict()

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
        {"label": "No. of OR", "fieldname": "or_count", "fieldtype": "Int", "width": 90},

        {"label": "Ccy (Paid Amount)", "fieldname": "currency_paid_amount", "fieldtype": "Data", "width": 110},
        {"label": "Paid Amount", "fieldname": "paid_amount", "fieldtype": "Currency", "width": 150},

        {"label": "Ccy (Paid With)", "fieldname": "currency_paid_with", "fieldtype": "Data", "width": 110},
        {"label": "Paid With", "fieldname": "paid_with", "fieldtype": "Currency", "width": 150},
    ]


def get_data(filters):

    sql = """
        SELECT
            pe.posting_date AS date,
            COUNT(pe.name) AS or_count,

            pe.paid_from_account_currency AS currency_paid_amount,
            SUM(pe.paid_amount) AS paid_amount,

            pe.paid_to_account_currency AS currency_paid_with,
            SUM(pe.received_amount) AS paid_with

        FROM `tabPayment Entry` pe
        WHERE pe.docstatus = 1
        AND pe.payment_type = 'Receive'
        AND pe.posting_date BETWEEN %(from_date)s AND %(to_date)s

        GROUP BY
            pe.posting_date,
            pe.paid_from_account_currency,
            pe.paid_to_account_currency

        ORDER BY pe.posting_date ASC
    """

    rows = frappe.db.sql(sql, filters, as_dict=True)

    # ---------- TOTAL PER CURRENCY ----------
    totals = {}

    for r in rows:
        curr_amt = r.currency_paid_amount
        curr_with = r.currency_paid_with

        # Paid Amount per currency
        if curr_amt:
            if curr_amt not in totals:
                totals[curr_amt] = {"paid_amount": 0, "paid_with": 0}
            totals[curr_amt]["paid_amount"] += flt(r.paid_amount)

        # Paid With per currency
        if curr_with:
            if curr_with not in totals:
                totals[curr_with] = {"paid_amount": 0, "paid_with": 0}
            totals[curr_with]["paid_with"] += flt(r.paid_with)

    final = list(rows)

    # ---------- TOTAL ROW ----------
    for curr, t in totals.items():

        paid_amount_val = t["paid_amount"] if t["paid_amount"] > 0 else None
        paid_with_val = t["paid_with"] if t["paid_with"] > 0 else None

        final.append({
            "date": None,
            "or_count": None,

            "currency_paid_amount": f"Total ({curr})",
            "paid_amount": paid_amount_val,

            "currency_paid_with": None,
            "paid_with": paid_with_val,

            "is_total_row": 1
        })

    return final
