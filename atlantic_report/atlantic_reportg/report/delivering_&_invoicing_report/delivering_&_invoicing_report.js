frappe.query_reports["Delivering & Invoicing Report"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.get_today()
        }
    ],

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        // Row total → bold (sesuai template HTML Anda)
        if (data && data.is_total_row) {
            return `<span style="font-weight:bold; font-size:12px;">${value}</span>`;
        }

        return `<span style="font-size:12px;">${value}</span>`;
    }
};
