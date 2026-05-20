from __future__ import annotations

import re


def generate_phonetic_seeds(
    names: list[str],
    manual_overrides: dict[str, str] | None = None,
) -> dict[str, object]:
    overrides = manual_overrides or {}
    generated = []
    for name in names:
        if name in overrides:
            continue
        if _looks_pronunciation_sensitive(name):
            generated.append(
                {
                    "term": name,
                    "pronunciation_hint": _build_hint(name),
                    "source": "generated",
                }
            )
    return {
        "manual_overrides": [
            {"term": term, "pronunciation": pronunciation}
            for term, pronunciation in overrides.items()
        ],
        "generated": generated,
    }


def _looks_pronunciation_sensitive(name: str) -> bool:
    return (
        bool(re.search(r"(tj|kh|kj|eirs|flight|[A-Z][a-z]+[A-Z])", name))
        or sum(ch.lower() in "aeiou" for ch in name) <= 2
    )


def _build_hint(name: str) -> str:
    return re.sub(r"([A-Z])", r" \1", name).strip()
