frappe.query_reports["Cust Payment Report - Per Off Receipt"] = {
    "filters": [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.year_start(),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        }
    ],

    formatter: function (value, row, column, data, default_formatter) {

        value = default_formatter(value, row, column, data);

        // base style
        let style = "font-size: 12px; white-space: nowrap;";

        // ============================================================
        // STYLE UNTUK ROW TOTAL
        // ============================================================
        if (data && data.is_total_row) {
            style += `
                font-weight: bold;
                color: #000;
            `;
        }

        // ============================================================
        // ALIGNMENT PER KOLOM
        // ============================================================

        // Angka currency → right align
        if (["paid_amount", "paid_with"].includes(column.fieldname)) {
            return `<div style="${style} text-align:right;">${value}</div>`;
        }

        // Currency code (SGD, USD, etc.) → center
        if (["currency_amt", "currency_with"].includes(column.fieldname)) {
            return `<div style="${style} text-align:center;">${value}</div>`;
        }

        // Text columns → left align
        if (["pe_name", "date", "customer", "bank"].includes(column.fieldname)) {
            return `<div style="${style} text-align:left;">${value}</div>`;
        }

        return value;
    }
};
