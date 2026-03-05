# Statement of Account Receivable - Outstanding Only

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
        {"fieldname": "sales_ref", "label": "SALES REF", "fieldtype": "Data", "width": 120},
        {"fieldname": "amount", "label": "AMOUNT", "fieldtype": "Currency", "width": 120},
        {"fieldname": "balance", "label": "BALANCE", "fieldtype": "Currency", "width": 120},
    ]


def get_data(filters):
    params = {"customer": filters.get("customer")}
    customers = frappe.db.sql(
        """
        SELECT name, customer_name
        FROM `tabCustomer`
        WHERE docstatus < 2
          AND (%(customer)s IS NULL OR name = %(customer)s)
        """,
        params,
        as_dict=True,
    )

    final_rows = []
    grand_total = {}   # pisahkan dari subtotal

    for cust in customers:

        rows, subtotal = get_customer_outstanding(cust.name, filters)

        if not rows:
            continue

        # HEADER CUSTOMER
        final_rows.append({
            "reff": cust.name,
            "indent": 0,
        })

        # ADD TRANSACTION ROWS
        final_rows.extend(rows)

        # SUBTOTAL PER CUSTOMER
        final_rows.append({
            "reff": f"TOTAL ({subtotal['currency']})",
            "currency_display": subtotal["currency"],
            "amount": subtotal["amount"],
            "balance": "",
            "is_subtotal_row": 1,
            "indent": 1
        })

        # accumulate into GRAND TOTAL
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


def get_customer_outstanding(customer, filters):

    sql = """
        SELECT 
            si.name AS reff,
            si.posting_date AS date,
            si.outstanding_amount AS amount,
            si.currency,
            'INVOICE' AS description,
            (SELECT sales_person FROM `tabSales Team` 
             WHERE parent = si.name LIMIT 1) AS sales_ref
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
        AND si.customer = %s
        AND si.outstanding_amount > 0
        AND si.posting_date <= %s
        ORDER BY si.posting_date ASC
    """

    invoices = frappe.db.sql(sql, (customer, filters.to_date), as_dict=True)

    if not invoices:
        return [], None

    running = 0
    rows = []
    currency = invoices[0].currency  # selalu sama per customer

    for inv in invoices:
        running += flt(inv.amount)

        rows.append({
            "date": inv.date,
            "reff": inv.reff,
            "currency_display": inv.currency,
            "description": inv.description,
            "sales_ref": inv.sales_ref,
            "amount": inv.amount,
            "balance": running,
            "indent": 1
        })

    subtotal = {
        "currency": currency,
        "amount": running
    }

    return rows, subtotal
