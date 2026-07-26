// Copyright (c) 2025
// Supplier DO Report - Detail

frappe.query_reports["Supplier DO Report - Detail"] = {

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

    skip_total_row: 1,   // total row dihandle manual di PY
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
                height: 65px !important;
                min-height: 65px !important;
            }

            .dt-body 
            .dt-row:not(.dt-row-header):not(.dt-row-filter) 
            .dt-cell__wrapper,
            .dt-body 
            .dt-row:not(.dt-row-header):not(.dt-row-filter) 
            .dt-cell__content {
                height: 65px !important;
                min-height: 65px !important;
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

        // ==================================================================
        // PATCH DATATABLE: OVERRIDE internal getRowHeight() → 65px
        // ==================================================================
        const patch_row_height = () => {
            const dt = frappe.query_report?.datatable;
            if (!dt) return;

            const H = 65;

            // set cell height globally
            dt.options.cellHeight = H;

            const rm = dt.rowmanager;
            if (!rm) return;

            // simpan original
            if (!rm.__orig_getRowHeight) {
                rm.__orig_getRowHeight = rm.getRowHeight?.bind(rm);
            }

            // override seluruh row height
            rm.getRowHeight = function(rowIndex) {
                return H;
            };

            rm.rowHeight = H;
            rm.row_height = H;

            try {
                rm.refreshRows(dt.datamanager.getRows());
            } catch(e) {
                dt.refresh();
            }
        };

        frappe.after_ajax(patch_row_height);
        setTimeout(patch_row_height, 350);
        setTimeout(patch_row_height, 900);
    },

    // ==================================================================
    // FORMATTER UTAMA
    // ==================================================================
    formatter(value, row, column, data, default_formatter) {

        // Jalankan default formatter (angka, html link, dsb)
        value = default_formatter(value, row, column, data);

        if (!data) {
            return value;
        }

        // ==================================================================
        // BASE STYLE: semua cell font 12px
        // ==================================================================
        let style = `
            font-size:12px;
            line-height:1.15;
            margin:0 !important;
            padding:0 !important;
            vertical-align:top !important;
            display:inline-block;
            width:100%;
        `;

        // ==================================================================
        // ALIGNMENT
        // ==================================================================
        if (["Currency", "Float", "Int"].includes(column.fieldtype) ||
            ["qty_info", "rate_info", "amount_info"].includes(column.fieldname)) {
            style += "text-align:right !important; white-space:nowrap;";
        }

        if (column.fieldname === "currency_info") {
            style += "text-align:center !important;";
        }

        // ==================================================================
        // BOLD RULES
        // ==================================================================

        // Row total → seluruh kolom bold
        if (data.is_total_row) {
            style += "font-weight:bold !important;";
        }

        // Supplier name → bold hanya kolom ini (bukan seluruh row)
        if (column.fieldname === "supplier_name") {
            style += "font-weight:bold !important;";
        }

        // ==================================================================
        // Column berisi HTML (gunakan div, bukan span)
        // ==================================================================
        const html_columns = [
            "pr_info", "supplier_name", "status",
            "item_info", "qty_info", "currency_info",
            "rate_info", "amount_info"
        ];

        if (html_columns.includes(column.fieldname)) {
            return `<div style="${style}">${value}</div>`;
        }

        // selain itu → span biasa
        return `<span style="${style}">${value}</span>`;
    }
};
