frappe.query_reports["Aging Statement of AP - Summary"] = {

    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            reqd: 0
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

        let raw = data ? data[column.fieldname] : null;
        value = default_formatter(value, row, column, data);
        if (!data) return value;

        let is_currency = column.fieldtype === "Currency";

        // tampilkan 0 sebagai ---
        if (is_currency && (raw === 0 || raw === 0.0)) {
            value = "---";
        }

        let style = "display:flex; align-items:center; width:100%; height:100%;";

        if (is_currency) {
            style += "justify-content:flex-end; text-align:right;";
        } else {
            style += "justify-content:flex-start;";
        }

        // highlight total row
        if (data.is_total_row) {
            style += "font-weight:bold;";
        }

        return `<span style="${style}">${value}</span>`;
    }
};
