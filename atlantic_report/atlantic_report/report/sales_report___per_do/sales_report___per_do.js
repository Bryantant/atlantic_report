frappe.query_reports["Sales Report - per DO"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.month_start()
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

        // TOTAL ROW dari Python → gunakan flag "is_total_row"
        if (data && data.is_total_row) {
            return `<span style="font-weight:bold; font-size:12px;">${value}</span>`;
        }

        return `<span style="font-size:12px;">${value}</span>`;
    }
};
