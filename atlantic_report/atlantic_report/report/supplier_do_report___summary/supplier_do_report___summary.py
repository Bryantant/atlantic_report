# Copyright (c) 2025
# Supplier DO Report - Summary

import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": "PR Date",
            "fieldname": "pr_date",
            "fieldtype": "Data",
            "width": 110
        },
        {
            "label": "PR No",
            "fieldname": "pr_no",
            "fieldtype": "Link",
            "options": "Purchase Receipt",
            "width": 140
        },
        {
            "label": "PO Date",
            "fieldname": "po_date",
            "fieldtype": "Data",
            "width": 110
        },
        {
            "label": "Supplier Name",
            "fieldname": "supplier",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "Received By",
            "fieldname": "received_by",
            "fieldtype": "Data",
            "width": 140
        },
        {
            "label": "Status",
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 100
        },
    ]


def get_data(filters):
    sql = """
        SELECT
            DATE_FORMAT(pr.posting_date, '%%d-%%b-%%y') AS pr_date,
            pr.name AS pr_no,
            DATE_FORMAT(po.transaction_date, '%%d-%%b-%%y') AS po_date,
            pr.supplier AS supplier,
            pr.custom_received_by AS received_by,
            pr.status AS status
        FROM
            `tabPurchase Receipt` AS pr
        LEFT JOIN
            `tabPurchase Receipt Item` AS pri ON pri.parent = pr.name
        LEFT JOIN
            `tabPurchase Order` AS po ON po.name = pri.purchase_order
        WHERE
            pr.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY
            pr.name, po.name
        ORDER BY
            pr.posting_date ASC, pr.name ASC
    """

    return frappe.db.sql(sql, filters, as_dict=True)
