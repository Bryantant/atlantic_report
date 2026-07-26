# Copyright (c) 2025, Takwindo
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import formatdate, flt, add_months, today, fmt_money
import re

# ============================================================
# AGGRESSIVE TEXT SANITIZER
# ============================================================
def clean_text(text):
    """Bersihkan text dari newline, tab, spasi berlebih, dll."""
    if text is None:
        return "-"
    t = str(text)

    # Hapus newline, carriage return, tab
    t = t.replace("\n", " ").replace("\r", " ").replace("\t", " ")

    # Multi-space -> single space
    t = re.sub(r"\s{2,}", " ", t)

    # Hapus whitespace di antara tag HTML
    t = re.sub(r">\s+<", "><", t)

    t = t.strip()
    return t or "-"

# ============================================================
def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

# ============================================================
def get_columns():
    return [
        {
            "label": "PR NO / PO NO<br>PR DATE / PO DATE<br>RECEIVED BY",
            "fieldname": "pr_info",
            "fieldtype": "Data",
            "width": 230,
            "align": "left",
        },
        {
            "label": "SUPPLIER NAME",
            "fieldname": "supplier",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": "STATUS",
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "ITEM CODE / BRAND<br>DESCRIPTION",
            "fieldname": "item_info",
            "fieldtype": "Data",
            "width": 300,
            "align": "left",
        },
        {
            "label": "QTY<br>UOM",
            "fieldname": "qty_info",
            "fieldtype": "Data",
            "width": 90,
            "align": "right",
        },
        {
            "label": "CCY",
            "fieldname": "currency_info",
            "fieldtype": "Data",
            "width": 50,
            "align": "center",
        },
        {
            "label": "PRICE",
            "fieldname": "rate_info",
            "fieldtype": "Data",
            "width": 110,
            "align": "right",
        },
        {
            "label": "TOTAL",
            "fieldname": "amount_info",
            "fieldtype": "Data",
            "width": 120,
            "align": "right",
        },
    ]

# ============================================================
def get_data(filters):
    if not filters:
        filters = frappe._dict()

    if not filters.get("from_date"):
        filters.from_date = add_months(today(), -1)
    if not filters.get("to_date"):
        filters.to_date = today()

    sql = """
        SELECT
            pr.name AS pr_no,
            pr.posting_date AS pr_date,
            pr.custom_received_by,
            pr.supplier,
            pr.status,
            pr.currency,
            pr.grand_total,

            pri.purchase_order AS po_no,
            po.transaction_date AS po_date,

            pri.item_code,
            pri.item_name,
            pri.description,
            pri.qty,
            pri.uom,
            pri.rate,
            pri.amount,

            i.brand

        FROM `tabPurchase Receipt` AS pr
        JOIN `tabPurchase Receipt Item` AS pri ON pri.parent = pr.name
        LEFT JOIN `tabPurchase Order` AS po ON po.name = pri.purchase_order
        LEFT JOIN `tabItem` AS i ON i.name = pri.item_code
        WHERE
            pr.docstatus = 1
            AND pr.posting_date BETWEEN %(from_date)s AND %(to_date)s
        ORDER BY
            pr.name ASC
    """

    raw_data = frappe.db.sql(sql, filters, as_dict=True)

    # Style basic (tanpa bold, font-size 10px)
    style_norm = "font-size:10px; color:#333;"

    processed = []
    last_pr = None

    totals_by_ccy = {}

    for row in raw_data:
        ccy = clean_text(row.currency)

        if ccy not in totals_by_ccy:
            totals_by_ccy[ccy] = {"grand_total": 0.0, "qty": 0.0}

        totals_by_ccy[ccy]["qty"] += flt(row.qty)

        # ========== CLEAN TEXT FIELD ==========
        pr_no_txt   = clean_text(row.pr_no)
        po_no_txt   = clean_text(row.po_no) if row.po_no else "-"
        rec_by_txt  = clean_text(row.custom_received_by) if row.custom_received_by else "-"
        supp_name   = clean_text(row.supplier)
        status_txt  = clean_text(row.status)
        item_code   = clean_text(row.item_code)
        item_name   = clean_text(row.item_name)
        brand_txt   = clean_text(row.brand) if row.brand else "-"
        # description fallback ke item_name kalau kosong
        desc_src    = row.description if row.description else item_name
        desc_txt    = clean_text(desc_src)

        # ========== ITEM INFO: 3 BARIS KONSISTEN ==========
        line1 = f'<span style="{style_norm}">{item_code} / {brand_txt}</span>'
        line2 = f'<span style="{style_norm}">{desc_txt}</span>'
        line3 = ''

        row["item_info"] = line1 + "<br>" + line2

        # ========== QTY INFO ==========
        qty_val = flt(row.qty)
        row["qty_info"] = (
            f'<span style="{style_norm}">{qty_val:,.2f}</span><br>'
            f'<span style="{style_norm}">{clean_text(row.uom)}</span>'
        )

        # ========== PRICE & AMOUNT ==========
        price = fmt_money(row.rate, currency=ccy)
        amt = fmt_money(row.amount, currency=ccy)

        row["rate_info"] = f'<span style="{style_norm}">{price}</span>'
        row["amount_info"] = f'<span style="{style_norm}">{amt}</span>'

        # ========== HEADER PER PR ==========
        if last_pr == row.pr_no:
            # Baris lanjutan dari PR yang sama -> kosongkan info header
            row["pr_info"] = ""
            row["supplier"] = ""
            row["status"] = ""
            row["currency_info"] = ""
        else:
            totals_by_ccy[ccy]["grand_total"] += flt(row.grand_total)

            pr_date_str = formatdate(row.pr_date, "dd-MMM-yy") if row.pr_date else "-"
            po_date_str = formatdate(row.po_date, "dd-MMM-yy") if row.po_date else "-"

            row["pr_info"] = (
                f'<span style="{style_norm}">{pr_no_txt}</span> / '
                f'<span style="{style_norm}">{po_no_txt}</span><br>'
                f'<span style="{style_norm}">{pr_date_str}</span> / '
                f'<span style="{style_norm}">{po_date_str}</span><br>'
                f'<span style="{style_norm}">Rec By: {rec_by_txt}</span>'
            )

            # supplier TIDAK dibold di sini (bold diatur di JS/HTML)
            row["supplier"] = f'<span style="{style_norm}">{supp_name}</span>'
            row["status"] = f'<span style="{style_norm}">{status_txt}</span>'
            row["currency_info"] = f'<span style="{style_norm}">{ccy}</span>'

            last_pr = row.pr_no

        processed.append(row)

    # =====================================================
    # TOTAL ROW PER CURRENCY
    # =====================================================
    if processed:
        for ccy, vals in totals_by_ccy.items():
            style_total = "font-size:10px; font-weight:bold; color:#333;"

            total_amt_html = (
                f'<span style="{style_total}">'
                f'{fmt_money(vals["grand_total"], currency=ccy)}'
                f'</span>'
            )
            total_qty_html = (
                f'<span style="{style_total}">{flt(vals["qty"]):,.2f}</span>'
            )

            label_html = (
                '<div style="text-align:right; font-size:10px; font-weight:bold;">'
                f'TOTAL ({ccy}) :'
                '</div>'
            )

            processed.append(
                {
                    "pr_info": label_html,
                    "supplier": "",
                    "status": "",
                    "item_info": "",
                    "qty_info": total_qty_html,
                    "currency_info": f'<span style="{style_total}">{ccy}</span>',
                    "rate_info": "",
                    "amount_info": total_amt_html,
                    "is_total_row": True,
                }
            )

    return processed
