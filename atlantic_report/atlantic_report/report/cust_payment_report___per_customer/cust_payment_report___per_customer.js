frappe.query_reports["Cust Payment Report - Per Customer"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -12),
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

    formatter(value, row, column, data, default_formatter) {

        let formatted = default_formatter(value, row, column, data);

        // Row Total → Bold + highlight
        if (data && data.is_total_row) {
            return `<span style="font-weight:bold; background-color:#fafafa;">${formatted}</span>`;
        }

        return formatted;
    }
};
