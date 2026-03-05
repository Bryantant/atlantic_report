// Statement of Account Payables - By Month

frappe.query_reports["Statement of Account Payables"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "supplier",
            "label": __("Supplier"),
            "fieldtype": "Link",
            "options": "Supplier"
        }
    ],

    "formatter": function (value, row, column, data, default_formatter) {

        let content = default_formatter(value, row, column, data);
        if (!data) return content;

        // Format tanggal
        if (column.fieldname === "date" && value) {
            return `<span style="font-size:12px;">${moment(value).format("DD-MMM-YYYY")}</span>`;
        }

        // HEADER SUPPLIER (indent = 0)
        if (data.indent === 0) {
            if (column.fieldname === "reff") {
                return `<span style="font-weight:bold; font-size:12px;">${content}</span>`;
            }
            // kolom lain di header kosong
            return "";
        }

        // DETEKSI row TOTAL / GRAND TOTAL
        let is_total_row = !!data.is_total_row || !!data.is_grand_total;
        if (!is_total_row) {
            if (data.reff && data.reff.toString().includes("TOTAL")) is_total_row = true;
            if (data.bill_no && data.bill_no.toString().includes("TOTAL")) is_total_row = true;
        }

        // Row BALANCE (opening)
        let is_balance_row = data.bill_no && data.bill_no.toString().includes("BALANCE");

        // Hapus TRM 0
        if (column.fieldname === "trm" && (value === 0 || value === "0" || value === 0.0)) {
            return "";
        }

        // DEBIT & CREDIT 0 → "---"
        if (["debit", "credit"].includes(column.fieldname)) {
            let rawVal = data[column.fieldname];
            if (rawVal === 0 || rawVal === 0.0) {
                return `<span style="font-size:12px; display:block; text-align:right; width:100%;">---</span>`;
            }
        }

        // Styling untuk row TOTAL
        if (is_total_row) {
            // Balance di row total dikosongkan
            if (column.fieldname === "balance") {
                return "";
            }
            if (["reff", "bill_no", "debit", "credit"].includes(column.fieldname)) {
                return `<b><span style="font-size:12px;">${content}</span></b>`;
            }
        }

        // Styling untuk row BALANCE (opening)
        if (is_balance_row) {
            if (["bill_no", "balance"].includes(column.fieldname)) {
                return `<b><span style="font-size:12px;">${content}</span></b>`;
            }
            if (["trm", "currency_display"].includes(column.fieldname)) {
                return "";
            }
        }

        // default
        return `<span style="font-size:12px;">${content}</span>`;
    }
};
