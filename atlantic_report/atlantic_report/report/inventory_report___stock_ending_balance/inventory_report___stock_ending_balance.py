import frappe
from frappe.utils import flt, add_months, today, fmt_money


def execute(filters=None):
    if not filters:
        filters = frappe._dict()

    if not filters.from_date:
        filters.from_date = add_months(today(), -1)

    if not filters.to_date:
        filters.to_date = today()

    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():

    return [
        {
            "fieldname": "item_info",
            "label": "ITEM CODE<br>DESCRIPTION",
            "fieldtype": "Data",
            "width": 650
        },
        {
            "fieldname": "qty_info",
            "label": "ENDING QTY<br>UOM",
            "fieldtype": "Data",
            "width": 120,
            "align": "right"
        },
        {
            "fieldname": "value_info",
            "label": "VALUATION RATE<br>ENDING VALUE",
            "fieldtype": "Data",
            "width": 150,
            "align": "right"
        }
    ]


def get_data(filters):

    sql = """
        WITH aggregated AS (

            SELECT
                sle.item_code,

                SUM(CASE WHEN sle.posting_date < %(from_date)s
                    THEN sle.actual_qty ELSE 0 END) AS beginning_qty,

                SUM(CASE WHEN sle.posting_date < %(from_date)s
                    THEN sle.stock_value_difference ELSE 0 END) AS beginning_value,

                SUM(CASE WHEN sle.posting_date BETWEEN %(from_date)s AND %(to_date)s
                    AND sle.actual_qty > 0 THEN sle.actual_qty ELSE 0 END) AS qty_in,

                SUM(CASE WHEN sle.posting_date BETWEEN %(from_date)s AND %(to_date)s
                    AND sle.actual_qty < 0 THEN sle.actual_qty ELSE 0 END) AS qty_out,

                SUM(CASE WHEN sle.posting_date BETWEEN %(from_date)s AND %(to_date)s
                    THEN sle.stock_value_difference ELSE 0 END) AS value_diff

            FROM `tabStock Ledger Entry` sle
            WHERE sle.docstatus = 1
              AND sle.is_cancelled = 0
              AND sle.posting_date <= %(to_date)s
            GROUP BY sle.item_code
        )

        SELECT
            i.name AS item_code,
            i.item_name,
            i.stock_uom,

            COALESCE(a.beginning_qty, 0) AS beginning_qty,
            COALESCE(a.beginning_value, 0) AS beginning_value,
            COALESCE(a.qty_in, 0) AS qty_in,
            COALESCE(a.qty_out, 0) AS qty_out,
            COALESCE(a.value_diff, 0) AS value_diff

        FROM `tabItem` i
        LEFT JOIN aggregated a ON a.item_code = i.name
        WHERE i.is_stock_item = 1
        ORDER BY i.name ASC
    """

    rows = frappe.db.sql(sql, filters, as_dict=True)

    result = []
    company = frappe.defaults.get_user_default("Company")
    currency = frappe.get_cached_value("Company", company, "default_currency") or "IDR"

    total_qty_all = 0
    total_value_all = 0

    for r in rows:

        ending_qty = flt(r.beginning_qty) + flt(r.qty_in) + flt(r.qty_out)
        base_value = flt(r.beginning_value) + flt(r.value_diff)

        ending_rate = (base_value / ending_qty) if ending_qty > 0 else 0
        ending_value = ending_qty * ending_rate

        # Skip kosong
        if ending_qty == 0 and r.beginning_qty == 0 and r.qty_in == 0 and r.qty_out == 0:
            continue

        # Akumulasi total
        total_qty_all += ending_qty
        total_value_all += ending_value

        # =============== ITEM INFO ===============
        desc = (r.item_name or "").strip()
        r["item_info"] = f"<b>{r.item_code}</b><br>{desc}"

        # =============== QTY INFO ===============
        r["qty_info"] = f"""
            <div style='text-align:right'>
                {ending_qty:,.2f}<br>
                {r.stock_uom}
            </div>
        """

        # =============== VALUE INFO (HTML) ===============
        r["value_info"] = f"""
            <div style='text-align:right'>
                {ending_rate:,.2f}<br>
                {ending_value:,.2f}
            </div>
        """

        result.append(r)

    # =============== TOTAL ROW ===============
    if result:
        result.append({
            "item_info": "<div style='text-align:right;font-weight:bold;'>TOTAL :</div>",
            "qty_info": f"<div style='font-weight:bold;text-align:right'>{total_qty_all:,.2f}</div>",
            "value_info": f"<div style='font-weight:bold;text-align:right'>{total_value_all:,.2f}</div>",
            "is_total_row": 1
        })

    return result
