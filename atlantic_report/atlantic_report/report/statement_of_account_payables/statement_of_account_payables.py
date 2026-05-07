# Statement of Account Payables - By Month

import frappe
from frappe.utils import flt, today


def execute(filters=None):
    if not filters:
        filters = frappe._dict()

    if not filters.from_date:
        filters.from_date = today()
    if not filters.to_date:
        filters.to_date = today()

    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"fieldname": "date", "label": "DATE", "fieldtype": "Date", "width": 100},
        {
            "fieldname": "reff",
            "label": "REFF.",
            "fieldtype": "Dynamic Link",
            "options": "doctype",
            "width": 250,
        },
        {"fieldname": "currency_display", "label": "Ccy", "fieldtype": "Data", "width": 50},
        {"fieldname": "description", "label": "DESCRIPTION", "fieldtype": "Data", "width": 110},
        {"fieldname": "bill_no", "label": "BILL NO", "fieldtype": "Data", "width": 120},
        {"fieldname": "trm", "label": "TRM", "fieldtype": "Int", "width": 50},
        {"fieldname": "debit", "label": "DEBIT", "fieldtype": "Currency", "width": 120},
        {"fieldname": "credit", "label": "CREDIT", "fieldtype": "Currency", "width": 120},
        {"fieldname": "balance", "label": "BALANCE", "fieldtype": "Currency", "width": 120},
    ]


def get_data(filters):
    params = {"supplier": filters.get("supplier")}
    suppliers = frappe.db.sql(
        """
        SELECT name, supplier_name
        FROM `tabSupplier`
        WHERE docstatus < 2
          AND (%(supplier)s IS NULL OR name = %(supplier)s)
        ORDER BY name ASC
        """,
        params,
        as_dict=True,
    )

    final_data = []
    grand_totals = {}  # {ccy: {"debit": x, "credit": y}}

    for supp in suppliers:
        rows = get_by_month_transactions(supp.name, filters)

        # skip supplier tanpa transaksi
        if not rows:
            continue

        # HEADER SUPPLIER (indent = 0)
        final_data.append({
            "date": None,
            "reff": supp.name,
            "currency_display": "",
            "description": "",
            "bill_no": "",
            "trm": "",
            "debit": "",
            "credit": "",
            "balance": "",
            "indent": 0,
        })

        # DETAIL (indent = 1)
        final_data.extend(rows)

        # akumulasi GRAND TOTAL (hanya debit/credit, per currency)
        for r in rows:
            if r.get("is_opening_row") or r.get("is_total_row") or r.get("is_grand_total"):
                continue

            ccy = r.get("currency_display") or "SGD"
            if ccy not in grand_totals:
                grand_totals[ccy] = {"debit": 0.0, "credit": 0.0}

            grand_totals[ccy]["debit"] += flt(r.get("debit"))
            grand_totals[ccy]["credit"] += flt(r.get("credit"))

    # GRAND TOTAL per currency
    for ccy, t in grand_totals.items():
        final_data.append({
            "date": None,
            "reff": f"GRAND TOTAL ({ccy})",
            "currency_display": ccy,
            "description": "",
            "bill_no": "",
            "trm": "",
            "debit": t["debit"],
            "credit": t["credit"],
            "balance": "",
            "indent": 1,
            "is_total_row": 1,
            "is_grand_total": 1,
        })

    return final_data


def get_by_month_transactions(supplier, filters):
    """
    Ambil transaksi AP per supplier:
    - Debit/Credit pakai *_in_account_currency supaya sesuai dengan account_currency
    - Journal Entry (Journal Adj.) TIDAK ditampilkan
    """

    # Opening balance in invoice (transaction) currency
    opening_sql = """
        SELECT SUM(debit_in_transaction_currency - credit_in_transaction_currency)
        FROM `tabGL Entry`
        WHERE party_type = 'Supplier'
          AND party = %s
          AND posting_date < %s
          AND is_cancelled = 0
          AND voucher_type != 'Journal Entry'
    """
    opening_result = frappe.db.sql(opening_sql, (supplier, filters.from_date))
    opening_bal = flt(opening_result[0][0], 2) if opening_result else 0.0

    trans_sql = """
        SELECT
            gle.posting_date AS date,
            gle.voucher_no   AS reff,

            -- gunakan nilai & currency dari transaksi (invoice currency)
            gle.debit_in_transaction_currency  AS debit,
            gle.credit_in_transaction_currency AS credit,

            gle.transaction_currency AS currency,

            CASE 
                WHEN gle.voucher_type = 'Purchase Invoice' THEN 'INVOICE'
                WHEN gle.voucher_type = 'Payment Entry'   THEN 'PAYMENT'
                -- Journal Entry TIDAK diambil (lihat WHERE), jadi tidak perlu JOURNAL ADJ.
                ELSE gle.voucher_type 
            END AS description,

            CASE 
                WHEN gle.voucher_type = 'Purchase Invoice' THEN 
                    COALESCE(
                        (SELECT bill_no
                           FROM `tabPurchase Invoice`
                          WHERE name = gle.voucher_no
                          LIMIT 1),
                        gle.voucher_no
                    )
                ELSE gle.voucher_no 
            END AS bill_no,

            IF(gle.voucher_type = 'Purchase Invoice',
               DATEDIFF(
                   (SELECT due_date
                      FROM `tabPurchase Invoice`
                     WHERE name = gle.voucher_no),
                   gle.posting_date
               ),
               0
            ) AS trm

        FROM `tabGL Entry` gle
        WHERE
            gle.party_type = 'Supplier'
            AND gle.party = %s
            AND gle.posting_date BETWEEN %s AND %s
            AND gle.is_cancelled = 0
            AND gle.voucher_type != 'Journal Entry'   -- ⬅️ HILANGKAN JOURNAL ADJ
        ORDER BY gle.posting_date ASC, gle.creation ASC
    """

    transactions = frappe.db.sql(
        trans_sql, (supplier, filters.from_date, filters.to_date), as_dict=True
    )

    if not transactions:
        return []

    result = []
    curr = transactions[0].currency or "SGD"

    # OPENING BALANCE ROW
    result.append({
        "date": filters.from_date,
        "reff": "",
        "currency_display": "",
        "description": "",
        "bill_no": "BALANCE",
        "trm": "",
        "debit": "",
        "credit": "",
        "balance": opening_bal,
        "indent": 1,
        "is_opening_row": 1,
    })

    running_balance = opening_bal

    # DETAIL TRANSAKSI
    for row in transactions:
        # balance dalam transaction currency
        running_balance += flt(row.debit) - flt(row.credit)

        row.balance = flt(running_balance, 2)
        row.indent = 1
        row.currency_display = row.currency

        if row.trm == 0:
            row.trm = ""

        result.append(row)

    return result
