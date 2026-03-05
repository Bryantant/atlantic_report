// Copyright (c) 2025, Takwindo and contributors
// For license information, please see license.txt

frappe.query_reports["Inventory Report - Stock Mutation Detail"] = {
    "filters": [
        {
            "fieldname": "item_code",
            "label": __("Item Code"),
            "fieldtype": "Link",
            "options": "Item",
            "reqd": 0
        },
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
        }
    ],

    "formatter": function (value, row, column, data, default_formatter) {
        
        // Skip default formatter untuk date karena sudah HTML
        if (column.fieldname !== "date") {
            value = default_formatter(value, row, column, data);
        }

        if (value === null || value === undefined) {
            value = "";
        }

        // [REVISI] Logic Sembunyikan 0 (Hanya jika BUKAN header)
        if (data && !data.is_header) {
            if (["in_qty", "out_qty"].includes(column.fieldname)) {
                if (data[column.fieldname] === 0 || data[column.fieldname] === 0.0) return "";
            }
        }

        // --- STYLING TABLE LAYOUT (PDF Safe & Vertical Center) ---
        let tableStyle = "display: table; width: 100%; height: 100%; min-height: 25px; margin: 0; padding: 0;";
        let cellStyle = "display: table-cell; vertical-align: middle; font-size: 12px; line-height: 1.2;";

        // --- HORIZONTAL ALIGNMENT ---
        if (["Currency", "Float", "Int"].includes(column.fieldtype)) {
            cellStyle += " text-align: right;";
        } else if (column.fieldname === "date") {
            cellStyle += " text-align: center;";
        } else {
            cellStyle += " text-align: left;";
        }

        // --- [REVISI] BOLD HEADER (Gunakan flag is_header) ---
        if (data && data.is_header) {
            cellStyle += " font-weight: bold;";
        }

        return `<div style="${tableStyle}"><div style="${cellStyle}">${value}</div></div>`;
    }
};