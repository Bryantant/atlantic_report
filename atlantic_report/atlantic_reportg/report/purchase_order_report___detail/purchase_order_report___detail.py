# Copyright (c) 2025, Takwindo

import frappe
from frappe.utils import formatdate, flt, fmt_money
import re

# ============================================================
# AGGRESSIVE SANITIZER (hapus semua whitespace liar)
# ============================================================
def clean_text(text):
    if not text:
        return "-"
    
    t = str(text)

    # Hapus newline, tab, CR
    t = t.replace("\n", " ").replace("\r", " ").replace("\t", " ")

    # Hapus spasi antar-tag HTML
    t = re.sub(r'>\s+<', '><', t)

    # Multiple spaces → single space
    t = re.sub(r'\s{2,}', ' ', t)

    # Trim
    t = t.strip()

    return t or "-"


# ============================================================
# MAIN EXECUTE
# ============================================================
def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


# ============================================================
# COLUMNS
# ============================================================
def get_columns():
    return [
        {"label": "PO NO. / STATUS<br>NAME", "fieldname": "po_info", "fieldtype": "Data", "width": 190},
        {"label": "SUPPLIER NAME<br>PO DATE", "fieldname": "supp_info", "fieldtype": "Data", "width": 250},
        {"label": "CCY<br>TOTAL PO", "fieldname": "ccy_info", "fieldtype": "Data", "width": 110, "align": "right"},

        {"label": "ITEM CODE / BRAND<br>DESCRIPTION", "fieldname": "item_info", "fieldtype": "Data", "width": 300},

        {"label": "ORDER<br>REC.<br>RETURN", "fieldname": "qty_info", "fieldtype": "Data", "width": 100, "align": "right"},
        {"label": "U/M<br>PRICE<br>TOTAL", "fieldname": "amount_info", "fieldtype": "Data", "width": 140, "align": "right"},
    ]


# ============================================================
# GET DATA
# ============================================================
def get_data(filters):
    if not filters:
        filters = frappe._dict()

    conditions = ""
    if filters.from_date and filters.to_date:
        conditions += " AND po.transaction_date BETWEEN %(from_date)s AND %(to_date)s"

    sql = f"""
        SELECT
            po.name as po_no,
            po.status,
            po.custom_order_by,
            po.supplier,
            po.transaction_date,
            po.currency,
            po.grand_total,

            poi.item_code,
            poi.description,
            poi.qty,
            poi.received_qty,
            poi.returned_qty,
            poi.uom,
            poi.rate,
            poi.amount,

            i.brand

        FROM `tabPurchase Order` po
        INNER JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
        LEFT JOIN `tabItem` i ON i.name = poi.item_code
        WHERE po.docstatus = 1
        {conditions}
        ORDER BY po.name ASC, poi.idx ASC
    """

    rows = frappe.db.sql(sql, filters, as_dict=True)

    # Styles
    style_label = "font-size:10px; color:#777;"
    style_val   = "font-size:10px; font-weight:bold; color:#333;"
    style_norm  = "font-size:10px; color:#333;"

    processed = []
    last_po = None
    totals_by_ccy = {}

    # ============================================================
    # MAIN ROW PROCESSING
    # ============================================================
    for r in rows:

        ccy = r.currency
        if ccy not in totals_by_ccy:
            totals_by_ccy[ccy] = {'grand_total': 0.0, 'qty': 0.0, 'rec': 0.0, 'ret': 0.0}

        totals_by_ccy[ccy]['qty'] += flt(r.qty)
        totals_by_ccy[ccy]['rec'] += flt(r.received_qty)
        totals_by_ccy[ccy]['ret'] += flt(r.returned_qty)

        # CLEANING FIELD AGGRESSIVELY
        item_code = clean_text(r.item_code)
        brand     = clean_text(r.brand)
        desc      = clean_text(r.description)
        supplier  = clean_text(r.supplier)
        custom_ord = clean_text(r.custom_order_by)

        # ITEM INFO
        r["item_info"] = (
            f'<span style="{style_val}">{item_code} / {brand}</span>'
            '<br>'
            f'<span style="{style_norm}">{desc}</span>'
        )

        # QTY INFO
        r["qty_info"] = (
            f'<span style="{style_val}">{flt(r.qty):,.0f}</span>'
            '<br>'
            f'<span style="{style_norm}">{flt(r.received_qty):,.0f}</span>'
            '<br>'
            f'<span style="{style_norm}">{flt(r.returned_qty):,.2f}</span>'
        )

        # PRICE + AMOUNT
        price = fmt_money(r.rate, currency=r.currency)
        amt   = fmt_money(r.amount, currency=r.currency)

        r["amount_info"] = (
            f'<span style="{style_norm}">{clean_text(r.uom)}</span>'
            '<br>'
            f'<span style="{style_norm}">{price}</span>'
            '<br>'
            f'<span style="{style_val}">{amt}</span>'
        )

        # HEADER DISPLAY (only once per PO)
        if last_po == r.po_no:
            r["po_info"] = ""
            r["supp_info"] = ""
            r["ccy_info"] = ""
        else:
            totals_by_ccy[ccy]['grand_total'] += flt(r.grand_total)
            d = formatdate(r.transaction_date, "dd-MMM-yy")

            r["po_info"] = (
                f'<span style="{style_val}">{clean_text(r.po_no)}</span> / '
                f'<span style="{style_norm}">{clean_text(r.status)}</span>'
                '<br>'
                f'<span style="{style_norm}">{custom_ord}</span>'
            )

            r["supp_info"] = (
                f'<span style="{style_val}">{supplier}</span>'
                '<br>'
                f'<span style="{style_norm}">{d}</span>'
            )

            total_fmt = fmt_money(r.grand_total, currency=r.currency)
            r["ccy_info"] = (
                f'<span style="{style_val}">{ccy}</span>'
                '<br>'
                f'<span style="{style_val}">{total_fmt}</span>'
            )

            last_po = r.po_no

        processed.append(r)

    # ============================================================
    # TOTAL PER CURRENCY
    # ============================================================
    if processed:
        for ccy, vals in totals_by_ccy.items():

            total_po_html = (
                f'<span style="{style_val}">{ccy}</span>'
                '<br>'
                f'<span style="{style_val}">{fmt_money(vals["grand_total"], currency=ccy)}</span>'
            )

            total_qty_html = (
                f'<span style="{style_val}">{vals["qty"]:,.0f}</span>'
                '<br>'
                f'<span style="{style_norm}">{vals["rec"]:,.0f}</span>'
                '<br>'
                f'<span style="{style_norm}">{vals["ret"]:,.2f}</span>'
            )

            label_html = (
                '<br>'
                '<div style="text-align:right; font-weight:bold; font-size:10px;">'
                f'TOTAL ({ccy}) :</div>'
            )

            processed.append({
                "po_info": label_html,
                "supp_info": "",
                "ccy_info": total_po_html,
                "item_info": "",
                "qty_info": total_qty_html,
                "amount_info": "",
                "is_total_row": True
            })

    return processed
