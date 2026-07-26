import frappe
from frappe.utils import flt

def execute(filters=None):
    if not filters:
        filters = frappe._dict()

    columns = get_columns()
    data = get_data(filters)
    return columns, data


# ================================================================
# COLUMNS
# ================================================================
def get_columns():
    return [
        {"label": "Off. Rec. No.", "fieldname": "pe_name", "fieldtype": "Data", "width": 140},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 240},

        {"label": "Ccy", "fieldname": "currency_amt", "fieldtype": "Data", "width": 50, "align": "center"},
        {"label": "Paid Amount", "fieldname": "paid_amount", "fieldtype": "Currency", "width": 130},

        {"label": "Ccy", "fieldname": "currency_with", "fieldtype": "Data", "width": 50, "align": "center"},
        {"label": "Paid With", "fieldname": "paid_with", "fieldtype": "Currency", "width": 130},

        {"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 180},
    ]


# ================================================================
# DATA QUERY
# ================================================================
def get_data(filters):

    sql = """
        SELECT
            pe.name AS pe_name,
            pe.posting_date AS date,
            pe.party AS customer,

            pe.paid_from_account_currency AS currency_amt,
            pe.paid_amount AS paid_amount,

            pe.paid_to_account_currency AS currency_with,
            pe.received_amount AS paid_with,

            acc.account_name AS bank_name

        FROM `tabPayment Entry` pe
        LEFT JOIN `tabAccount` acc ON acc.name = pe.paid_to

        WHERE pe.docstatus = 1
        AND pe.payment_type = 'Receive'
        AND pe.posting_date BETWEEN %(from_date)s AND %(to_date)s

        ORDER BY pe.name ASC
    """

    rows = frappe.db.sql(sql, filters, as_dict=True)
    result = []

    totals = {}  # contoh: {"SGD": {"paid_amount": X, "paid_with": Y}}

    for r in rows:

        # append detail rows
        result.append({
            "pe_name": r.pe_name,
            "date": r.date,
            "customer": r.customer,

            "currency_amt": r.currency_amt,
            "paid_amount": flt(r.paid_amount or 0),

            "currency_with": r.currency_with,
            "paid_with": flt(r.paid_with or 0),

            "bank": r.bank_name or ""
        })

        # determine currency grouping (use currency_amt as main currency)
        curr = r.currency_amt

        if curr not in totals:
            totals[curr] = {"paid_amount": 0, "paid_with": 0}

        totals[curr]["paid_amount"] += flt(r.paid_amount or 0)
        totals[curr]["paid_with"] += flt(r.paid_with or 0)


    # ================================================================
    # APPEND TOTAL ROWS BY CURRENCY
    # ================================================================
    for curr, t in totals.items():
        result.append({
            "pe_name": "",
            "date": "",
            "customer": f"<b>Total ({curr})</b>",

            "currency_amt": curr,
            "paid_amount": t["paid_amount"],

            "currency_with": curr,
            "paid_with": t["paid_with"],

            "bank": "",
            "is_total_row": 1
        })

    return result
