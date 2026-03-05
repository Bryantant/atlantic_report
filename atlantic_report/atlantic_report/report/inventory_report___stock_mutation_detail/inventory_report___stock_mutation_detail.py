# Copyright (c) 2025, Takwindo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, add_months, today, getdate, formatdate

def execute(filters=None):
    if not filters: filters = frappe._dict()
    
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        # [KEMBALI KE DATE] Biarkan HTML yang format tanggalnya
        {"fieldname": "date", "label": _("Date"), "fieldtype": "Date", "width": 100, "align": "center"},
        
        # [DATA] Voucher Type & No
        {"fieldname": "voucher_type", "label": _("Voucher Type"), "fieldtype": "Data", "width": 140},
        
        {
            "fieldname": "voucher_no", 
            "label": _("Voucher No"), 
            "fieldtype": "Dynamic Link", 
            "options": "voucher_type", 
            "width": 180
        },
        
        # [FLOAT] Rata Kanan Otomatis di HTML
        {"fieldname": "in_qty", "label": _("In Qty"), "fieldtype": "Float", "width": 100},
        {"fieldname": "out_qty", "label": _("Out Qty"), "fieldtype": "Float", "width": 100},
        
        # [CURRENCY] Rata Kanan Otomatis di HTML
        {"fieldname": "incoming_rate", "label": _("In Rate"), "fieldtype": "Currency", "width": 110},
        {"fieldname": "outgoing_rate", "label": _("Out Rate"), "fieldtype": "Currency", "width": 110},
        {"fieldname": "valuation_rate", "label": _("Unit Price"), "fieldtype": "Currency", "width": 110},
        
        {"fieldname": "balance_qty", "label": _("Bal. Qty"), "fieldtype": "Float", "width": 110},
        {"fieldname": "balance_value", "label": _("Bal. Value"), "fieldtype": "Currency", "width": 140},
        
        # [HIDDEN] Currency untuk referensi format_currency di HTML
        {"fieldname": "currency", "label": "Currency", "fieldtype": "Data", "hidden": 1}
    ]

def get_data(filters):
    if not filters.from_date: filters.from_date = add_months(today(), -1)
    if not filters.to_date: filters.to_date = today()
    params = {
        "from_date": filters.from_date,
        "to_date": filters.to_date,
        "item_code": filters.get("item_code"),
    }

    # 1. AMBIL DATA TRANSAKSI
    sql = """
        SELECT
            name,
            item_code,
            posting_date as date,
            voucher_type,
            voucher_no,
            actual_qty,
            incoming_rate,
            outgoing_rate,
            valuation_rate,
            qty_after_transaction,
            stock_value
        FROM
            `tabStock Ledger Entry`
        WHERE
            posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND is_cancelled = 0
            AND (%(item_code)s IS NULL OR item_code = %(item_code)s)
        ORDER BY
            item_code ASC, 
            posting_date ASC, 
            posting_time ASC,
            creation ASC
    """
    
    transactions = frappe.db.sql(sql, params, as_dict=True)

    # 2. AMBIL OPENING BALANCE
    opening_sql = """
        SELECT 
            item_code,
            SUM(actual_qty) as qty,
            SUM(stock_value_difference) as val
        FROM `tabStock Ledger Entry`
        WHERE 
            posting_date < %(from_date)s
            AND is_cancelled = 0
            AND (%(item_code)s IS NULL OR item_code = %(item_code)s)
        GROUP BY item_code
    """
    
    opening_res = frappe.db.sql(opening_sql, params, as_dict=True)
    
    opening_map = {}
    for d in opening_res:
        qty = flt(d.qty)
        val = flt(d.val)
        if abs(qty) <= 0.001: 
            qty = 0.0
            val = 0.0 
        opening_map[d.item_code] = {"qty": qty, "val": val}

    final_data = []
    
    # 3. GROUPING & CALCULATING
    all_items = set([d.item_code for d in transactions] + list(opening_map.keys()))
    sorted_items = sorted(list(all_items))

    trans_map = {}
    for row in transactions:
        if row.item_code not in trans_map: trans_map[row.item_code] = []
        trans_map[row.item_code].append(row)
        
    company_currency = frappe.get_cached_value('Company',  frappe.defaults.get_user_default("Company"),  "default_currency") or "IDR"

    for item in sorted_items:
        op_qty = opening_map.get(item, {}).get("qty", 0.0)
        op_val = opening_map.get(item, {}).get("val", 0.0)
        
        final_data.append({
            "date": filters.from_date, # Date Object
            "voucher_type": item,      # Item Code di kolom Voucher Type
            "voucher_no": "OPENING BALANCE",
            "in_qty": None, "out_qty": None, 
            "incoming_rate": None, "outgoing_rate": None, "valuation_rate": None,
            "balance_qty": op_qty,
            "balance_value": op_val,
            "currency": company_currency,
            
            # Gunakan is_total_row agar HTML menebalkan baris ini (sebagai Header)
            "is_total_row": True 
        })

        item_trans = trans_map.get(item, [])
        
        for row in item_trans:
            v_type = row.voucher_type
            if v_type == "Delivery Note":
                v_type = "Delivery Order"

            in_qty = flt(row.actual_qty) if row.actual_qty > 0 else 0
            out_qty = abs(flt(row.actual_qty)) if row.actual_qty < 0 else 0
            
            bal_qty = flt(row.qty_after_transaction)
            bal_val = flt(row.stock_value)
            
            if abs(bal_qty) <= 0.001:
                bal_qty = 0.0
                bal_val = 0.0

            final_data.append({
                "date": row.date, # Date Object
                "voucher_type": v_type,
                "voucher_no": row.voucher_no,
                "in_qty": in_qty,
                "out_qty": out_qty,
                "incoming_rate": row.incoming_rate,
                "outgoing_rate": row.outgoing_rate,
                "valuation_rate": row.valuation_rate,
                "balance_qty": bal_qty,
                "balance_value": bal_val,
                "currency": company_currency,
                
                # Tidak ada flag -> Baris biasa
            })
            
    return final_data
