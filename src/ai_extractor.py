from __future__ import annotations

import json
import os
from typing import Any, Dict

import requests


class AIExtractionUnavailable(RuntimeError):
    pass


def extract_supplier_message(message: str) -> Dict[str, Any]:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise AIExtractionUnavailable("DEEPSEEK_API_KEY is not configured. Use the human-confirmed fields instead.")

    api_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    prompt = (
        "Extract purchasing facts from the supplier message. Return JSON only with keys: "
        "item, quantity, unit, unit_price. Use null for missing or ambiguous values. "
        "Do not infer unit conversions or invent values.\n\nSupplier message: " + message
    )
    response = requests.post(
        api_url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "You extract structured purchasing data. Never invent missing facts."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        },
        timeout=20,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    data = json.loads(content)
    allowed = {"item", "quantity", "unit", "unit_price"}
    return {key: data.get(key) for key in allowed}
