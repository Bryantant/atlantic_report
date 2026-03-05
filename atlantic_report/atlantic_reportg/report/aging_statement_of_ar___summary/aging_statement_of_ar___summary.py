# Copyright (c) 2025, Takwindo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff, getdate, flt, nowdate, today

def execute(filters=None):
    if not filters: filters = frappe._dict()
    
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        # KOLOM 1: Customer Name
        {"fieldname": "customer_display", "label": _("Customer"), "fieldtype": "Link", "options": "Customer", "width": 220},
        
        # KOLOM 2: Currency
        {"fieldname": "currency", "label": _("Ccy"), "fieldtype": "Data", "width": 50},
        
        # KOLOM 3: Sales Ref
        {"fieldname": "sales_ref", "label": _("Salesman Ref"), "fieldtype": "Data", "width": 100},
        
        # KOLOM 4: Total Outstanding (Awal)
        {"fieldname": "total_outstanding", "label": _("Total"), "fieldtype": "Currency", "options": "currency", "width": 135},
        
        # KOLOM 5-9: Buckets
        {"fieldname": "range1", "label": _("< 31 Days"), "fieldtype": "Currency", "options": "currency", "width": 100},
        {"fieldname": "range2", "label": _("31 - 60 Days"), "fieldtype": "Currency", "options": "currency", "width": 100},
        {"fieldname": "range3", "label": _("61 - 90 Days"), "fieldtype": "Currency", "options": "currency", "width": 100},
        {"fieldname": "range4", "label": _("91 - 150 Days"), "fieldtype": "Currency", "options": "currency", "width": 100},
        {"fieldname": "range5", "label": _("> 150 Days"), "fieldtype": "Currency", "options": "currency", "width": 100},
        
        # KOLOM 10: Outstanding Akhir
        {"fieldname": "outstanding_end", "label": _("Outstanding"), "fieldtype": "Currency", "options": "currency", "width": 135}
    ]

def get_data(filters):
    if not filters: filters = frappe._dict()
    
    # Default Dates
    if not filters.to_date: filters.to_date = today()
    
    # 1. Ambil Data Sales Person dari Master Customer
    customer_sales_map = get_customer_sales_persons()

    params = {
        "to_date": filters.get("to_date"),
        "customer": filters.get("customer"),
        "from_date": filters.get("from_date"),
    }

    sql = """
        SELECT
            customer,
            customer_name,
            posting_date,
            currency,
            outstanding_amount
        FROM
            `tabSales Invoice`
        WHERE
            docstatus = 1
            AND outstanding_amount > 0
            AND posting_date <= %(to_date)s
            AND (%(customer)s IS NULL OR customer = %(customer)s)
            AND (%(from_date)s IS NULL OR posting_date >= %(from_date)s)
        ORDER BY
            customer ASC
    """

    invoices = frappe.db.sql(sql, params, as_dict=True)

    # 3. Proses Aggregasi (Grouping per Customer + Currency)
    summary_map = {}
    today_realtime = getdate(nowdate())

    for row in invoices:
        key = (row.customer, row.currency)
        
        if key not in summary_map:
            summary_map[key] = {
                "customer": row.customer,
                "customer_name": row.customer_name,
                "currency": row.currency,
                "total": 0.0,
                "r1": 0.0, "r2": 0.0, "r3": 0.0, "r4": 0.0, "r5": 0.0
            }

        # Hitung Ageing
        ots_days = date_diff(today_realtime, getdate(row.posting_date))
        val = flt(row.outstanding_amount)

        # Masukkan ke Bucket
        summary_map[key]["total"] += val
        
        if ots_days < 31:
            summary_map[key]["r1"] += val
        elif 31 <= ots_days <= 60:
            summary_map[key]["r2"] += val
        elif 61 <= ots_days <= 90:
            summary_map[key]["r3"] += val
        elif 91 <= ots_days <= 150: 
            summary_map[key]["r4"] += val
        else: 
            summary_map[key]["r5"] += val

    # 4. Susun Data Final
    final_data = []
    grand_totals = {} 

    for key, item in summary_map.items():
        ccy = item["currency"]
        sales_ref = customer_sales_map.get(item["customer"], "")

        # Row Data
        final_data.append({
            "customer_display": f"{item['customer']}", # Gunakan nama field yang sesuai kolom 1
            "currency": ccy,
            "sales_ref": sales_ref,
            "total_outstanding": item["total"],
            "range1": item["r1"],
            "range2": item["r2"],
            "range3": item["r3"],
            "range4": item["r4"],
            "range5": item["r5"],
            "outstanding_end": item["total"]
        })

        # Hitung Grand Total
        if ccy not in grand_totals:
            grand_totals[ccy] = {"t": 0, "r1": 0, "r2": 0, "r3": 0, "r4": 0, "r5": 0}
        
        grand_totals[ccy]["t"] += item["total"]
        grand_totals[ccy]["r1"] += item["r1"]
        grand_totals[ccy]["r2"] += item["r2"]
        grand_totals[ccy]["r3"] += item["r3"]
        grand_totals[ccy]["r4"] += item["r4"]
        grand_totals[ccy]["r5"] += item["r5"]

    # 5. Tambahkan Baris Grand Total
    for ccy, totals in grand_totals.items():
        if totals["t"] > 0:
            final_data.append({
                "customer_display": f"Total ({ccy})", # Label Total
                "currency": ccy,
                "sales_ref": "",
                "total_outstanding": totals["t"],
                "range1": totals["r1"],
                "range2": totals["r2"],
                "range3": totals["r3"],
                "range4": totals["r4"],
                "range5": totals["r5"],
                "outstanding_end": totals["t"],
                
                # [PENTING] Flag untuk HTML Template agar baris ini di-BOLD
                "is_total_row": True 
            })

    return final_data

def get_customer_sales_persons():
    sql = """
        SELECT 
            st.parent as customer, 
            GROUP_CONCAT(DISTINCT st.sales_person SEPARATOR ', ') as sales_person
        FROM `tabSales Team` st
        WHERE st.parenttype = 'Customer'
        GROUP BY st.parent
    """
    result = frappe.db.sql(sql, as_dict=True)
    sales_map = {}
    for r in result:
        sales_map[r.customer] = r.sales_person
    return sales_map
