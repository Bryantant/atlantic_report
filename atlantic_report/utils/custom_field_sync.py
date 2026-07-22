from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from .print_format_sync import _api_url, _response_json


def push_custom_field_to_remote(
    remote_base_url: str,
    api_key_path: str,
    field_spec: dict[str, Any],
) -> dict[str, Any]:
    """Create or update a Custom Field on the remote site via REST API."""
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

    name = f"{field_spec['dt']}-{field_spec['fieldname']}"
    get_response = session.get(_api_url(remote_base_url, "Custom Field", name), timeout=60)
    if get_response.status_code == 404:
        response = session.post(_api_url(remote_base_url, "Custom Field"), json=field_spec, timeout=60)
        _response_json(response)
        action = "created"
    else:
        _response_json(get_response)
        response = session.put(_api_url(remote_base_url, "Custom Field", name), json=field_spec, timeout=60)
        _response_json(response)
        action = "updated"

    return {"name": name, "action": action, "remote_base_url": remote_base_url.rstrip("/")}
