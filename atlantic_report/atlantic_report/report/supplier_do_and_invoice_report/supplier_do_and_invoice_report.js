// Copyright (c) 2025, Takwindo and contributors
// For license information, please see license.txt

frappe.query_reports["Supplier DO and Invoice Report"] = {
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
        
        // 1. Format Tanggal (DD-MMM-YY) dimana Month Huruf
        if ((column.fieldname === "po_date" || column.fieldname === "inv_date") && value) {
            value = moment(value).format("DD-MMM-YY");
        } else {
            value = default_formatter(value, row, column, data);
        }

        if (!data) return value;

        // 2. Styling Khusus Row TOTAL
        if (data.is_total_row) {
            // Beri background abu-abu muda di seluruh baris
            $(row).css("background-color", "#f7f7f7");
            
            // Bold untuk kolom label Total
            if (column.fieldname === "purchase_order") {
                 var $val = $(`<span>${value}</span>`);
                 $val.css({"float": "right", "margin-right": "15px", "font-weight": "bold"});
                 value = $val.prop('outerHTML');
            }
            // Bold untuk angka Total
            else if (column.fieldname === "grand_total") {
                value = `<b>${value}</b>`;
            }
        }

        // 3. Ubah Nilai 0 menjadi "-" pada Currency
        if (column.fieldtype === "Currency") {
            if (data[column.fieldname] === 0 || data[column.fieldname] === 0.0) {
                value = "-"; 
            }
        }

        // 4. GLOBAL STYLING (Font Kecil & Padat sesuai contoh)
        let style = "font-size: 12px; line-height: 1;";

        // Alignment Tanggal Rata Kiri
        if (column.fieldname === "po_date" || column.fieldname === "inv_date") {
            style += " display: flex; justify-content: flex-start; align-items: center; width: 100%; height: 100%; white-space: nowrap;";
        }
        
        // Currency jangan wrap
        if (column.fieldtype === "Currency") {
             style += " white-space: nowrap;";
        }

        return `<span style="${style}">${value}</span>`;
    }
};