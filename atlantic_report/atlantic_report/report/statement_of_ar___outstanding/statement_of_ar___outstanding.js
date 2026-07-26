frappe.query_reports["Statement Of AR - Outstanding"] = {

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
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer"
        }
    ],

    formatter: function (value, row, column, data, default_formatter) {
        let content = default_formatter(value, row, column, data);
        if (!data) return content;

        // Format date
        if (column.fieldname === "date" && value) {
            return `<span style="font-size:12px;">${moment(value).format("DD-MMM-YYYY")}</span>`;
        }

        // HEADER CUSTOMER (indent = 0)
        if (data.indent === 0) {
            if (column.fieldname === "reff") {
                return `<span style="font-weight:bold; font-size:12px;">${content}</span>`;
            }
            return "";
        }

        // DETEKSI TOTAL ROW
        let is_total_row = data.is_total_row || (data.reff && data.reff.toString().includes("TOTAL"));

        if (is_total_row) {
            return `<b><span style="font-size:12px;">${content || ""}</span></b>`;
        }

        return `<span style="font-size:12px;">${content}</span>`;
    }
};
