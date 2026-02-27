# Copyright (c) 2025, Takwindo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_months, today, flt, fmt_money

def execute(filters=None):
    if not filters: filters = frappe._dict()
    
    if not filters.from_date: filters.from_date = add_months(today(), -1)
    if not filters.to_date: filters.to_date = today()

    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        # KOLOM 1: Item Code / Description
        {
            "fieldname": "item_info", 
            "label": "ITEM CODE<br>DESCRIPTION", 
            "fieldtype": "Data", 
            "width": 250,
            "align": "left"
        },

        # KOLOM 2: Total In / Total Out (Qty)
        {
            "fieldname": "mutation_qty", 
            "label": "TOTAL IN<br>TOTAL OUT", 
            "fieldtype": "Data", 
            "width": 140,
            "align": "right"
        },

        # KOLOM 3: Beginning / Ending (Qty)
        {
            "fieldname": "balance_qty", 
            "label": "BEGINNING QTY<br>ENDING QTY", 
            "fieldtype": "Data", 
            "width": 140,
            "align": "right"
        },

        # KOLOM 4: Beginning Cost / Ending Cost
        {
            "fieldname": "cost_info", 
            "label": "BEGINNING COST<br>ENDING COST", 
            "fieldtype": "Data", 
            "width": 140,
            "align": "right"
        },

        # KOLOM 5: Beginning Value / Ending Value
        {
            "fieldname": "value_info", 
            "label": "BEGINNING VALUE<br>ENDING VALUE", 
            "fieldtype": "Data", 
            "width": 140,
            "align": "right"
        }
    ]

