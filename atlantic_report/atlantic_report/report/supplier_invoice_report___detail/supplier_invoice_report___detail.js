// Copyright (c) 2025, Takwindo and contributors
// For license information, please see license.txt

frappe.query_reports["Supplier Invoice Report - Detail"] = {
    onload(report) {

        const style = document.createElement("style");
        style.innerHTML = `

            /* =====================================================
               GLOBAL FONT 12PX
            ===================================================== */
            .dt-cell, .dt-cell__content, .dt-cell__text {
                font-size: 12px !important;
                line-height: 1.25 !important;
            }

            /* =====================================================
               HEADER ROW AUTO HEIGHT — ONLY HEADER
            ===================================================== */
            .dt-row-header {
                height: auto !important;
                min-height: auto !important;
                display: flex !important;
                align-items: flex-start !important;
            }

            .dt-row-header .dt-cell {
                height: auto !important;
                min-height: auto !important;
                display: flex !important;
                align-items: flex-start !important;
            }

            .dt-row-header .dt-cell__content {
                height: auto !important;
                min-height: auto !important;
                display: block !important;
                white-space: normal !important;
                line-height: 1.2 !important;
                overflow: visible !important;
            }

            /* =====================================================
               BODY ROW — DO NOT TOUCH HEADER OR FILTER
            ===================================================== */
            .dt-body .dt-row:not(.dt-row-header):not(.dt-row-filter) {
                height: 60px !important;
                min-height: 60px !important;
            }

            .dt-body 
            .dt-row:not(.dt-row-header):not(.dt-row-filter) 
            .dt-cell__wrapper,
            .dt-body 
            .dt-row:not(.dt-row-header):not(.dt-row-filter) 
            .dt-cell__content {
                height: 60px !important;
                min-height: 60px !important;
            }

            /* =====================================================
               FIX ITEM DISPLAY — ONLY BODY, NEVER HEADER/FILTER
            ===================================================== */
            .dt-row:not(.dt-row-header):not(.dt-row-filter) .dt-cell--item_display {
                overflow: visible !important;
            }

            .dt-row:not(.dt-row-header):not(.dt-row-filter) 
                .dt-cell--item_display .dt-cell__wrapper {
                height: auto !important;
                overflow: visible !important;
                display: block !important;
                align-items: flex-start !important;
            }

            .dt-row:not(.dt-row-header):not(.dt-row-filter) 
                .dt-cell--item_display .dt-cell__content {
                height: auto !important;
                overflow: visible !important;
                display: block !important;
                white-space: normal !important;
            }

            .dt-row:not(.dt-row-header):not(.dt-row-filter) 
                .dt-cell--item_display .dt-cell__text {
                white-space: normal !important;
                display: block !important;
                overflow: visible !important;
            }

            /* =====================================================
               RIGHT ALIGN — PRICE & AMOUNT ONLY IN BODY ROW
            ===================================================== */
            .dt-row:not(.dt-row-header):not(.dt-row-filter) 
                .dt-cell--rate .dt-cell__content,
            .dt-row:not(.dt-row-header):not(.dt-row-filter) 
                .dt-cell--rate .dt-cell__text,
            .dt-row:not(.dt-row-header):not(.dt-row-filter) 
                .dt-cell--amount .dt-cell__content,
            .dt-row:not(.dt-row-header):not(.dt-row-filter) 
                .dt-cell--amount .dt-cell__text {
                text-align: right !important;
                justify-content: flex-end !important;
                width: 100% !important;
                display: flex !important;
            }
        `;
        document.head.appendChild(style);

        /* =====================================================
           FORCE BODY ROW HEIGHT ONLY (HEADER/FILTER untouched)
        ===================================================== */
        /* =====================================================
        FORCE ALL ROW HEIGHT = 60px (HEADER, FILTER, BODY)
        ===================================================== */
        const patch_row_height = () => {
            const dt = frappe.query_report?.datatable;
            if (!dt) return;

            const H = 60;

            // Set option global
            dt.options.cellHeight = H;

            const rm = dt.rowmanager;
            if (!rm) return;

            // Simpan original jika suatu saat ingin dikembalikan
            if (!rm.__orig_getRowHeight) {
                rm.__orig_getRowHeight = rm.getRowHeight?.bind(rm);
            }

            // Override tinggi baris untuk SEMUA row
            rm.getRowHeight = function (rowIndex) {
                return H;
            };

            // Set properti internal lain
            rm.rowHeight = H;
            rm.row_height = H;

            // Refresh table
            try {
                rm.refreshRows(dt.datamanager.getRows());
            } catch (e) {
                dt.refresh();
            }
        };

        frappe.after_ajax(patch_row_height);
        setTimeout(patch_row_height, 400);
        setTimeout(patch_row_height, 1200);

    },
    
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.month_start(),
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
            "fieldname": "supplier",
            "label": __("Supplier"),
            "fieldtype": "Link",
            "options": "Supplier"
        }
    ],

    "formatter": function (value, row, column, data, default_formatter) {
        
        // 1. [PRIORITAS UTAMA] Bersihkan kolom Price di Header
        // Harus dijalankan sebelum format Currency
        if (data && data.indent === 0 && column.fieldname === "price") {
            return "";
        }

        // 2. Format Currency (Nowrap)
        if (column.fieldtype === "Currency") {
            value = default_formatter(value, row, column, data);
            return `<span style="white-space: nowrap;">${value}</span>`;
        }

        value = default_formatter(value, row, column, data);
        if (!data) return value;

        // HEADER (Indent 0)
        if (data.indent === 0) {
            // Bold hanya untuk Total
            if (column.fieldname === "total") {
                return `<b>${value}</b>`;
            }
        }

        // CHILD (Indent 1)
        if (data.indent === 1) {
            if (["inv_details", "supp_terms"].includes(column.fieldname)) {
                return "";
            }
        }

        return value;
    }
};