// Copyright (c) 2025, Takwindo and contributors
// For license information, please see license.txt

frappe.query_reports["Aging Statement of AP - Detail"] = {
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
            "fieldname": "supplier",
            "label": __("Supplier"),
            "fieldtype": "Link",
            "options": "Supplier"
        }
    ],

    "tree": true,
    "name_field": "invoice_no",
    "parent_field": "parent",
    "initial_depth": 3,

    "formatter": function (value, row, column, data, default_formatter) {
        
        // 1. Format Tanggal Standard
        if (column.fieldname === "date" && value) {
            value = moment(value).format("DD-MMM-YYYY");
        } else {
            value = default_formatter(value, row, column, data);
        }

        if (!data) return value;

        // 2. DEFINE STYLE (NOWRAP)
        let style = "";
        if (column.fieldname === "date" || column.fieldtype === "Currency") {
            style = "white-space: nowrap;";
        }

        // --- LOGIKA HEADER (Indent 0) ---
        if (data.indent === 0) {
            
            var $value = $(`<span>${value}</span>`);
            $value.css("font-weight", "bold");
            value = $value.prop('outerHTML');

            // GRAND TOTAL
            if (data.is_grand_total) {
                $(row).css("background-color", "#f7f7f7");
                
                if (column.fieldname === "invoice_no") {
                     var $val = $(`<span>${value}</span>`);
                     $val.css({"float": "right", "margin-right": "15px"});
                     value = $val.prop('outerHTML');
                }
            } 
            // HEADER SUPPLIER BIASA
            else if (column.fieldname !== "invoice_no") {
                const columnsToClear = ["total", "range1", "range2", "range3", "range4", "accumulation", "ots"];
                if (columnsToClear.includes(column.fieldname)) {
                    value = ""; 
                }
            }
        }

        // --- LOGIKA ISI DATA (Indent 1) ---
        if (data.indent === 1) {
            if (column.fieldtype === "Currency") {
                if (data[column.fieldname] === 0 || data[column.fieldname] === 0.0) {
                    // [PERBAIKAN] Ubah "-" menjadi "--" dan paksa Rata Kanan
                    return `<span style="${style} display:block; text-align:right; width:100%;">--</span>`;
                }
            }
        }

        // 3. APPLY STYLE WRAPPER
        if (style) {
            return `<span style="${style}">${value}</span>`;
        }

        return value;
    }
};