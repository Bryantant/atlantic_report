# Copyright (c) 2025, Takwindo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, today, getdate

def execute(filters=None):
    if not filters: filters = frappe._dict()
    
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        # [HAPUS] Kolom No. sudah dibuang
        
        {"fieldname": "invoice_no", "label": _("Invoice No."), "fieldtype": "Link", "options": "Sales Invoice", "width": 160},
        {"fieldname": "inv_date", "label": _("Inv. Date"), "fieldtype": "Date", "width": 100},
        {"fieldname": "customer_display", "label": _("Customer"), "fieldtype": "Data", "width": 250},
        {"fieldname": "status", "label": _("Status"), "fieldtype": "Data", "width": 100}, 
        {"fieldname": "currency", "label": _("Curr."), "fieldtype": "Data", "width": 50},
        
        {"fieldname": "net_total", "label": _("Amount"), "fieldtype": "Currency", "options": "currency", "width": 120},
        {"fieldname": "tax_amount", "label": _("Tax"), "fieldtype": "Currency", "options": "currency", "width": 100},
        {"fieldname": "grand_total", "label": _("Total"), "fieldtype": "Currency", "options": "currency", "width": 120},
    ]

def get_data(filters):
    if not filters.to_date: filters.to_date = today()
    if not filters.from_date: filters.from_date = today()
    params = {
        "from_date": filters.from_date,
        "to_date": filters.to_date,
        "customer": filters.get("customer"),
    }
    
    # [HAPUS] Filter Company dibuang agar muncul semua data

    sql = """
        SELECT
            name as invoice_no,
            posting_date,
            customer,
            customer_name,
            status,
            currency,
            net_total,
            total_taxes_and_charges as tax_amount,
            grand_total
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
    grand_totals = {} 
    last_date = None

    for row in invoices:
        # 1. Akumulasi Total
        ccy = row.currency
        if ccy not in grand_totals:
            grand_totals[ccy] = {"net": 0.0, "tax": 0.0, "grand": 0.0}
        
        grand_totals[ccy]["net"] += flt(row.net_total)
        grand_totals[ccy]["tax"] += flt(row.tax_amount)
        grand_totals[ccy]["grand"] += flt(row.grand_total)

        # 2. Logika Tanggal Kembar
        display_date = row.posting_date
        if last_date == row.posting_date:
            display_date = None 
        else:
            last_date = row.posting_date 

        # 3. Susun Data (Tanpa Kolom No)
        row_data = {
            "invoice_no": row.invoice_no,
            "inv_date": display_date, 
            "customer_display": f"{row.customer_name}",
            "status": row.status,
            "currency": ccy,
            "net_total": row.net_total,
            "tax_amount": row.tax_amount,
            "grand_total": row.grand_total
        }
        final_data.append(row_data)

    # 4. Grand Total (Tanpa Spasi Baris)
    if final_data:
        # [HAPUS] Baris final_data.append({}) dihapus agar nempel
        
        for ccy, totals in grand_totals.items():
            final_data.append({
                "invoice_no": f"TOTAL ({ccy})", 
                "inv_date": None,
                "customer_display": "",
                "status": "",
                "currency": ccy,
                "net_total": totals["net"],
                "tax_amount": totals["tax"],
                "grand_total": totals["grand"],
                "is_grand_total": True 
            })

    return final_data
