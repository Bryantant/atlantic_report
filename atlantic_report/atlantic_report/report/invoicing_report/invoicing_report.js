// Copyright (c) 2025, Takwindo and contributors
// For license information, please see license.txt

frappe.query_reports["Invoicing Report"] = {
    "filters": [
        // [HAPUS] Filter Company dibuang
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
        },
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        }
    ],

    "formatter": function (value, row, column, data, default_formatter) {
        
        // Format Tanggal (DD-MMM-YYYY)
        if (column.fieldname === "inv_date" && value) {
            value = moment(value).format("DD-MMM-YYYY");
        } else {
            value = default_formatter(value, row, column, data);
        }

        if (!data) return value;

        // Styling Grand Total
        if (data.is_grand_total) {
            $(row).css({
                "font-weight": "bold",
                "background-color": "#f7f7f7"
            });
            return `<span style="font-weight:bold;">${value}</span>`;
        }

        return value;
    }
};