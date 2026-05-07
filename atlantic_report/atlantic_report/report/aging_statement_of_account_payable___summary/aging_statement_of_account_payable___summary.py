# Aging Statement of AP - Summary
# Copyright (c) 2025

import frappe
from frappe import _
from frappe.utils import date_diff, getdate, flt, nowdate, today


def execute(filters=None):
    if not filters:
        filters = frappe._dict()

    if not filters.to_date:
        filters.to_date = today()

    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"fieldname": "supplier_display", "label": _("Supplier"), "fieldtype": "Link", "options": "Supplier", "width": 220},
        {"fieldname": "currency", "label": _("Ccy"), "fieldtype": "Data", "width": 50},

        {"fieldname": "total_outstanding", "label": _("Total"), "fieldtype": "Currency", "options": "currency", "width": 135},

        {"fieldname": "range1", "label": _("< 31 Days"), "fieldtype": "Currency", "options": "currency", "width": 100},
        {"fieldname": "range2", "label": _("31 - 60 Days"), "fieldtype": "Currency", "options": "currency", "width": 100},
        {"fieldname": "range3", "label": _("61 - 90 Days"), "fieldtype": "Currency", "options": "currency", "width": 100},
        {"fieldname": "range4", "label": _("91 - 150 Days"), "fieldtype": "Currency", "options": "currency", "width": 100},
        {"fieldname": "range5", "label": _("> 150 Days"), "fieldtype": "Currency", "options": "currency", "width": 100},

        {"fieldname": "outstanding_end", "label": _("Outstanding"), "fieldtype": "Currency", "options": "currency", "width": 135}
    ]


def get_data(filters):
    params = {
        "to_date": filters.get("to_date"),
        "supplier": filters.get("supplier"),
        "from_date": filters.get("from_date"),
    }

    sql = """
        SELECT
            supplier,
            supplier_name,
            posting_date,
            currency,
            (grand_total - paid_amount) AS outstanding_amount
        FROM `tabPurchase Invoice`
        WHERE
            docstatus = 1
            AND outstanding_amount > 0
            AND posting_date <= %(to_date)s
            AND (%(supplier)s IS NULL OR supplier = %(supplier)s)
            AND (%(from_date)s IS NULL OR posting_date >= %(from_date)s)
        ORDER BY supplier ASC
    """

    invoices = frappe.db.sql(sql, params, as_dict=True)

    summary_map = {}
    today_realtime = getdate(nowdate())

    for row in invoices:
        key = (row.supplier, row.currency)

        if key not in summary_map:
            summary_map[key] = {
                "supplier": row.supplier,
                "supplier_name": row.supplier_name,
                "currency": row.currency,
                "total": 0.0,
                "r1": 0.0,
                "r2": 0.0,
                "r3": 0.0,
                "r4": 0.0,
                "r5": 0.0,
            }

        # hitung aging
        age_days = date_diff(today_realtime, getdate(row.posting_date))
        amt = flt(row.outstanding_amount)

        summary_map[key]["total"] += amt

        if age_days < 31:
            summary_map[key]["r1"] += amt
        elif 31 <= age_days <= 60:
            summary_map[key]["r2"] += amt
        elif 61 <= age_days <= 90:
            summary_map[key]["r3"] += amt
        elif 91 <= age_days <= 150:
            summary_map[key]["r4"] += amt
        else:
            summary_map[key]["r5"] += amt

    final_data = []
    grand_totals = {}

    for key, item in summary_map.items():
        ccy = item["currency"]

        final_data.append({
            "supplier_display": item["supplier"],
            "currency": ccy,
            "total_outstanding": item["total"],
            "range1": item["r1"],
            "range2": item["r2"],
            "range3": item["r3"],
            "range4": item["r4"],
            "range5": item["r5"],
            "outstanding_end": item["total"]
        })

        # grand total per currency
        if ccy not in grand_totals:
            grand_totals[ccy] = {"t": 0, "r1": 0, "r2": 0, "r3": 0, "r4": 0, "r5": 0}

        grand_totals[ccy]["t"] += item["total"]
        grand_totals[ccy]["r1"] += item["r1"]
        grand_totals[ccy]["r2"] += item["r2"]
        grand_totals[ccy]["r3"] += item["r3"]
        grand_totals[ccy]["r4"] += item["r4"]
        grand_totals[ccy]["r5"] += item["r5"]

    # append GRAND TOTAL rows
    for ccy, totals in grand_totals.items():
        if totals["t"] > 0:
            final_data.append({
                "supplier_display": f"Total ({ccy})",
                "currency": ccy,
                "total_outstanding": totals["t"],
                "range1": totals["r1"],
                "range2": totals["r2"],
                "range3": totals["r3"],
                "range4": totals["r4"],
                "range5": totals["r5"],
                "outstanding_end": totals["t"],
                "is_total_row": True
            })

    return final_data
