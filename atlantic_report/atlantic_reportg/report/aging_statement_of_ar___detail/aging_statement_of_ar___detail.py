# Copyright (c) 2025, Takwindo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff, getdate, flt, nowdate, today

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    def f_lbl(label):
        return f"<span style='font-size: 11px; font-weight: bold;'>{label}</span>"

    return [
        {"fieldname": "date", "label": f_lbl(_("Date")), "fieldtype": "Date", "width": 70},
        {"fieldname": "invoice_no", "label": f_lbl(_("Invoice No.")), "fieldtype": "Link", "options": "Sales Invoice", "width": 270},
        {"fieldname": "currency", "label": f_lbl(_("Ccy")), "fieldtype": "Data", "width": 40},
        {"fieldname": "sales_ref", "label": f_lbl(_("Sales Ref")), "fieldtype": "Data", "width": 80},
        {"fieldname": "trm", "label": f_lbl(_("TRM")), "fieldtype": "Int", "width": 40},
        {"fieldname": "total", "label": f_lbl(_("Total")), "fieldtype": "Currency", "options": "currency", "width": 95},
        {"fieldname": "range1", "label": f_lbl(_("< 31 Days")), "fieldtype": "Currency", "options": "currency", "width": 85},
        {"fieldname": "range2", "label": f_lbl(_("31 - 60 Days")), "fieldtype": "Currency", "options": "currency", "width": 85},
        {"fieldname": "range3", "label": f_lbl(_("61 - 90 Days")), "fieldtype": "Currency", "options": "currency", "width": 85},
        {"fieldname": "range4", "label": f_lbl(_("> 90 Days")), "fieldtype": "Currency", "options": "currency", "width": 85},
        {"fieldname": "accumulation", "label": f_lbl(_("Accumulation")), "fieldtype": "Currency", "options": "currency", "width": 95},
        {"fieldname": "ots", "label": f_lbl(_("OTS")), "fieldtype": "Int", "width": 40}
    ]

def get_data(filters):
    if filters is None: filters = frappe._dict()
    if not isinstance(filters, frappe._dict): filters = frappe._dict(filters)
    if not filters.to_date: filters.to_date = today()

    conditions = ""
    if filters.customer:
        conditions += " AND si.customer = %(customer)s"
    if filters.from_date:
        conditions += " AND si.posting_date >= %(from_date)s"

    sql = """
        SELECT
            si.name as invoice_no,
            si.customer,
            si.customer_name,
            si.posting_date,
            si.due_date,
            si.currency,
            si.outstanding_amount,
            GROUP_CONCAT(DISTINCT st.sales_person SEPARATOR ', ') as sales_ref
        FROM
            `tabSales Invoice` si
        LEFT JOIN
            `tabSales Team` st ON st.parent = si.name
        WHERE
            si.docstatus = 1 
            AND si.outstanding_amount > 0
            AND si.posting_date <= %(to_date)s
            {conditions}
        GROUP BY
            si.name
        ORDER BY
            si.customer ASC, si.posting_date ASC
    """.format(conditions=conditions)

    raw_data = frappe.db.sql(sql, filters, as_dict=True)

    final_data = []
    current_customer = None
    customer_accumulation = 0.0
    today_realtime = getdate(nowdate())

    grand_totals_map = {}

    for row in raw_data:
        # HEADER ROW (Logic Customer)
        if row.customer != current_customer:
            header_text = f"{row.customer}"
            
            header_row = {
                "invoice_no": f"{header_text}", 
                "date": None, 
                "indent": 0, 
                "has_value": True,
                "total": "", "range1": "", "range2": "", "range3": "", "range4": "", 
                "accumulation": "", "ots": ""
            }
            final_data.append(header_row)
            current_customer = row.customer
            customer_accumulation = 0.0

        # DATA ROW
        invoice_date = getdate(row.posting_date)
        ots_days = date_diff(today_realtime, invoice_date)
        trm_days = date_diff(getdate(row.due_date), invoice_date)
        val = flt(row.outstanding_amount)
        ccy = row.currency

        # Init Grand Total Map per Currency
        if ccy not in grand_totals_map:
            # [PERBAIKAN 3] Menambahkan key 'accumulation' untuk menampung total akumulasi
            grand_totals_map[ccy] = {"total": 0.0, "r1": 0.0, "r2": 0.0, "r3": 0.0, "r4": 0.0, "accumulation": 0.0}

        r1 = val if ots_days < 31 else 0
        r2 = val if 31 <= ots_days <= 60 else 0
        r3 = val if 61 <= ots_days <= 90 else 0
        r4 = val if ots_days > 90 else 0
        
        customer_accumulation += val

        # Add to Grand Totals
        grand_totals_map[ccy]["total"] += val
        grand_totals_map[ccy]["r1"] += r1
        grand_totals_map[ccy]["r2"] += r2
        grand_totals_map[ccy]["r3"] += r3
        grand_totals_map[ccy]["r4"] += r4
        # [PERBAIKAN 3] Total Accumulation = Sum of all values
        grand_totals_map[ccy]["accumulation"] += val 

        row_data = {
            "date": row.posting_date,
            "invoice_no": row.invoice_no,
            "currency": ccy,
            "sales_ref": row.sales_ref,
            "trm": trm_days,
            "total": val,
            "range1": r1, "range2": r2, "range3": r3, "range4": r4,
            "accumulation": customer_accumulation,
            "ots": ots_days,
            "indent": 1
        }
        final_data.append(row_data)

    if final_data:
        for ccy, totals in grand_totals_map.items():
            final_data.append({
                "date": None, 
                "invoice_no": f"Total ({ccy})", 
                "currency": ccy,
                "total": totals["total"],
                "range1": totals["r1"],
                "range2": totals["r2"],
                "range3": totals["r3"],
                "range4": totals["r4"],
                "accumulation": totals["accumulation"], # [PERBAIKAN 3] Menggunakan nilai total akumulasi
                "indent": 0,
                "is_grand_total": True
            })

    return final_data