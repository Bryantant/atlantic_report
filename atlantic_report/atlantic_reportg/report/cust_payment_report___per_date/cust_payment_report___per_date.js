frappe.query_reports["Cust Payment Report - Per Date"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.year_start(),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        }
    ],

    formatter: function (value, row, column, data, default_formatter) {

        let formatted = default_formatter(value, row, column, data);

        if (data && data.is_total_row) {
            formatted = `<b>${formatted}</b>`;
        }

        if (["paid_amount", "paid_with"].includes(column.fieldname)) {
            formatted = `<div style="text-align:right;">${formatted}</div>`;
        }

        return formatted;
    }
};
