"""Read local secrets from the gitignored .secrets/ directory."""

import frappe


def get_hicomsystem_api_key():
	"""Read the atlanticsea hicomsystem API key from .secrets/atlanticsea_hicomsystem_api_key.txt."""
	path = frappe.utils.get_bench_path() + "/apps/atlantic_report/.secrets/atlanticsea_hicomsystem_api_key.txt"
	try:
		with open(path) as f:
			return f.read().strip()
	except FileNotFoundError:
		frappe.throw(f"hicomsystem API key file not found at {path}")
