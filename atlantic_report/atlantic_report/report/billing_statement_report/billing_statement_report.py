# Copyright (c) 2025, Takwindo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, today

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "no",
            "label": _("NO."),
            "fieldtype": "Int",
            "width": 50
        },
        {
            "fieldname": "bs_no",
            "label": _("BS NO."),
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 180
        },
        {
            "fieldname": "date",
            "label": _("DATE"),
            "fieldtype": "Date",
            "width": 120
        },
        {
            "fieldname": "customer_display",
            "label": _("CUSTOMER"),
            "fieldtype": "Data", 
            "width": 350
        },
        {
            "fieldname": "status_label",
            "label": _("Status"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "amount",
            "label": _("AMOUNT"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 150
        }
    ]

def get_data(filters):
    if not filters: filters = frappe._dict()
    
    # Default Dates
    if not filters.to_date: filters.to_date = today()
    if not filters.from_date: filters.from_date = today()

    params = {
        "from_date": filters.from_date,
        "to_date": filters.to_date,
        "customer": filters.get("customer"),
    }

    # Query SQL
    sql = """
        SELECT
            name as bs_no,
            posting_date,
            customer,
            customer_name,
            grand_total as amount,
            currency
        FROM
            `tabSales Invoice`
        WHERE
            docstatus = 1
            AND posting_date >= %(from_date)s
            AND posting_date <= %(to_date)s
            AND (%(customer)s IS NULL OR customer = %(customer)s)
        ORDER BY
            posting_date ASC, name ASC
    """

    invoices = frappe.db.sql(sql, params, as_dict=True)

    final_data = []
    
    # [LOGIKA BARU] Penampung Grand Total per Mata Uang
    grand_totals = {} 
    
    idx = 1
    for row in invoices:
        ccy = row.currency
        val = flt(row.amount)

        # Akumulasi Total per Currency
        if ccy not in grand_totals:
            grand_totals[ccy] = 0.0
        grand_totals[ccy] += val

        row_data = {
            "no": idx,
            "bs_no": row.bs_no,
            "date": row.posting_date,
            
            # [PERUBAHAN] Hanya Nama Customer Saja
            "customer_display": row.customer_name, 
            
            "status_label": "Receive", 
            "amount": val,
            "currency": ccy
        }
        final_data.append(row_data)
        idx += 1

    # [LOGIKA BARU] Loop dictionary Grand Total untuk membuat baris total
    if final_data:
        for ccy, total_amt in grand_totals.items():
            final_data.append({
                "no": None,
                # Tampilkan Label Total dengan Mata Uangnya
                "bs_no": f"Total ({ccy})", 
                "date": None,
                "customer_display": "",
                "status_label": "",
                "amount": total_amt,
                "currency": ccy,
                "is_grand_total": True # Flag untuk JS
            })

    return final_data
