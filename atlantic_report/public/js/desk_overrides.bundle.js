// Atlantic Report desk overrides: hide the row-number column on all Query Reports.
// query_report.js is the only core call site that builds its grid off `window.DataTable`
// (report_view.js and import_preview.js use their own local import binding), so this
// wrapper only affects Query/Custom Reports, not the standard doctype Report View grid.
(function () {
	var OriginalDataTable = window.DataTable;
	if (!OriginalDataTable || OriginalDataTable.__atlantic_patched) return;

	function PatchedDataTable(el, options) {
		options = options || {};
		if (!("serialNoColumn" in options)) {
			options.serialNoColumn = false;
		}
		return new OriginalDataTable(el, options);
	}
	PatchedDataTable.prototype = OriginalDataTable.prototype;
	Object.setPrototypeOf(PatchedDataTable, OriginalDataTable);
	PatchedDataTable.__atlantic_patched = true;

	window.DataTable = PatchedDataTable;
})();

// Atlantic Report desk overrides: start with sidebar closed on form/list pages (not workspace)
frappe.router.on("change", function () {
	setTimeout(function () {
		var route = frappe.get_route();
		// Skip workspace — its left nav should stay open
		if (!route || !route[0] || route[0] === "Workspaces") return;

		var $sidebar = $(".layout-side-section");
		if ($sidebar.is(":visible")) {
			$sidebar.hide();
			var $icon = $(".sidebar-toggle-btn .sidebar-toggle-icon");
			if ($icon.length && frappe.utils) {
				$icon.html(frappe.utils.icon("es-line-sidebar-expand", "md"));
			}
		}
	}, 300);
});
