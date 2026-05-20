from __future__ import annotations

from backend.database.repositories.cases_repo import get_case_intake


def resolve_live_speaker_label(
    case_id: int,
    *,
    speaker_index: int,
    explicit_label: str | None = None,
    database_path=None,
) -> str:
    if explicit_label:
        return explicit_label
    try:
        intake = get_case_intake(case_id, database_path)
    except LookupError:
        intake = {"attorneys": []}
    attorneys = intake.get("attorneys", [])
    for attorney in attorneys:
        case_attorney = attorney.get("case_attorney", {})
        label = case_attorney.get("speaker_label")
        if label and speaker_index == 0:
            return str(label)
    return f"SPEAKER {speaker_index + 1}"
