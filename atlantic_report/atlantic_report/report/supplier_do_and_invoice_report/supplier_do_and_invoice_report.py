# Copyright (c) 2025, Takwindo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    
    if data:
        data = append_currency_totals(data)
        
    return columns, data

def get_columns():
    # Helper untuk formatting Header Kolom (sesuai contoh source)
    def f_lbl(label):
        return f"<span style='font-size: 11px; font-weight: bold;'>{label}</span>"

    return [
        {
            "fieldname": "purchase_order",
            "label": f_lbl("PO No."),
            "fieldtype": "Link",
            "options": "Purchase Order",
            "width": 120
        },
        {
            "fieldname": "po_date",
            "label": f_lbl("PO Date"),
            "fieldtype": "Date", # Kembali ke Date agar bisa diformat JS
            "width": 80
        },
        {
            "fieldname": "inv_no",
            "label": f_lbl("Inv No."),
            "fieldtype": "Link",
            "options": "Purchase Invoice",
            "width": 140
        },
        {
            "fieldname": "inv_date",
            "label": f_lbl("Inv Date"),
            "fieldtype": "Date", # Kembali ke Date agar bisa diformat JS
            "width": 80
        },
        {
            "fieldname": "supplier",
            "label": f_lbl("Supplier Name"),
            "fieldtype": "Data",
            "width": 210
        },
      
        {
            "fieldname": "currency",
            "label": f_lbl("Ccy"),
            "fieldtype": "Link",
            "options": "Currency",
            "width": 50
        },
        {
            "fieldname": "grand_total",
            "label": f_lbl("Amount"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 120
        },
				{
            "fieldname": "status",
            "label": f_lbl("Status"),
            "fieldtype": "Data",
            "width": 80
        }
    ]

def get_data(filters):
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.msgprint("Please select From Date and To Date")
        return []

    # Query murni, tanggal biarkan format database (YYYY-MM-DD)
    sql_query = """
        SELECT
            pii.purchase_order as purchase_order,
            po.transaction_date as po_date,
            pi.name as inv_no,
            pi.posting_date as inv_date,
            pi.supplier as supplier,
            pi.status as status,
            pi.currency as currency,
            pi.grand_total as grand_total
        FROM
            `tabPurchase Invoice` AS pi
        JOIN
            `tabPurchase Invoice Item` AS pii ON pii.parent = pi.name
        LEFT JOIN
            `tabPurchase Order` AS po ON po.name = pii.purchase_order
        WHERE
            pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND pii.purchase_order IS NOT NULL
            AND pi.is_return = 0
        GROUP BY
            pi.name, pii.purchase_order
        ORDER BY
            pii.purchase_order ASC
    """
    
    return frappe.db.sql(sql_query, filters, as_dict=True)

def append_currency_totals(data):
    totals = {}
    
    for row in data:
        ccy = row.get("currency")
        amount = flt(row.get("grand_total"))
        
        if ccy not in totals:
            totals[ccy] = 0.0
        totals[ccy] += amount

    for ccy, total_amount in totals.items():
        total_row = {
            "purchase_order": f"Total ({ccy})", 
            "po_date": None,
            "inv_no": "",
            "inv_date": None,
            "supplier": "",
            "status": "",
            "currency": ccy,
            "grand_total": total_amount,
            "is_total_row": True # Flag penting untuk JS
        }
        data.append(total_row)
        
    return data