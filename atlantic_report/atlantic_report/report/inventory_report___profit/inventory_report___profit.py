# Copyright (c) 2025
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, add_months, today

# ------------------------------------------------------
# MAIN EXECUTE FUNCTION
# ------------------------------------------------------
def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data


# ------------------------------------------------------
# COLUMNS
# ------------------------------------------------------
def get_columns(filters):
    
    uom_label = filters.uom if filters and filters.get("uom") else "Kg"

    return [
        {
            "fieldname": "item_info", 
            "label": "ITEM CODE<br>DESCRIPTION", 
            "fieldtype": "Data", 
            "width": 400,
            "align": "left"
        },
        {
            "fieldname": "qty_info", 
            "label": f"({uom_label}) QTY SALE<br>QTY RETURN", 
            "fieldtype": "Data", 
            "width": 150, 
            "align": "right"
        },
        {
            "fieldname": "sales_ret_amt", 
            "label": "($) SALES AMOUNT<br>RETURN AMOUNT", 
            "fieldtype": "Data", 
            "width": 150, 
            "align": "right"
        },
        {
            "fieldname": "cost_info", 
            "label": "($) COST AMOUNT<br>COST RET. AMT", 
            "fieldtype": "Data", 
            "width": 150, 
            "align": "right"
        },
        {
            "fieldname": "profit_info", 
            "label": "($) GROSS PROFIT<br>NET PROFIT", 
            "fieldtype": "Data", 
            "width": 150, 
            "align": "right"
        },
        {
            "fieldname": "percent", 
            "label": "(%)", 
            "fieldtype": "Data", 
            "width": 60, 
            "align": "right"
        }
    ]


# ------------------------------------------------------
# DATA PROCESSING
# ------------------------------------------------------
def get_data(filters):
    if not filters:
        filters = frappe._dict()

    if not filters.from_date:
        filters.from_date = add_months(today(), -1)

    if not filters.to_date:
        filters.to_date = today()

    params = {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        "uom": filters.get("uom"),
    }

    sql = """
        SELECT
            sii.item_code,
            sii.item_name,

            SUM(IF(si.is_return = 0, sii.qty, 0)) AS qty_sale,
            SUM(IF(si.is_return = 1, sii.qty, 0)) AS qty_return,

            SUM(IF(si.is_return = 0, sii.base_net_amount, 0)) AS sale_amount,
            SUM(IF(si.is_return = 1, sii.base_net_amount, 0)) AS return_amount,

            SUM(IF(si.is_return = 0, (sii.qty * IFNULL(NULLIF(sii.incoming_rate, 0), IFNULL(dni.incoming_rate, 0))), 0)) AS cost_amount,
            SUM(IF(si.is_return = 1, (sii.qty * IFNULL(NULLIF(sii.incoming_rate, 0), IFNULL(dni.incoming_rate, 0))), 0)) AS cost_return_amt,

            MAX(si.currency) as currency,
            MAX(sii.stock_uom) as uom

        FROM
            `tabSales Invoice Item` AS sii
        JOIN
            `tabSales Invoice` AS si ON si.name = sii.parent
        LEFT JOIN
            `tabDelivery Note Item` AS dni ON dni.name = sii.dn_detail
        WHERE
            si.docstatus = 1
            AND (
                %(from_date)s IS NULL OR %(to_date)s IS NULL
                OR si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            )
            AND (%(uom)s IS NULL OR sii.stock_uom = %(uom)s)
        GROUP BY
            sii.item_code
        ORDER BY
            item_code
    """

    raw_data = frappe.db.sql(sql, params, as_dict=True)

    final_data = []
    style_div = "line-height: 1.5;"

    sum_qty_sale = sum_qty_ret = 0.0
    sum_sale_amt = sum_ret_amt = 0.0
    sum_cost_amt = sum_cost_ret = 0.0
    sum_gross_profit = sum_net_profit = 0.0

    for row in raw_data:
        uom = row.uom or ""

        sum_qty_sale += flt(row.qty_sale)
        sum_qty_ret += flt(row.qty_return)
        sum_sale_amt += flt(row.sale_amount)
        sum_ret_amt += flt(row.return_amount)
        sum_cost_amt += flt(row.cost_amount)
        sum_cost_ret += flt(row.cost_return_amt)

        gross_profit = flt(row.sale_amount) - flt(row.cost_amount)
        net_profit = gross_profit + (flt(row.cost_return_amt) - flt(row.return_amount))

        sum_gross_profit += gross_profit
        sum_net_profit += net_profit

        row["item_info"] = f"""
            <div style="{style_div}">
                {row.item_code}<br>
                {row.item_name}
            </div>
        """

        row["qty_info"] = f"""
            <div style="{style_div}">
                {flt(row.qty_sale):,.2f}<br>
                {flt(row.qty_return):,.2f}
            </div>
        """

        row["sales_ret_amt"] = f"""
            <div style="{style_div}">
                {flt(row.sale_amount):,.2f}<br>
                {flt(row.return_amount):,.2f}
            </div>
        """

        row["cost_info"] = f"""
            <div style="{style_div}">
                {flt(row.cost_amount):,.2f}<br>
                {flt(row.cost_return_amt):,.2f}
            </div>
        """

        row["profit_info"] = f"""
            <div style="{style_div}">
                {flt(gross_profit):,.2f}<br>
                {flt(net_profit):,.2f}
            </div>
        """

        cost_amt = flt(row.cost_amount)
        pct = 0 if cost_amt == 0 else (net_profit / cost_amt * 100)

        row["percent"] = f"""
            <div style="{style_div}">
                {pct:,.2f}
            </div>
        """

        final_data.append(row)

    if final_data:
        total_margin_pct = 0 if sum_cost_amt == 0 else (sum_net_profit / sum_cost_amt * 100)

        total_row = {
            "item_info": "<div style='text-align: right;'>TOTAL :</div>",

            "qty_info": f"""
                <div style="{style_div}">
                    {sum_qty_sale:,.2f}<br>
                    {sum_qty_ret:,.2f}
                </div>
            """,

            "sales_ret_amt": f"""
                <div style="{style_div}">
                    {flt(sum_sale_amt):,.2f}<br>
                    {flt(sum_ret_amt):,.2f}
                </div>
            """,

            "cost_info": f"""
                <div style="{style_div}">
                    {flt(sum_cost_amt):,.2f}<br>
                    {flt(sum_cost_ret):,.2f}
                </div>
            """,

            "profit_info": f"""
                <div style="{style_div}">
                    {flt(sum_gross_profit):,.2f}<br>
                    {flt(sum_net_profit):,.2f}
                </div>
            """,

            "percent": f"""
                <div style="{style_div}">
                    {total_margin_pct:,.2f}
                </div>
            """,

            "is_total_row": True
        }

        final_data.append(total_row)

    return final_data
