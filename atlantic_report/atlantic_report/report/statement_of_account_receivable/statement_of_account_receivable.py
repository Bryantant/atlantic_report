# Statement of Account Receivable - By Month

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
        {"fieldname": "date", "label": "DATE", "fieldtype": "Date", "width": 80},
        {"fieldname": "reff", "label": "REFF.", "fieldtype": "Data", "width": 325},
        {"fieldname": "currency_display", "label": "Ccy", "fieldtype": "Data", "width": 45},
        {"fieldname": "description", "label": "DESCRIPTION", "fieldtype": "Data", "width": 110},
        {"fieldname": "sales_ref", "label": "SALES REF", "fieldtype": "Data", "width": 100},
        {"fieldname": "trm", "label": "TRM", "fieldtype": "Int", "width": 40},
        {"fieldname": "debit", "label": "DEBIT", "fieldtype": "Currency", "width": 100},
        {"fieldname": "credit", "label": "CREDIT", "fieldtype": "Currency", "width": 100},
        {"fieldname": "balance", "label": "BALANCE", "fieldtype": "Currency", "width": 100},
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
    grand = {}
    company_currency = frappe.db.get_default("currency") or "IDR"

    for cust in customers:

        rows = get_transactions(cust.name, filters)

        if not rows:
            continue

        # ============================================================
        # CUSTOMER HEADER ROW (Now Complete Fields)
        # ============================================================
        final_rows.append({
            "date": "",
            "reff": f"Customer : {cust.name}",
            "currency_display": "",
            "description": "",
            "sales_ref": "",
            "trm": "",
            "debit": "",
            "credit": "",
            "balance": "",
            "indent": 0,
            "is_customer_header": 1
        })

        # Append all transaction rows
        final_rows.extend(rows)

        # Determine customer currency
        first_row = rows[0]
        ccy = (
            first_row.get("currency")
            or first_row.get("currency_display")
            or company_currency
        )

        if ccy not in grand:
            grand[ccy] = {"debit": 0.0, "credit": 0.0}

        # Accumulate totals without counting subtotal rows
        for r in rows:
            if r.get("is_total_row"):
                continue

            grand[ccy]["debit"] += flt(r.get("debit"))
            grand[ccy]["credit"] += flt(r.get("credit"))

    # ============================================================
    # GRAND TOTAL PER CURRENCY (Complete Fields)
    # ============================================================
    for ccy, t in grand.items():
        final_rows.append({
            "date": "",
            "reff": f"TOTAL ({ccy})",
            "currency_display": ccy,
            "description": "",
            "sales_ref": "",
            "trm": "",
            "debit": t["debit"],
            "credit": t["credit"],
            "balance": "",
            "indent": 0,
            "is_total_row": 1
        })

    return final_rows


def get_transactions(customer, filters):

    # Opening Balance
    opening = frappe.db.sql(
        """
        SELECT SUM(debit - credit)
        FROM `tabGL Entry`
        WHERE party_type = 'Customer'
          AND party = %s
          AND posting_date < %s
          AND is_cancelled = 0
        """,
        (customer, filters.from_date),
    )[0][0] or 0

    sql = """
        SELECT
            gle.posting_date AS date,
            gle.voucher_no   AS reff,
            gle.debit,
            gle.credit,
            gle.account_currency AS currency,
            CASE 
                WHEN gle.voucher_type = 'Sales Invoice'  THEN 'INVOICE'
                WHEN gle.voucher_type = 'Payment Entry'  THEN 'OFFICIAL RECEIPT'
                ELSE gle.voucher_type
            END AS description,
            (SELECT sales_person FROM `tabSales Team`
             WHERE parent = gle.voucher_no LIMIT 1) AS sales_ref,
            IF(gle.voucher_type = 'Sales Invoice',
                DATEDIFF(
                    (SELECT due_date FROM `tabSales Invoice`
                     WHERE name = gle.voucher_no),
                    gle.posting_date
                ),
                NULL
            ) AS trm
        FROM `tabGL Entry` gle
        WHERE party_type = 'Customer'
          AND party = %s
          AND posting_date BETWEEN %s AND %s
          AND is_cancelled = 0
        ORDER BY gle.posting_date ASC
    """

    entries = frappe.db.sql(
        sql, (customer, filters.from_date, filters.to_date), as_dict=True
    )

    if not entries:
        return []

    result = []
    curr = entries[0].currency

    # ============================================================
    # OPENING BALANCE ROW
    # ============================================================
    result.append({
        "date": filters.from_date,
        "reff": "",
        "currency": curr,
        "currency_display": "",
        "description": "",
        "sales_ref": "BALANCE",
        "trm": "",
        "debit": "",
        "credit": "",
        "balance": opening,
        "indent": 1,
    })

    bal = opening

    for e in entries:
        bal += flt(e.debit) - flt(e.credit)
        e.balance = bal
        e.currency_display = e.currency
        e.indent = 1
        result.append(e)

    return result
