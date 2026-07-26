// Sales Report - Detail (Final Revised Patch)

frappe.query_reports["Sales Report - Detail"] = {

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
                height: 75px !important;
                min-height: 75px !important;
            }

            .dt-body 
            .dt-row:not(.dt-row-header):not(.dt-row-filter) 
            .dt-cell__wrapper,
            .dt-body 
            .dt-row:not(.dt-row-header):not(.dt-row-filter) 
            .dt-cell__content {
                height: 75px !important;
                min-height: 75px !important;
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
        FORCE ALL ROW HEIGHT = 75px (HEADER, FILTER, BODY)
        ===================================================== */
        const patch_row_height = () => {
            const dt = frappe.query_report?.datatable;
            if (!dt) return;

            const H = 85;

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

    /* =====================================================
       FORMATTER (unchanged)
    ===================================================== */
    formatter(value, row, column, data, default_formatter) {

        /* ==========================================================
        KHUSUS KOL0M QTY_UOM (detail + total row)
        ========================================================== */
        if (column.fieldname === "qty_uom" && value) {
            var html = value || "";

            // Ambil angka qty
            var qty_match = html.match(/>([\d.,]+)</);
            var qty_val = qty_match ? qty_match[1] : "0";
            qty_val = format_number(flt(qty_val), null, 2);   // thousand separator + 2 decimal

            // Ambil UOM (detail saja)
            var uom_match = html.match(/<br>\s*<span[^>]*>(.*?)<\/span>/);
            var uom_val = uom_match ? uom_match[1] : "";

            // TOTAL ROW → hanya angka bold, no UOM
            if (data && data.is_total_row) {
                return `<div style="text-align:right;font-weight:bold;">${qty_val}</div>`;
            }

            // DETAIL ROW → Qty + UOM
            return `
                <div style="display:block;">
                    <div style="text-align:right;">${qty_val}</div>
                    ${uom_val ? `<div>${uom_val}</div>` : ``}
                </div>
            `;
        }

        /* ==========================================================
        BARIS TOTAL UNTUK KOLOM LAIN
        ========================================================== */
        if (data && data.is_total_row) {

            // -- Kolom PRICE harus dikosongkan --
            if (column.fieldname === "rate") {
                return "";
            }

            // -- Kolom AMOUNT → format currency 2 decimal --
            if (column.fieldname === "amount") {
                return `<b>${format_currency(flt(value), data.currency, 2)}</b>`;
            }

            // -- Kolom lainnya → bold value biasa --
            return `<b>${value || ""}</b>`;
        }

        /* ==========================================================
        CURRENCY (detail row)
        ========================================================== */
        if (column.fieldtype === "Currency") {
            return `
                <div style="text-align:right;width:100%;">
                    ${format_currency(flt(value), data.currency, 2)}
                </div>
            `;
        }

        /* ==========================================================
        FLOAT / INT (detail row)
        ========================================================== */
        if (["Float", "Int"].includes(column.fieldtype)) {
            return `
                <div style="text-align:right;width:100%;">
                    ${format_number(value, null, 2)}
                </div>
            `;
        }

        /* ==========================================================
        DEFAULT (text, HTML, dll.)
        ========================================================== */
        return default_formatter(value, row, column, data);
    }

};
