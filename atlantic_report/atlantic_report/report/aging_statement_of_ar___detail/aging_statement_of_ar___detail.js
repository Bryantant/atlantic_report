// Copyright (c) 2025, Takwindo and contributors
// For license information, please see license.txt

frappe.query_reports["Aging Statement of AR - Detail"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
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

    "tree": true,
    "name_field": "invoice_no",
    "parent_field": "parent",
    "initial_depth": 3,

    "formatter": function (value, row, column, data, default_formatter) {
        
        // 1. Simpan Data Mentah (Raw)
        let raw_value = data ? data[column.fieldname] : null;

        // 2. Format Tanggal
        if (column.fieldname === "date" && value) {
            value = moment(value).format("DD-MMM-YYYY");
        } else {
            value = default_formatter(value, row, column, data);
        }

        if (!data) return value;

        // --- HEADER (CUSTOMER) & GRAND TOTAL LOGIC ---
        // Keduanya memiliki indent === 0
        if (data.indent === 0) {
            
            // [REVISI] BOLD UNTUK SELURUH BARIS (Customer & Total)
            $(row).css("font-weight", "bold");

            if (data.is_grand_total) {
                $(row).css("background-color", "#f7f7f7");
                if (column.fieldname === "invoice_no") {
                     var $val = $(`<span>${value}</span>`);
                     $val.css({"float": "right", "margin-right": "15px", "font-weight": "bold"});
                     value = $val.prop('outerHTML');
                }
            } else {
                // Clear kolom angka di baris Header Customer
                const columnsToClear = ["trm", "total", "range1", "range2", "range3", "range4", "accumulation", "ots"];
                if (columnsToClear.includes(column.fieldname)) {
                    value = ""; 
                }
            }
        }

        // --- HANDLING NULL/ZERO CURRENCY ---
        let is_currency = (column.fieldtype === "Currency");
        
        if (is_currency) {
            if (raw_value === 0 || raw_value === 0.0 || raw_value === null || raw_value === "") {
                if (value !== "") { 
                    value = "---";
                }
            }
        }

        // --- GLOBAL STYLING & VERTICAL ALIGN ---
        let style = "font-size: 12px; line-height: 1; display: flex; align-items: center; width: 100%; height: 100%;";

        // Logic Alignment Horizontal
        if (column.fieldname === "date" || column.fieldname === "invoice_no" || column.fieldname === "sales_ref") {
            style += " justify-content: flex-start;";
        } else if (is_currency || column.fieldtype === "Int") {
            style += " justify-content: flex-end; text-align: right;"; 
        } else {
            style += " justify-content: center;";
        }

        if (is_currency) {
             style += " white-space: nowrap;";
        }
        
        // [TAMBAHAN] Pastikan span di dalam juga inherit bold jika row-nya bold
        if (data.indent === 0) {
            style += " font-weight: bold;";
        }

        return `<span style="${style}">${value}</span>`;
    }
};