# Copyright (c) 2025, Takwindo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, today

def execute(filters=None):
    if not filters: filters = frappe._dict()
    
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    # 1. Definisi kolom dasar (TRM dihapus dari sini)
    columns = [
        {"fieldname": "date", "label": _("DATE"), "fieldtype": "Date", "width": 100},
        {"fieldname": "reff", "label": _("REFF."), "fieldtype": "Dynamic Link", "options": "doctype", "width": 160},
        {"fieldname": "currency_display", "label": _("Ccy"), "fieldtype": "Data", "width": 50},
        {"fieldname": "description", "label": _("DESCRIPTION"), "fieldtype": "Data", "width": 200},
        {"fieldname": "sales_ref", "label": _("SALES REF"), "fieldtype": "Data", "width": 120},
    ]

    # 2. Logika Kondisional berdasarkan Report Type
    if filters.get("report_type") == "By Month":
        # TAMBAHKAN KOLOM TRM HANYA DISINI
        columns.append({"fieldname": "trm", "label": _("TRM"), "fieldtype": "Int", "width": 50})
        
        columns.extend([
            {"fieldname": "debit", "label": _("DEBIT"), "fieldtype": "Currency", "options": "currency", "width": 120},
            {"fieldname": "credit", "label": _("CREDIT"), "fieldtype": "Currency", "options": "currency", "width": 120},
            {"fieldname": "balance", "label": _("BALANCE"), "fieldtype": "Currency", "options": "currency", "width": 120}
        ])
    else: 
        # Jika Outstanding Only, TRM tidak ditambahkan
        columns.extend([
            {"fieldname": "amount", "label": _("AMOUNT"), "fieldtype": "Currency", "options": "currency", "width": 120},
            {"fieldname": "balance", "label": _("BALANCE"), "fieldtype": "Currency", "options": "currency", "width": 120}
        ])

    columns.append({"fieldname": "doctype", "label": "Doctype", "fieldtype": "Data", "hidden": 1})
    columns.append({"fieldname": "currency", "label": "Currency", "fieldtype": "Data", "hidden": 1})

    return columns

def get_data(filters):
    if not filters.to_date: filters.to_date = today()
    if not filters.from_date: filters.from_date = today()

    cond = "name = %(customer)s" if filters.customer else "docstatus < 2"
    customers = frappe.db.sql(f"SELECT name, customer_name FROM `tabCustomer` WHERE {cond}", filters, as_dict=True)

    final_data = []
    
    # Dictionary untuk menampung Grand Total per Currency
    grand_totals = {}

    for cust in customers:
        cust_rows = []
        
        if filters.get("report_type") == "By Month":
            cust_rows = get_by_month_transactions(cust.name, filters)
        else:
            cust_rows = get_outstanding_invoices(cust.name, filters)

        if cust_rows:
            final_data.append({
                "reff": f"{cust.name}", 
                "date": None,
                "indent": 0,
                "currency": cust_rows[0].get("currency", "IDR"),
                "currency_display": "" 
            })
            
            final_data.extend(cust_rows)
            final_data.append({"reff": "", "indent": 0}) 

            # --- LOGIKA PENJUMLAHAN GRAND TOTAL ---
            ccy = cust_rows[0].get("currency", "IDR")
            if ccy not in grand_totals:
                grand_totals[ccy] = {"debit": 0.0, "credit": 0.0, "amount": 0.0, "balance": 0.0}

            # Ambil balance terakhir dari customer ini (End Balance Customer)
            grand_totals[ccy]["balance"] += flt(cust_rows[-1].get("balance"))

            # Loop untuk sum Debit/Credit/Amount (Skip row Summary/Header di dalam cust_rows)
            for row in cust_rows:
                # Hindari double counting jika ada row Total/Balance bawaan fungsi
                s_ref = row.get("sales_ref", "")
                if "TOTAL" in s_ref or "BALANCE" in s_ref:
                    continue

                grand_totals[ccy]["debit"] += flt(row.get("debit"))
                grand_totals[ccy]["credit"] += flt(row.get("credit"))
                grand_totals[ccy]["amount"] += flt(row.get("amount"))
    
    # --- MENAMPILKAN ROW GRAND TOTAL ---
    if final_data and grand_totals:
        # Spacer sebelum Grand Total
        final_data.append({"reff": "", "indent": 0}) 

        for ccy, totals in grand_totals.items():
            row = {
                "date": None,
                "reff": "",
                "description": "",
                "sales_ref": f"GRAND TOTAL ({ccy})", # Flag untuk JS
                "currency": ccy,
                "currency_display": ccy,
                "indent": 1
            }

            if filters.get("report_type") == "By Month":
                row["debit"] = totals["debit"]
                row["credit"] = totals["credit"]
                row["balance"] = totals["balance"]
                row["trm"] = 0
            else:
                row["amount"] = totals["amount"]
                row["balance"] = totals["balance"]
            
            final_data.append(row)

    return final_data

