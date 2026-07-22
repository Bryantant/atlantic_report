from __future__ import annotations

import json
import mimetypes
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

import frappe
import requests


APP_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = APP_ROOT / ".sync_artifacts" / "print_formats"
DEFAULT_SOURCE_NAMES = [
    "Custom Invoice",
    "Custom Delivery Order",
    "Custom Stock Mutation",
    "Custom Receiving Note",
    "custom Payment Note",
]
NAME_ALIASES = {
    "Custom Sales Invoice": "Custom Invoice",
    "Custom Payment Note": "custom Payment Note",
}
SYSTEM_FIELDS = {
    "__last_sync_on",
    "__onload",
    "__unsaved",
    "_assign",
    "_comments",
    "_liked_by",
    "_seen",
    "_user_tags",
    "creation",
    "docstatus",
    "doctype",
    "idx",
    "modified",
    "modified_by",
    "owner",
}
INTER_FONT_FACE_CSS = """@font-face {
  font-family: "Inter";
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url("/assets/frappe/css/fonts/inter/Inter-Regular.woff2") format("woff2");
}
@font-face {
  font-family: "Inter";
  font-style: normal;
  font-weight: 500;
  font-display: swap;
  src: url("/assets/frappe/css/fonts/inter/Inter-Medium.woff2") format("woff2");
}
@font-face {
  font-family: "Inter";
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url("/assets/frappe/css/fonts/inter/Inter-SemiBold.woff2") format("woff2");
}
@font-face {
  font-family: "Inter";
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url("/assets/frappe/css/fonts/inter/Inter-Bold.woff2") format("woff2");
}

"""

def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def _resolve_names(print_format_names: list[str] | None = None) -> list[str]:
    requested = print_format_names or DEFAULT_SOURCE_NAMES
    resolved: list[str] = []
    for name in requested:
        resolved.append(NAME_ALIASES.get(name, name))
    return resolved


def _sanitize_print_format(doc: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in doc.items():
        if key in SYSTEM_FIELDS or key.startswith("_"):
            continue
        cleaned[key] = value

    # Preview attachments are synced separately.
    cleaned.pop("print_designer_preview_img", None)
    return cleaned


def _preview_file_doc(print_format_name: str) -> dict[str, Any] | None:
    matches = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "Print Format",
            "attached_to_name": print_format_name,
            "attached_to_field": "print_designer_preview_img",
        },
        fields=["name", "file_name", "file_url", "is_private"],
        order_by="modified desc",
        limit_page_length=1,
    )
    return matches[0] if matches else None


def _preview_site_path(file_doc: dict[str, Any]) -> Path:
    file_url = file_doc.get("file_url") or ""
    filename = Path(file_url).name or file_doc["file_name"]
    if file_doc.get("is_private"):
        return Path(frappe.get_site_path("private", "files", filename))
    return Path(frappe.get_site_path("public", "files", filename))


def export_print_formats(
    print_format_names: list[str] | None = None,
    output_dir: str | None = None,
) -> dict[str, Any]:
    outdir = Path(output_dir or DEFAULT_OUTPUT_DIR)
    outdir.mkdir(parents=True, exist_ok=True)

    exported_items: list[dict[str, Any]] = []
    for name in _resolve_names(print_format_names):
        doc = frappe.get_doc("Print Format", name)
        payload = _sanitize_print_format(doc.as_dict())
        slug = _slugify(name)
        json_path = outdir / f"{slug}.json"
        json_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )

        preview_meta = _preview_file_doc(name)
        preview_path: str | None = None
        if preview_meta:
            source_path = _preview_site_path(preview_meta)
            if source_path.exists():
                preview_filename = preview_meta["file_name"] or source_path.name
                target_path = outdir / preview_filename
                target_path.write_bytes(source_path.read_bytes())
                preview_path = str(target_path)

        exported_items.append(
            {
                "source_name": name,
                "doc_type": payload.get("doc_type"),
                "json_path": str(json_path),
                "preview_path": preview_path,
                "preview_is_private": int(preview_meta.get("is_private")) if preview_meta else None,
            }
        )

    summary = {
        "site": frappe.local.site,
        "output_dir": str(outdir),
        "items": exported_items,
    }
    (outdir / "export_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _api_url(base_url: str, doctype: str, name: str | None = None) -> str:
    encoded_doctype = quote(doctype, safe="")
    if name is None:
        return f"{base_url.rstrip('/')}/api/resource/{encoded_doctype}"
    encoded_name = quote(name, safe="")
    return f"{base_url.rstrip('/')}/api/resource/{encoded_doctype}/{encoded_name}"


def _response_json(response: requests.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError as exc:
        response.raise_for_status()
        raise RuntimeError("API response was not valid JSON") from exc

    if not response.ok:
        raise RuntimeError(
            f"API request failed with status {response.status_code}: {json.dumps(data, ensure_ascii=True)}"
        )
    if data.get("exc"):
        raise RuntimeError(json.dumps(data, ensure_ascii=True))
    return data


def _upsert_print_format(
    session: requests.Session,
    base_url: str,
    payload: dict[str, Any],
) -> str:
    name = payload["name"]
    get_response = session.get(_api_url(base_url, "Print Format", name), timeout=60)
    if get_response.status_code == 404:
        response = session.post(_api_url(base_url, "Print Format"), json=payload, timeout=60)
        _response_json(response)
        return "created"

    _response_json(get_response)
    response = session.put(_api_url(base_url, "Print Format", name), json=payload, timeout=60)
    _response_json(response)
    return "updated"


def _upload_preview(
    session: requests.Session,
    base_url: str,
    print_format_name: str,
    preview_path: str,
    preview_is_private: int | None,
) -> None:
    path = Path(preview_path)
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    with path.open("rb") as handle:
        response = session.post(
            f"{base_url.rstrip('/')}/api/method/upload_file",
            data={
                "doctype": "Print Format",
                "docname": print_format_name,
                "fieldname": "print_designer_preview_img",
                "is_private": str(int(bool(preview_is_private))),
            },
            files={"file": (path.name, handle, mime_type)},
            timeout=120,
        )
    _response_json(response)


def _sample_doc_name(session: requests.Session, base_url: str, doctype: str) -> str | None:
    response = session.get(
        _api_url(base_url, doctype),
        params={
            "fields": json.dumps(["name"]),
            "filters": json.dumps([["docstatus", "=", 1]]),
            "order_by": "modified desc",
            "limit_page_length": 1,
        },
        timeout=60,
    )
    data = _response_json(response)
    rows = data.get("data") or []
    if not rows:
        return None
    return rows[0].get("name")


def fetch_remote_doc(
    remote_base_url: str,
    api_key_path: str,
    doctype: str,
    name: str,
) -> dict[str, Any]:
    api_token = Path(api_key_path).read_text(encoding="utf-8").strip()
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"token {api_token}",
            "Accept": "application/json",
        }
    )
    response = session.get(_api_url(remote_base_url, doctype, name), timeout=60)
    return _response_json(response)["data"]


