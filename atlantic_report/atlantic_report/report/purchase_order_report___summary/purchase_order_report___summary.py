# Copyright (c) 2025, Your Name and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, formatdate

def execute(filters=None):
    if not filters: filters = frappe._dict()
    
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "po_no",
            "label": _("PO No."),
            "fieldtype": "Link",
            "options": "Purchase Order",
            "width": 150
        },
        {
            "fieldname": "po_date",
            "label": _("PO Date"),
            "fieldtype": "Data", 
            "width": 100
        },
        {
            "fieldname": "supplier",
            "label": _("Supplier"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "status",
            "label": _("Status"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "preparer",
            "label": _("Preparer"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "currency",
            "label": _("Ccy"),
            "fieldtype": "Data",
            "width": 50
        },
        {
            "fieldname": "total",
            "label": _("Total"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 120
        },
        {
            "fieldname": "tax",
            "label": _("Tax"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 100
        },
        {
            "fieldname": "disc",
            "label": _("Disc"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 100
        },
        {
            "fieldname": "grand_total",
            "label": _("Grand Total"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 120
        }
    ]

def get_data(filters):
    # Query SQL
    sql = """
        SELECT
            name as po_no,
            transaction_date,
            supplier as supplier,
            status,
            custom_order_by as preparer,
            currency,
            total,
            total_taxes_and_charges as tax,
            discount_amount as disc,
            grand_total
        FROM
            `tabPurchase Order`
        WHERE
            docstatus < 2 
            AND transaction_date BETWEEN %(from_date)s AND %(to_date)s
        ORDER BY
            name ASC
    """
    
    raw_data = frappe.db.sql(sql, filters, as_dict=True)
    
    final_data = []
    currency_totals = {}

    for row in raw_data:
        # 1. Format Tanggal
        row['po_date'] = formatdate(row['transaction_date'], "dd-MMM-yy")
        
        # 2. Akumulasi Total per Currency
        ccy = row['currency']
        if ccy not in currency_totals:
            currency_totals[ccy] = {
                "total": 0.0,
                "tax": 0.0,
                "disc": 0.0,
                "grand_total": 0.0
            }
            
        currency_totals[ccy]["total"] += flt(row['total'])
        currency_totals[ccy]["tax"] += flt(row['tax'])
        currency_totals[ccy]["disc"] += flt(row['disc'])
        currency_totals[ccy]["grand_total"] += flt(row['grand_total'])
        
        final_data.append(row)

    # 3. Tambahkan Baris Total di Akhir (Langsung tanpa spasi/jarak)
    if final_data:
        # [REVISI] Baris spacer `final_data.append({})` telah dihapus di sini.
        
        for ccy, totals in currency_totals.items():
            row_total = {
                "po_no": f"TOTAL {ccy}", 
                "currency": ccy,
                "total": totals["total"],
                "tax": totals["tax"],
                "disc": totals["disc"],
                "grand_total": totals["grand_total"],
                "is_total_row": True 
            }
            final_data.append(row_total)

    return final_data