def get_data(filters):
    
    # Query SQL (Tidak ada perubahan pada SQL)
    sql = """
        WITH Aggregates AS (
            SELECT
                sle.item_code,
                
                -- SALDO AWAL
                SUM(IF(sle.posting_date < %(from_date)s, sle.actual_qty, 0)) AS beginning_qty,
                SUM(IF(sle.posting_date < %(from_date)s, sle.stock_value_difference, 0)) AS beginning_value,
                
                -- MUTASI MASUK
                SUM(IF(sle.posting_date BETWEEN %(from_date)s AND %(to_date)s AND sle.actual_qty > 0, sle.actual_qty, 0)) AS total_in_qty,
                
                -- MUTASI KELUAR
                SUM(IF(sle.posting_date BETWEEN %(from_date)s AND %(to_date)s AND sle.actual_qty < 0, sle.actual_qty, 0)) AS total_out_qty

            FROM 
                `tabStock Ledger Entry` AS sle
            WHERE
                sle.posting_date <= %(to_date)s
                AND sle.is_cancelled = 0
            GROUP BY
                sle.item_code
        ),

        LastTransaction AS (
            SELECT
                sle.item_code,
                sle.qty_after_transaction AS ending_qty_ledger,
                sle.valuation_rate AS ending_rate_ledger,
                sle.stock_value AS ending_value_ledger,
                
                ROW_NUMBER() OVER(
                    PARTITION BY sle.item_code 
                    ORDER BY 
                        sle.posting_date DESC,
                        sle.posting_time DESC,
                        sle.name DESC
                ) AS rn
            FROM
                `tabStock Ledger Entry` AS sle
            WHERE
                sle.posting_date <= %(to_date)s
                AND sle.is_cancelled = 0
        )

        SELECT
            i.name as item_code,
            i.item_name,
            i.stock_uom,
            
            COALESCE(agg.beginning_qty, 0) AS beginning_qty,
            COALESCE(agg.beginning_value, 0) AS beginning_value,
            
            COALESCE(agg.total_in_qty, 0) AS total_in_qty,
            COALESCE(agg.total_out_qty, 0) AS total_out_qty,
            
            COALESCE(lt.ending_qty_ledger, 0) AS ending_qty,
            COALESCE(lt.ending_value_ledger, 0) AS ending_value,
            COALESCE(lt.ending_rate_ledger, 0) AS ending_rate
            
        FROM 
            `tabItem` AS i
        LEFT JOIN 
            Aggregates AS agg ON i.name = agg.item_code
        LEFT JOIN 
            LastTransaction AS lt ON i.name = lt.item_code AND lt.rn = 1
        WHERE
            i.is_stock_item = 1
            AND (
                COALESCE(lt.ending_qty_ledger, 0) != 0 
                OR COALESCE(agg.total_in_qty, 0) != 0 
                OR COALESCE(agg.total_out_qty, 0) != 0
                OR COALESCE(agg.beginning_qty, 0) != 0
            )
        ORDER BY
            i.name ASC
    """

    raw_data = frappe.db.sql(sql, filters, as_dict=True)
    
    final_data = []
    company_currency = frappe.get_cached_value('Company',  frappe.defaults.get_user_default("Company"),  "default_currency") or "IDR"
    
    style_row = "font-size: 10px; line-height: 1.5; color: #36414c;"
    style_bold = "font-weight: bold; color: #333;"

    for row in raw_data:
        uom = row.stock_uom
        desc = (row.item_name or "").strip()

        if desc:
            row["item_info"] = (
                f'<div style="{style_row}">'
                f'<span style="{style_bold}">{row.item_code}</span><br>'
                f'{desc}'
                f'</div>'
            )
        else:
            row["item_info"] = (
                f'<div style="{style_row}">'
                f'<span style="{style_bold}">{row.item_code}</span>'
                f'</div>'
            )
        
        # --- 2. MUTATION QTY ---
        in_qty_fmt = f"{flt(row.total_in_qty):,.2f} {uom}"
        out_qty_fmt = f"{flt(row.total_out_qty):,.2f} {uom}" 
        
        row["mutation_qty"] = f"""
            <div style="{style_row}">
                {in_qty_fmt}<br>
                {out_qty_fmt}
            </div>
        """

        # --- 3. BALANCE QTY ---
        beg_qty_val = flt(row.beginning_qty)
        end_qty_val = flt(row.ending_qty) 
        
        beg_qty_fmt = f"{beg_qty_val:,.2f} {uom}"
        end_qty_fmt = f"{end_qty_val:,.2f} {uom}"
        
        row["balance_qty"] = f"""
            <div style="{style_row}">
                {beg_qty_fmt}<br>
                <span style="{style_bold}">{end_qty_fmt}</span>
            </div>
        """

        # --- 4. COST (RATE) & VALUE CALCULATION ---
        
        # A. Hitung Beginning Rate
        # Kita ambil total value dari SQL dulu hanya untuk mencari rata-rata harga (Rate)
        raw_beg_val_sum = flt(row.beginning_value)
        
        if beg_qty_val != 0:
            beg_rate = raw_beg_val_sum / beg_qty_val
        else:
            beg_rate = 0.0

        # B. Hitung Ending Rate
        if end_qty_val == 0:
            end_rate = 0.0
        else:
            end_rate = flt(row.ending_rate)

        # C. Hitung VALUE Berdasarkan Rumus Baru (Qty * Rate)
        # Sesuai request: Ending Value = Ending Qty x Ending Cost
        # Beginning Value = Beginning Qty x Beginning Cost
        
        calculated_beg_value = beg_qty_val * beg_rate
        calculated_end_value = end_qty_val * end_rate

        # --- FORMAT DISPLAY ---

        # Format Currency untuk Rate
        beg_rate_fmt = fmt_money(beg_rate, currency=company_currency)
        end_rate_fmt = fmt_money(end_rate, currency=company_currency)
        
        row["cost_info"] = f"""
            <div style="{style_row}">
                {beg_rate_fmt}<br>
                <span style="{style_bold}">{end_rate_fmt}</span>
            </div>
        """

        # --- 5. VALUE (MENGGUNAKAN HASIL KALKULASI BARU) ---
        # Format Currency untuk Value yang baru dihitung
        beg_val_fmt = fmt_money(calculated_beg_value, currency=company_currency)
        end_val_fmt = fmt_money(calculated_end_value, currency=company_currency)
        
        row["value_info"] = f"""
            <div style="{style_row}">
                {beg_val_fmt}<br>
                <span style="{style_bold}">{end_val_fmt}</span>
            </div>
        """

        final_data.append(row)

    return final_data