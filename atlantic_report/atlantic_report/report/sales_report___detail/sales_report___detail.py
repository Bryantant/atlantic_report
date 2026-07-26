# Copyright (c) 2025, Takwindo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import formatdate, flt, get_url_to_form

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "label": "DO No<br>Date<br>Salesman", 
            "fieldname": "do_info", 
            "fieldtype": "Data", 
            "width": 130,
            "align": "left"
        },
        {
            "label": "Invoice No<br>Date", 
            "fieldname": "inv_info", 
            "fieldtype": "Data", 
            "width": 110,
            "align": "left"
        },
        {
            "label": "Customer", 
            "fieldname": "customer_name", 
            "fieldtype": "Data", 
            "width": 230
        },
        {
            "label": "Item Code<br>Description (Brand, Model, Size)", 
            "fieldname": "item_display", 
            "fieldtype": "Data", 
            "width": 300
        },
        {
            "label": "Curr", 
            "fieldname": "currency", 
            "fieldtype": "Data", 
            "width": 50
        },
        {
            "label": "Qty<br>U/M", 
            "fieldname": "qty_uom", 
            "fieldtype": "Data", 
            "width": 80,
            "align": "right"
        },
        {
            "label": "Price", 
            "fieldname": "rate", 
            "fieldtype": "Currency", 
            "options": "currency",
            "width": 90
        },
        {
            "label": "Amount", 
            "fieldname": "amount", 
            "fieldtype": "Currency", 
            "options": "currency", 
            "width": 110
        },
        {
            "label": "Status", 
            "fieldname": "status", 
            "fieldtype": "Data", 
            "width": 80
        }
    ]

def get_data(filters):
    params = {
        "from_date": filters.get("from_date") if filters else None,
        "to_date": filters.get("to_date") if filters else None,
        "customer": filters.get("customer") if filters else None,
    }
    
    sql = """
        SELECT
            dn.name as do_no,
            DATE_FORMAT(dn.posting_date, '%%d-%%b-%%y') AS do_date,
            dn.customer_name,
            dn.currency,
            dn.status,
            dni.item_code,
            dni.item_name,
            dni.description,
            dni.qty,
            dni.uom,
            dni.rate,
            dni.amount,
            
            (
                SELECT GROUP_CONCAT(DISTINCT sales_person SEPARATOR ', ') 
                FROM `tabSales Team` 
                WHERE parent = dn.name
            ) as salesman,
            
            (
                SELECT parent 
                FROM `tabSales Invoice Item` 
                WHERE delivery_note = dn.name 
                LIMIT 1
            ) as inv_no,

            (
                SELECT posting_date 
                FROM `tabSales Invoice` 
                WHERE name = (
                    SELECT parent 
                    FROM `tabSales Invoice Item` 
                    WHERE delivery_note = dn.name 
                    LIMIT 1
                )
            ) as inv_date

        FROM
            `tabDelivery Note` dn
        INNER JOIN
            `tabDelivery Note Item` dni ON dn.name = dni.parent
        WHERE
            dn.docstatus = 1
            AND (
                %(from_date)s IS NULL OR %(to_date)s IS NULL
                OR dn.posting_date BETWEEN %(from_date)s AND %(to_date)s
            )
            AND (%(customer)s IS NULL OR dn.customer = %(customer)s)
        ORDER BY
            dn.name ASC
    """

    raw_data = frappe.db.sql(sql, params, as_dict=True)
    
    final_data = []
    
    # Inisialisasi dictionary untuk menyimpan total per mata uang
    totals_by_currency = {}

    # Font Size 10px & line-height 1.1
    style_base = "font-size: 10; line-height: 1.1; color: #36414c;"
    style_bold = "font-size: 10; font-weight: bold; line-height: 1.1; color: #36414c;"

    
    for row in raw_data:
        # --- 1. HITUNG TOTAL PER CURRENCY ---
        currency = row.currency
        qty = flt(row.qty)
        amount = flt(row.amount)

        if currency not in totals_by_currency:
            totals_by_currency[currency] = {"total_qty": 0, "total_amount": 0}
        
        totals_by_currency[currency]["total_qty"] += qty
        totals_by_currency[currency]["total_amount"] += amount

        # --- 2. FORMAT DO INFO ---
        do_link = get_url_to_form("Delivery Note", row.do_no)
        formatted_do_date = formatdate(row.do_date) if row.do_date else "-"
        salesman_txt = row.salesman if row.salesman else "-"
        
        row["do_info"] = f"""
            <div style="{style_base}">
                <a href="{do_link}" style="{style_bold}">{row.do_no}</a><br>
                <span>{formatted_do_date}</span><br>
                <span>{salesman_txt}</span>
            </div>
        """

        # --- 3. FORMAT INVOICE INFO ---
        if row.inv_no:
            inv_link = get_url_to_form("Sales Invoice", row.inv_no)
            formatted_inv_date = formatdate(row.inv_date) if row.inv_date else "-"
            row["inv_info"] = f"""
                <div style="{style_base}">
                    <a href="{inv_link}" style="{style_bold}">{row.inv_no}</a><br>
                    <span>{formatted_inv_date}</span>
                </div>
            """
        else:
            row["inv_info"] = "-"

        # --- 4. FORMAT ITEM ---
        desc_text = row.description if row.description else row.item_name
        
        # Hapus Enter/Spasi kosong
        if desc_text:
            desc_text = " ".join(desc_text.split())
        
        if row.item_code == desc_text:
              item_html = f"<div style='{style_bold}'>{row.item_code}</div>"
        else:
            item_html = f"""
                <div style="{style_base}">
                    <span style="{style_bold}">{row.item_code}</span><br>
                    <span>{desc_text}</span>
                </div>
             """
        row["item_display"] = item_html

        # --- 5. FORMAT QTY & UOM ---
        row["qty_uom"] = f"""
            <div style="{style_base}">
                <span style="{style_bold}">{flt(row.qty)}</span><br>
                <span>{row.uom}</span>
            </div>
        """

        final_data.append(row)

    # --- 6. TAMBAHKAN BARIS TOTAL PER CURRENCY ---
    # Styling untuk baris total
    total_style = "font-size: 10; font-weight: bold; line-height: 1.2;"

    for currency, totals in totals_by_currency.items():
        total_row = {
            "do_info": f"<div style='{total_style}'>Total ({currency})</div>",
            "inv_info": "",
            "customer_name": "",
            "item_display": "",
            "currency": currency,
            "qty_uom": f"""
                <div style="{total_style}">
                    <span>{flt(totals['total_qty'])}</span>
                </div>
            """,
            "rate": "",
            "amount": totals['total_amount'],
            "status": "",
            "is_total_row": 1
        }

        final_data.append(total_row)

    return final_data
