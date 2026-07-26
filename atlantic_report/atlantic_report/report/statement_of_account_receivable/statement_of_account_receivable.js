frappe.query_reports["Statement Of Account Receivable"] = {

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

    formatter(value, row, column, data, default_formatter) {
        let content = default_formatter(value, row, column, data);

        // Customer header row
        if (data && data.indent === 0) {
            if (column.fieldname === "reff") {
                return `<span style="font-weight:bold; font-size:12px;">${content}</span>`;
            }
            return "";
        }

        // Convert 0 → ---
        if (["debit", "credit"].includes(column.fieldname)) {
            if (value === 0) {
                return `<span style="display:block; text-align:right;">---</span>`;
            }
        }

        // Hide TRM = 0
        if (column.fieldname === "trm" && (value === 0 || value === "0")) {
            return "";
        }

        // Bold total rows
        if (data && data.is_total_row) {
            return `<b>${content}</b>`;
        }

        return `<span style="font-size:12px;">${content}</span>`;
    }
};
