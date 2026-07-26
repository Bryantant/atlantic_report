frappe.query_reports["Statement of AP - By Outstanding"] = {

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
            options: "Supplier"
        }
    ],

    formatter(value, row, column, data, default_formatter) {
        let content = default_formatter(value, row, column, data);
        if (!data) return content;

        // Format Tanggal
        if (column.fieldname === "date" && value) {
            return `<span style="font-size:12px;">${moment(value).format("DD-MMM-YYYY")}</span>`;
        }

        // HEADER SUPPLIER
        if (data.indent === 0) {
            if (column.fieldname === "reff") {
                return `<span style="font-weight:bold; font-size:12px;">${content}</span>`;
            }
            return "";
        }

        // TOTAL ROWS
        let is_total = data.is_subtotal_row || data.is_grand_total
            || (data.reff && data.reff.toString().includes("TOTAL"));

        if (is_total) {
            return `<b><span style="font-size:12px;">${content || ""}</span></b>`;
        }

        return `<span style="font-size:12px;">${content}</span>`;
    }
};
