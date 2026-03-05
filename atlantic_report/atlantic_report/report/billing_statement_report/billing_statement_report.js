// Copyright (c) 2025, Takwindo and contributors
// For license information, please see license.txt

frappe.query_reports["Billing Statement Report"] = {
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
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        }
    ],

    "formatter": function (value, row, column, data, default_formatter) {
        
        // 1. Format Default
        value = default_formatter(value, row, column, data);

        // Safety Check
        if (!data) return value;

        // 2. FORMAT TANGGAL (06-Aug-2025)
        if (column.fieldname === "date" && value) {
            // Kita harus format ulang nilai raw-nya agar aman
            value = moment(data[column.fieldname]).format("DD-MMM-YYYY");
        }

        // 3. STYLING GRAND TOTAL
        if (data.is_grand_total) {
            // Style Baris (Row)
            $(row).css({
                "font-weight": "bold",
                "background-color": "#e0e0e0" // Abu-abu lebih gelap dikit
            });
            
            // Paksa isi sel menjadi bold (untuk menimpa default formatter)
            return `<span style="font-weight:bold;">${value}</span>`;
        }

        return value;
    }
};