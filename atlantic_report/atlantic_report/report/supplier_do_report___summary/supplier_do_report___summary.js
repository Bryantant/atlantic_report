// Supplier DO Report - Summary

frappe.query_reports["Supplier DO Report - Summary"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.month_start(),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
        {
            fieldname: "supplier",
            label: __("Supplier"),
            fieldtype: "Link",
            options: "Supplier",
            reqd: 0
        }
    ],

    formatter(value, row, column, data, default_formatter) {
        // Highlight PR No as link (default behaviour)
        value = default_formatter(value, row, column, data);

        // Bold Supplier Name column
        if (column.fieldname === "supplier_name") {
            value = `<b>${value}</b>`;
        }

        return value;
    }
};
