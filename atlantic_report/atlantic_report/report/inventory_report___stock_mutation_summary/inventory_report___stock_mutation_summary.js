// Copyright (c) 2025, Takwindo and contributors
// For license information, please see license.txt

frappe.query_reports["Inventory Report - Stock Mutation Summary"] = {
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
                height: 40px !important;
                min-height: 40px !important;
            }

            .dt-body 
            .dt-row:not(.dt-row-header):not(.dt-row-filter) 
            .dt-cell__wrapper,
            .dt-body 
            .dt-row:not(.dt-row-header):not(.dt-row-filter) 
            .dt-cell__content {
                height: 40px !important;
                min-height: 40px !important;
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
        FORCE ALL ROW HEIGHT = 40px (HEADER, FILTER, BODY)
        ===================================================== */
        const patch_row_height = () => {
            const dt = frappe.query_report?.datatable;
            if (!dt) return;

            const H = 45;

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
        }
    ],

    "formatter": function (value, row, column, data, default_formatter) {
        
        if (value) {
            // 1. Style Dasar (Rata atas & Tidak turun baris)
            let style = "vertical-align: top; white-space: nowrap; font-size: 12px;";

            // 2. Daftar kolom yang harus RATA KANAN
            const right_align_fields = ["mutation_qty", "balance_qty", "cost_info", "value_info"];

            // 3. Cek apakah kolom saat ini ada di daftar tersebut
            if (right_align_fields.includes(column.fieldname)) {
                style += " text-align: right; display: block; width: 100%;";
            }

            // Return value dengan wrapper div yang sudah distyling
            return `<div style="${style}">${value}</div>`;
        }

        return value;
    }
};