// Copyright (c) 2025, Takwindo and contributors
// For license information, please see license.txt

frappe.query_reports["Statement Of Account Receivable"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
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
        },
        {
            "fieldname": "report_type",
            "label": __("Report Type"),
            "fieldtype": "Select",
            "options": ["By Month", "Outstanding Only"],
            "default": "By Month",
            "reqd": 1
        }
    ],

    "formatter": function (value, row, column, data, default_formatter) {
        
        let content = value; // Variable penampung konten sebelum dibungkus

        // 1. Format Tanggal
        if (column.fieldname === "date" && value) {
            content = moment(value).format("DD-MMM-YYYY");
        } else {
            content = default_formatter(value, row, column, data);
        }

        if (!data) return content;

        // 2. HEADER CUSTOMER (Indent 0)
        if (data.indent === 0 && column.fieldname === "reff") {
            // Sudah 10px dan Bold, langsung return karena style spesifik
            var $value = $(`<span>${content}</span>`);
            $value.css({
                "font-weight": "bold",
                "font-size": "10px"
            });
            return $value.prop('outerHTML');
        }
        if (data.indent === 0 && column.fieldname !== "reff") {
            return "";
        }

        // 3. DATA ROW (Indent 1)
        if (data.indent === 1) {
            
            // --- LOGIKA GRAND TOTAL (BARU) ---
            // Jika baris ini adalah GRAND TOTAL, semua kolom ditebalkan
            if (data.sales_ref && data.sales_ref.includes("GRAND TOTAL")) {
                if (column.fieldname === "trm" || column.fieldname === "currency_display") {
                    return ""; // Bersihkan kolom yang tidak perlu
                }
                content = `<b>${content}</b>`;
            }

            // --- LOGIKA EXISTING (SUB TOTAL PER CUSTOMER) ---
            else if (data.sales_ref && (data.sales_ref.includes("TOTAL") || data.sales_ref.includes("BALANCE"))) {
                
                // Tebalkan Sales Ref & Balance
                if (column.fieldname === "sales_ref" || column.fieldname === "balance") {
                    content = `<b>${content}</b>`;
                }
                
                if (column.fieldname === "amount" && data.sales_ref.includes("TOTAL")) {
                    return "";
                }
                // Sembunyikan TRM & Ccy di baris BALANCE
                if (data.sales_ref.includes("BALANCE")) {
                    if (column.fieldname === "trm" || column.fieldname === "currency_display") {
                        return "";
                    }
                }
            }

            // B. LOGIKA DEBIT & CREDIT (Sembunyikan 0)
            if (column.fieldname === 'debit' || column.fieldname === 'credit') {
                let rawVal = data[column.fieldname];
                if (rawVal === 0 || rawVal === 0.0) {
                     // Kecuali jika ini GRAND TOTAL, biarkan tampil (opsional, tapi biasanya 0 tetap tampil di total)
                     if (data.sales_ref && data.sales_ref.includes("GRAND TOTAL")) {
                         // Pass
                     } else if (data.description && data.description.trim() !== "") {
                        // Pass
                     } else {
                        content = "";
                     }
                }
            }

            // C. LOGIKA TRM (Sembunyikan 0)
            if (column.fieldname === "trm" && (value === 0 || value === "0" || value === 0.0)) {
                content = "";
            }
        }

        // --- GLOBAL STYLING: BUNGKUS DENGAN FONT 10PX ---
        return `<span style="font-size: 10px;">${content}</span>`;
    }
}