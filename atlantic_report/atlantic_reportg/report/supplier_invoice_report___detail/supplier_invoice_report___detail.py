# Copyright (c) 2025, Takwindo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, date_diff, getdate, formatdate

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "inv_details", 
            "label": "INV NO.<br>REC./INV. DATE<br>RECEIVED BY", 
            "fieldtype": "Data", 
            "width": 250,
            "align": "left"
        },
        {
            "fieldname": "supp_terms", 
            "label": "SUPP / STATUS<br>TERMS / DUE", 
            "fieldtype": "Data", 
            "width": 310
        },
        {
            "fieldname": "do_po", 
            "label": "DO NO.<br>PO NO.", 
            "fieldtype": "Data", 
            "width": 110
        },
        {
            "fieldname": "item_desc_brand", 
            "label": "ITEM CODE / BRAND<br>DESCRIPTION", 
            "fieldtype": "Data", 
            "width": 350
        },
        {"fieldname": "qty_ccy", "label": "QTY", "fieldtype": "Data", "width": 110, "align": "right"},
        {"fieldname": "price", "label": "PRICE", "fieldtype": "Currency", "options": "currency", "width": 100},
        {"fieldname": "total", "label": "TOTAL", "fieldtype": "Currency", "options": "currency", "width": 120},
    ]

def get_data(filters):
    if not filters: filters = frappe._dict()

    conditions = ""
    if filters.get("supplier"):
        conditions += " AND pi.supplier = %(supplier)s"
    
    sql = """
        SELECT
            pi.name as inv_no,
            pi.posting_date as inv_date,
            pi.due_date,
            pi.supplier,
            pi.supplier_name,
            pi.status,
            pi.currency,
            pi.grand_total,
            
            pii.item_code,
            pii.item_name,
            pii.description,
            pii.brand,
            pii.qty,
            pii.rate,
            pii.amount,
            pii.stock_uom,
            pii.purchase_order,
            pii.purchase_receipt,
            
            pr.posting_date as rec_date,
            pr.custom_received_by
        FROM
            `tabPurchase Invoice` pi
        JOIN
            `tabPurchase Invoice Item` pii ON pii.parent = pi.name
        LEFT JOIN
            `tabPurchase Receipt` pr ON pii.purchase_receipt = pr.name
        WHERE
            pi.docstatus = 1
            AND pi.posting_date >= %(from_date)s
            AND pi.posting_date <= %(to_date)s
            {conditions}
        ORDER BY
            pi.posting_date ASC, pi.name ASC
    """.format(conditions=conditions)

    raw_data = frappe.db.sql(sql, filters, as_dict=True)

    final_data = []
    current_inv = None
    std_style = "line-height: 1.1em; font-size: 10px; color: #black;"
    
    # Inisialisasi dictionary untuk menyimpan Grand Total per mata uang
    totals_by_currency = {}

    for row in raw_data:
        # --- LOGIKA PERHITUNGAN TOTAL ---
        currency = row.currency
        qty = flt(row.qty)
        amount = flt(row.amount)

        if currency not in totals_by_currency:
            totals_by_currency[currency] = {"total_qty": 0, "total_amount": 0}

        totals_by_currency[currency]["total_qty"] += qty
        totals_by_currency[currency]["total_amount"] += amount
        # ---------------------------------

        # --- HEADER INVOICE (Indent 0) ---
        if row.inv_no != current_inv:
            
            rec_date_str = formatdate(row.rec_date, "dd-MMM-yy") if row.rec_date else "-"
            inv_date_str = formatdate(row.inv_date, "dd-MMM-yy")
            date_display = f"{rec_date_str} / {inv_date_str}"

            days_diff = date_diff(row.due_date, row.inv_date)
            due_date_str = formatdate(row.due_date, "dd-MMM-yy")
            terms_display = f"{int(days_diff)} days / {due_date_str}"

            rcvd = row.custom_received_by or "-"
            
            inv_details_html = f"""
                <div style="{std_style}">
                    {row.inv_no}<br>
                    {date_display}<br>
                    {rcvd}
                </div>
            """

            supp_terms_html = f"""
                <div style="{std_style}">
                    {row.supplier} ({row.status})<br>
                    {terms_display}
                </div>
            """

            header_row = {
                "inv_details": inv_details_html,
                "supp_terms": supp_terms_html,
                "do_po": "", 
                "item_desc_brand": "",
                "qty_ccy": row.currency, 
                
                "price": "", 
                
                "total": row.grand_total, 
                "indent": 0, "has_value": True, "currency": row.currency
            }
            final_data.append(header_row)
            current_inv = row.inv_no

        # --- CHILD ITEM (Indent 1) ---
        
        # --- Kolom Keempat Konten ---
        item_code_brand = f"{row.item_code} / {row.brand or '-'}"
        description_text = row.description if row.description else row.item_name
        
        item_html = f"""
            <div style="{std_style}">
                <span style="font-weight: bold;">{item_code_brand}</span><br>
                <span>{description_text}</span>
            </div>
        """
        # ---------------------------

        po_ref = row.purchase_order if row.purchase_order else "-"
        do_val = row.purchase_receipt if row.purchase_receipt else "-"
        do_po_html = f"""
            <div style="{std_style}">
                {do_val}<br>
                {po_ref}
            </div>
        """

        qty_display = f"{flt(row.qty, 2)} {row.stock_uom}"

        child_row = {
            "inv_details": "", 
            "supp_terms": "",
            "do_po": do_po_html, 
            "item_desc_brand": item_html, 
            "qty_ccy": qty_display,
            "price": row.rate,
            "total": row.amount, 
            "indent": 1, "currency": row.currency
        }
        final_data.append(child_row)

    # --- TAMBAHKAN BARIS GRAND TOTAL PER MATA UANG (HANYA BOLD) ---
    for currency, totals in totals_by_currency.items():
        total_row = {
            # Menggunakan HTML <b> tag untuk bold
            "inv_details": f"<b>GRAND TOTAL ({currency})</b>", 
            "supp_terms": None,
            "do_po": None,
            "item_desc_brand": None,
            # Bold Qty
            "qty_ccy": f"<b>{flt(totals['total_qty'], 2)}</b>",
            "price": None,
            # Biarkan amount sebagai float, akan dibold oleh HTML template karena is_grand_total
            "total": totals['total_amount'], 
            "currency": currency,
            "indent": -1, 
            # Key standar Frappe untuk total, akan memicu <b> dan styling di print format
            "is_grand_total": 1 
        }
        final_data.append(total_row)

    return final_data