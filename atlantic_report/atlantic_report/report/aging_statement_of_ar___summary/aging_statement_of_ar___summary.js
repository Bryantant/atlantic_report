// Copyright (c) 2025, Takwindo and contributors
// For license information, please see license.txt

frappe.query_reports["Aging Statement of AR - Summary"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.month_start(),
            "reqd": 0
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        }
    ],

    "formatter": function (value, row, column, data, default_formatter) {
        
        let raw_value = data ? data[column.fieldname] : null;

        value = default_formatter(value, row, column, data);
        if (!data) return value;

        // --- A. FORMAT NILAI 0 JADI "---" ---
        let is_currency = (column.fieldtype === "Currency");
        if (is_currency) {
            if (raw_value === 0 || raw_value === 0.0 || raw_value === null || raw_value === "") {
                value = "---";
            }
        }

        // --- B. BASE STYLE ---
        let style = "display: flex; align-items: center; width: 100%; height: 100%;";
        
        if (is_currency) {
            style += " justify-content: flex-end; text-align:right; white-space:nowrap;";
        } else {
            style += " justify-content:flex-start;";
        }

        // --- C. GRAND TOTAL ROW ---
        if (data.is_grand_total) {
            $(row).css({
                "font-weight": "bold"
            });

            style += " font-weight:bold;";

            if (column.fieldname === "customer_display") {
                style += " justify-content:flex-end; margin-right:10px;";
            }
        }

        // --- D. TOTAL ROW BIASA (new) ---
        if (data.is_total_row) {

            $(row).css({
                "font-weight": "bold"
            });

            style += " font-weight:bold;";

            if (column.fieldname === "customer_display") {
                style += " justify-content:flex-end; margin-right:10px;";
            }
        }

        return `<span style="${style}">${value}</span>`;
    }
};
