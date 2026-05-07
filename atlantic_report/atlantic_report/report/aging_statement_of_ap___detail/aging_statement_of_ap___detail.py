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
    return [
        {"fieldname": "date", "label": _("Date"), "fieldtype": "Date", "width": 70},
        {"fieldname": "invoice_no", "label": _("Invoice No."), "fieldtype": "Link", "options": "Purchase Invoice", "width": 210},
        {"fieldname": "currency", "label": _("Ccy"), "fieldtype": "Data", "width": 40},
        
        # Kolom Angka
        {"fieldname": "total", "label": _("Total"), "fieldtype": "Currency", "options": "currency", "width": 130},
        {"fieldname": "range1", "label": _("< 31 Days"), "fieldtype": "Currency", "options": "currency", "width": 110},
        {"fieldname": "range2", "label": _("31 - 60 Days"), "fieldtype": "Currency", "options": "currency", "width": 110},
        {"fieldname": "range3", "label": _("61 - 90 Days"), "fieldtype": "Currency", "options": "currency", "width": 110},
        {"fieldname": "range4", "label": _("> 90 Days"), "fieldtype": "Currency", "options": "currency", "width": 110},
        {"fieldname": "accumulation", "label": _("Accumulation"), "fieldtype": "Currency", "options": "currency", "width": 130},
        {"fieldname": "ots", "label": _("OTS"), "fieldtype": "Int", "width": 50}
    ]

def get_data(filters):
    if filters is None: filters = frappe._dict()
    if not isinstance(filters, frappe._dict): filters = frappe._dict(filters)
    if not filters.to_date: filters.to_date = today()
    params = {
        "to_date": filters.to_date,
        "supplier": filters.get("supplier"),
        "from_date": filters.get("from_date"),
    }

    sql = """
        SELECT
            pi.name as invoice_no,
            pi.supplier,
            pi.supplier_name,
            pi.posting_date,
            pi.due_date,
            pi.currency,
            (pi.grand_total - pi.paid_amount) AS outstanding_amount
        FROM
            `tabPurchase Invoice` pi
        WHERE
            pi.docstatus = 1
            AND pi.outstanding_amount > 0
            AND pi.posting_date <= %(to_date)s
            AND (%(supplier)s IS NULL OR pi.supplier = %(supplier)s)
            AND (%(from_date)s IS NULL OR pi.posting_date >= %(from_date)s)
        ORDER BY
            pi.supplier ASC, pi.posting_date ASC
    """

    raw_data = frappe.db.sql(sql, params, as_dict=True)

    final_data = []
    current_supplier = None
    supplier_accumulation = 0.0
    today_realtime = getdate(nowdate())

    grand_totals_map = {}

    for row in raw_data:
        # --- 1. HEADER ROW (Grouping Supplier) ---
        if row.supplier != current_supplier:
            header_row = {
                "invoice_no": row.supplier, # Ditampilkan di kolom Invoice
                "date": None, 
                "currency": row.currency, # Penting untuk referensi format currency jika diperlukan
                "indent": 0, 
                "has_value": True,
                "total": "", "range1": "", "range2": "", "range3": "", "range4": "", 
                "accumulation": "", "ots": ""
            }
            final_data.append(header_row)
            current_supplier = row.supplier
            supplier_accumulation = 0.0

        # --- 2. DATA ROW ---
        invoice_date = getdate(row.posting_date)
        ots_days = date_diff(today_realtime, invoice_date)
        val = flt(row.outstanding_amount)
        ccy = row.currency

        # Init Map Grand Total
        if ccy not in grand_totals_map:
            grand_totals_map[ccy] = {
                "total": 0.0, "r1": 0.0, "r2": 0.0, "r3": 0.0, "r4": 0.0, "accumulation": 0.0
            }

        # Bucket Logic
        r1 = val if ots_days < 31 else 0
        r2 = val if 31 <= ots_days <= 60 else 0
        r3 = val if 61 <= ots_days <= 90 else 0
        r4 = val if ots_days > 90 else 0
        
        supplier_accumulation += val

        # Akumulasi Grand Total
        grand_totals_map[ccy]["total"] += val
        grand_totals_map[ccy]["r1"] += r1
        grand_totals_map[ccy]["r2"] += r2
        grand_totals_map[ccy]["r3"] += r3
        grand_totals_map[ccy]["r4"] += r4
        grand_totals_map[ccy]["accumulation"] += val

        row_data = {
            "date": row.posting_date,
            "invoice_no": row.invoice_no,
            "currency": ccy,
            "total": val,
            "range1": r1, "range2": r2, "range3": r3, "range4": r4,
            "accumulation": supplier_accumulation,
            "ots": ots_days,
            "indent": 1
        }
        final_data.append(row_data)

    # --- 3. GRAND TOTAL ROW ---
    if final_data:
        # Spacer (Optional, jika ingin ada jarak)
        # final_data.append({}) 

        for ccy, totals in grand_totals_map.items():
            final_data.append({
                "date": None,
                "invoice_no": f"TOTAL ({ccy})", # Label Total
                "currency": ccy,                # Mata Uang (Penting untuk HTML formatter)
                "total": totals["total"],
                "range1": totals["r1"],
                "range2": totals["r2"],
                "range3": totals["r3"],
                "range4": totals["r4"],
                "accumulation": totals["accumulation"], 
                "indent": 0,
                
                # [KUNCI] Flag ini dibaca oleh HTML Template Anda untuk BOLD
                "is_grand_total": True 
            })

    return final_data