def ensure_inter_font_faces_local(print_format_names: list[str] | None = None) -> dict[str, Any]:
    updated: list[str] = []
    unchanged: list[str] = []

    for name in _resolve_names(print_format_names):
        doc = frappe.get_doc("Print Format", name)
        css = doc.css or ""
        if "Inter-Regular.woff2" in css:
            unchanged.append(name)
            continue

        doc.css = INTER_FONT_FACE_CSS + css
        doc.save(ignore_permissions=True)
        updated.append(name)

    frappe.db.commit()
    return {"updated": updated, "unchanged": unchanged}


def compare_and_pull_print_formats(
    remote_base_url: str,
    api_key_path: str,
    print_format_names: list[str] | None = None,
) -> dict[str, Any]:
    """Compare each print format between the remote site and this (local) site.

    Where they differ, overwrite the local doc's changed fields with the remote values.
    """
    api_token = Path(api_key_path).read_text(encoding="utf-8").strip()
    if not api_token:
        raise RuntimeError(f"API key file is empty: {api_key_path}")

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"token {api_token}",
            "Accept": "application/json",
        }
    )

    results: list[dict[str, Any]] = []
    for name in _resolve_names(print_format_names):
        remote_response = session.get(_api_url(remote_base_url, "Print Format", name), timeout=60)
        remote_data = _response_json(remote_response)["data"]
        remote_clean = _sanitize_print_format(remote_data)

        local_doc = frappe.get_doc("Print Format", name)
        local_clean = _sanitize_print_format(local_doc.as_dict())

        changed_fields = sorted(
            key
            for key in remote_clean
            if key not in ("name", "doctype") and remote_clean.get(key) != local_clean.get(key)
        )

        entry: dict[str, Any] = {
            "name": name,
            "doc_type": remote_clean.get("doc_type"),
            "differs": bool(changed_fields),
            "changed_fields": changed_fields,
        }

        if changed_fields:
            for key in changed_fields:
                local_doc.set(key, remote_clean[key])
            local_doc.save(ignore_permissions=True)
            entry["action"] = "updated_local"
        else:
            entry["action"] = "no_change"

        results.append(entry)

    frappe.db.commit()
    return {
        "remote_base_url": remote_base_url.rstrip("/"),
        "local_site": frappe.local.site,
        "results": results,
    }


def sync_print_formats_to_remote(
    remote_base_url: str,
    api_key_path: str,
    print_format_names: list[str] | None = None,
    output_dir: str | None = None,
) -> dict[str, Any]:
    export_summary = export_print_formats(
        print_format_names=print_format_names,
        output_dir=output_dir,
    )

    api_token = Path(api_key_path).read_text(encoding="utf-8").strip()
    if not api_token:
        raise RuntimeError(f"API key file is empty: {api_key_path}")

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"token {api_token}",
            "Accept": "application/json",
        }
    )

    imported: list[dict[str, Any]] = []
    for item in export_summary["items"]:
        payload = json.loads(Path(item["json_path"]).read_text(encoding="utf-8"))
        action = _upsert_print_format(session, remote_base_url, payload)
        if item.get("preview_path"):
            _upload_preview(
                session=session,
                base_url=remote_base_url,
                print_format_name=payload["name"],
                preview_path=item["preview_path"],
                preview_is_private=item.get("preview_is_private"),
            )
        imported.append(
            {
                "name": payload["name"],
                "doc_type": payload.get("doc_type"),
                "action": action,
                "preview_uploaded": bool(item.get("preview_path")),
            }
        )

    doctypes = sorted({item["doc_type"] for item in imported if item.get("doc_type")})
    sample_docs = {
        doctype: _sample_doc_name(session, remote_base_url, doctype) for doctype in doctypes
    }

    result = {
        "source_site": frappe.local.site,
        "remote_base_url": remote_base_url.rstrip("/"),
        "output_dir": export_summary["output_dir"],
        "imported": imported,
        "sample_docs": sample_docs,
    }
    outdir = Path(export_summary["output_dir"])
    (outdir / "sync_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return result
