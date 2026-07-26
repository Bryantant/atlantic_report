// Copyright (c) 2025, Your Name and contributors
// For license information, please see license.txt

frappe.query_reports["Purchase Order Report - Summary"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.month_start(),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        }
    ],

    "formatter": function (value, row, column, data, default_formatter) {
        
        // 1. Default Formatter (Frappe built-in)
        value = default_formatter(value, row, column, data);

        if (!data) return value;

        // 2. Base Style (default font size 12px)
        let style = "width: 100%; display: block; font-size: 12px;";

        // ========= ALIGNMENT =========
        if (["Currency", "Float", "Int", "Percent"].includes(column.fieldtype)) {
            style += " text-align: right;";
        } else {
            style += " text-align: left;";
        }

        // ========= BOLD UNTUK TOTAL ROW =========
        if (data.is_total_row) {
            style += " font-weight: bold;";
        }

        // 3. Return HTML with style
        return `<div style="${style}">${value}</div>`;
    }
};
