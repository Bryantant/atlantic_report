# Statement of Account Payable - Outstanding Only

import frappe
from frappe.utils import flt, today


def execute(filters=None):
    if not filters:
        filters = frappe._dict()

    if not filters.from_date:
        filters.from_date = today()
    if not filters.to_date:
        filters.to_date = today()

    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"fieldname": "date", "label": "DATE", "fieldtype": "Date", "width": 95},
        {"fieldname": "reff", "label": "REFF.", "fieldtype": "Data", "width": 230},
        {"fieldname": "currency_display", "label": "Ccy", "fieldtype": "Data", "width": 45},
        {"fieldname": "description", "label": "DESCRIPTION", "fieldtype": "Data", "width": 110},
        {"fieldname": "bill_no", "label": "BILL NO", "fieldtype": "Data", "width": 120},
        {"fieldname": "amount", "label": "AMOUNT", "fieldtype": "Currency", "width": 120},
        {"fieldname": "balance", "label": "BALANCE", "fieldtype": "Currency", "width": 120},
    ]


def get_data(filters):
    params = {"supplier": filters.get("supplier")}
    suppliers = frappe.db.sql(
        """
        SELECT name, supplier_name
        FROM `tabSupplier`
        WHERE docstatus < 2
          AND (%(supplier)s IS NULL OR name = %(supplier)s)
        """,
        params,
        as_dict=True,
    )

    final_rows = []
    grand_total = {}   # {currency: total_amount}

    for supp in suppliers:

        rows, subtotal = get_supplier_outstanding(supp.name, filters)

        if not rows:
            continue

        # HEADER SUPPLIER
        final_rows.append({
            "reff": supp.name,
            "indent": 0,
        })

        # DETAIL ROWS
        final_rows.extend(rows)

        # SUBTOTAL
        final_rows.append({
            "reff": f"TOTAL ({subtotal['currency']})",
            "currency_display": subtotal["currency"],
            "amount": subtotal["amount"],
            "balance": "",
            "is_subtotal_row": 1,
            "is_total_row": 1,
            "indent": 1
        })

        # accumulate GRAND TOTAL
        ccy = subtotal["currency"]
        if ccy not in grand_total:
            grand_total[ccy] = 0
        grand_total[ccy] += subtotal["amount"]

    # GRAND TOTAL (global)
    for ccy, total in grand_total.items():
        final_rows.append({
            "reff": f"GRAND TOTAL ({ccy})",
            "currency_display": ccy,
            "amount": total,
            "balance": "",
            "is_grand_total": 1
        })

    return final_rows


def get_supplier_outstanding(supplier, filters):

    sql = """
        SELECT 
            pi.name AS reff,
            pi.posting_date AS date,
            pi.outstanding_amount AS amount,
            pi.currency,
            'INVOICE' AS description,
            COALESCE(pi.bill_no, pi.name) AS bill_no
        FROM `tabPurchase Invoice` pi
        WHERE pi.docstatus = 1
        AND pi.supplier = %s
        AND pi.outstanding_amount > 0
        AND pi.posting_date <= %s
        ORDER BY pi.posting_date ASC
    """

    invoices = frappe.db.sql(sql, (supplier, filters.to_date), as_dict=True)

    if not invoices:
        return [], None

    running = 0
    rows = []
    currency = invoices[0].currency  # selalu 1 currency per supplier

    for inv in invoices:
        running += flt(inv.amount)

        rows.append({
            "date": inv.date,
            "reff": inv.reff,
            "currency_display": inv.currency,
            "description": inv.description,
            "bill_no": inv.bill_no,
            "amount": inv.amount,
            "balance": running,
            "indent": 1
        })

    subtotal = {
        "currency": currency,
        "amount": running
    }

    return rows, subtotal
