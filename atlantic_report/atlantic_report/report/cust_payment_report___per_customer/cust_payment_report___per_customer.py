import frappe
from frappe.utils import flt

def execute(filters=None):
    if not filters:
        filters = frappe._dict()

    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 240},
        {"label": "Ccy", "fieldname": "currency", "fieldtype": "Data", "width": 50, "align": "center"},
        {"label": "Paid Amount", "fieldname": "paid_amount", "fieldtype": "Currency", "width": 140},
        {"label": "Ccy (Paid With)", "fieldname": "paid_with_currency", "fieldtype": "Data", "width": 80},
        {"label": "Paid With", "fieldname": "paid_with", "fieldtype": "Currency", "width": 140},
    ]


def get_data(filters):

    sql = """
        SELECT
            pe.party AS customer,
            pe.paid_from_account_currency AS currency_paid_amount,
            SUM(pe.paid_amount) AS paid_amount,

            pe.paid_to_account_currency AS currency_paid_with,
            SUM(pe.received_amount) AS paid_with

        FROM `tabPayment Entry` pe
        WHERE pe.docstatus = 1
        AND pe.payment_type = 'Receive'
        AND pe.party_type = 'Customer'
        AND pe.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY
            pe.party,
            pe.paid_from_account_currency,
            pe.paid_to_account_currency
        ORDER BY pe.party ASC
    """

    rows = frappe.db.sql(sql, filters, as_dict=True)

    final = []

    # dictionary: {"SGD": {"paid_amount": X, "paid_with": Y}}
    totals = {}

    for r in rows:

        final.append({
            "customer": r.customer,
            "currency": r.currency_paid_amount,
            "paid_amount": r.paid_amount,
            "paid_with_currency": r.currency_paid_with,
            "paid_with": r.paid_with
        })

        # Tentukan currency total (gunakan currency paid_amount)
        curr = r.currency_paid_amount

        if curr not in totals:
            totals[curr] = {"paid_amount": 0, "paid_with": 0}

        totals[curr]["paid_amount"] += flt(r.paid_amount)
        totals[curr]["paid_with"] += flt(r.paid_with)


    # TOTAL ROW PER CURRENCY
    for curr, t in totals.items():
        final.append({
            "customer": f"<b>Total ({curr})</b>",
            "currency": curr,
            "paid_amount": t["paid_amount"],
            "paid_with_currency": curr,
            "paid_with": t["paid_with"],
            "is_total_row": 1
        })

    return final