def get_by_month_transactions(customer, filters):
    
    opening_sql = """
        SELECT SUM(debit - credit) 
        FROM `tabGL Entry` 
        WHERE party_type = 'Customer' 
        AND party = %s 
        AND posting_date < %s 
        AND is_cancelled = 0
    """
    opening_result = frappe.db.sql(opening_sql, (customer, filters.from_date))
    opening_bal = flt(opening_result[0][0]) if opening_result else 0.0

    trans_sql = """
        SELECT
            gle.posting_date as date,
            gle.voucher_no as reff,
            gle.voucher_type as doctype,
            gle.debit,
            gle.credit,
            gle.account_currency as currency,
            CASE 
                WHEN gle.voucher_type = 'Sales Invoice' THEN 'INVOICE'
                WHEN gle.voucher_type = 'Payment Entry' THEN 'OFFICIAL RECEIPT'
                WHEN gle.voucher_type = 'Journal Entry' THEN 'JOURNAL ADJ.'
                ELSE gle.voucher_type 
            END as description,
            IF(gle.voucher_type='Sales Invoice', 
               (SELECT sales_person FROM `tabSales Team` WHERE parent=gle.voucher_no LIMIT 1), 
               '') as sales_ref,
            IF(gle.voucher_type='Sales Invoice', 
               DATEDIFF((SELECT due_date FROM `tabSales Invoice` WHERE name=gle.voucher_no), gle.posting_date), 
               0) as trm
        FROM `tabGL Entry` gle
        WHERE
            gle.party_type = 'Customer' 
            AND gle.party = %s
            AND gle.posting_date BETWEEN %s AND %s
            AND gle.is_cancelled = 0
        ORDER BY gle.posting_date ASC, gle.creation ASC
    """
    transactions = frappe.db.sql(trans_sql, (customer, filters.from_date, filters.to_date), as_dict=True)

    result = []
    curr = transactions[0].currency if transactions else "IDR"
    
    # --- BARIS 1: OPENING BALANCE ---
    result.append({
        "date": filters.from_date,       
        "reff": "",                      
        "currency_display": "",          
        "description": "",
        "sales_ref": "<b>BALANCE</b>",   
        "trm": 0,                        
        "debit": 0,                      
        "credit": 0,                     
        "balance": opening_bal,          
        "indent": 1,
        "currency": curr
    })

    running_balance = opening_bal

    for row in transactions:
        running_balance += (flt(row.debit) - flt(row.credit))
        row.balance = running_balance
        row.indent = 1
        row.currency_display = row.currency
        
        if row.trm == 0: row.trm = 0 
            
        result.append(row)

    return result

def get_outstanding_invoices(customer, filters):
    sql = """
        SELECT
            name as reff,
            posting_date as date,
            'Sales Invoice' as doctype,
            'INVOICE' as description, 
            outstanding_amount as amount,
            currency,
            (SELECT sales_person FROM `tabSales Team` WHERE parent = si.name LIMIT 1) as sales_ref
        FROM `tabSales Invoice` si
        WHERE
            docstatus = 1
            AND customer = %s
            AND outstanding_amount > 0
            AND posting_date <= %s
        ORDER BY posting_date ASC
    """
    data = frappe.db.sql(sql, (customer, filters.to_date), as_dict=True)
    
    running_balance = 0.0
    result = []
    
    for row in data:
        running_balance += flt(row.amount)
        row.balance = running_balance
        row.indent = 1
        row.currency_display = row.currency
        result.append(row)
        
    if result:
        result.append({
            "sales_ref": "<b>TOTAL :</b>",
            "balance": running_balance,
            "indent": 1,
            "currency": result[0].currency
        })

    return result