from __future__ import annotations

import json
from typing import Any, Mapping


_LOCAL_PROVIDERS = {"llamacpp", "llama.cpp", "llama-cpp"}


def parse_hermes_model_json(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return {}

    if not isinstance(value, dict):
        return {}

    nested = value.get("value")
    if isinstance(nested, dict):
        value = nested

    return dict(value)


def hermes_local_ready(model: Mapping[str, Any]) -> bool:
    provider = str(model.get("provider") or "").strip().lower()
    model_name = str(model.get("default") or model.get("model") or "").strip()
    return provider in _LOCAL_PROVIDERS and bool(model_name)
