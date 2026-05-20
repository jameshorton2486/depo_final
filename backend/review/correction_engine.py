from __future__ import annotations

from pathlib import Path

from backend.database.repositories.transcript_repo import (
    rebuild_block_working_text,
    update_block_working_text,
    update_word_modified_text,
)
from backend.review.audit_logger import log_audit_event
from backend.review.deterministic_rules import apply_deterministic_rules
from backend.review.review_state import (
    ReviewResolveRequest,
    create_review_action,
    ensure_review_session,
    get_review_flag,
    update_review_flag,
)
from backend.review.speaker_corrections import create_speaker_correction


def resolve_review_action(
    request: ReviewResolveRequest,
    database_path: Path | None = None,
) -> dict[str, object]:
    review_session = ensure_review_session(request.session_id, request.reviewer, database_path)
    flag = get_review_flag(request.review_flag_id, database_path)
    issue_category = str(
        request.issue_category.value if request.issue_category else flag["issue_category"]
    )

    original_value = flag.get("original_value")
    modified_value = flag.get("current_value")
    correction_source = "review_action"
    extra_payload: dict[str, object] = {}

    if request.corrected_speaker_label:
        correction_source = "speaker_correction"
        modified_value = request.corrected_speaker_label
        extra_payload["speaker_correction"] = create_speaker_correction(
            session_id=request.session_id,
            speaker_segment_id=int(flag["speaker_segment_id"]),
            original_speaker_label=str(flag.get("original_value") or ""),
            corrected_speaker_label=request.corrected_speaker_label,
            corrected_role=request.corrected_role,
            reviewer=request.reviewer,
            note=request.note,
            database_path=database_path,
        )
    elif request.apply_deterministic_rules:
        correction_source = "deterministic_rule"
        rule_result = apply_deterministic_rules(str(original_value or ""), issue_category)
        modified_value = str(rule_result["updated_value"])
        extra_payload["rules_applied"] = rule_result["rules_applied"]
        if flag.get("word_object_id") is not None:
            updated_word = update_word_modified_text(
                int(flag["word_object_id"]),
                modified_value,
                database_path,
            )
            updated_block = rebuild_block_working_text(
                updated_word.transcript_block_id, database_path
            )
            extra_payload["updated_word"] = updated_word.model_dump(mode="json")
            extra_payload["updated_block"] = updated_block.model_dump(mode="json")
        elif flag.get("transcript_block_id") is not None:
            updated_block = update_block_working_text(
                int(flag["transcript_block_id"]),
                modified_value,
                database_path,
            )
            extra_payload["updated_block"] = updated_block.model_dump(mode="json")

    next_status = _resolve_flag_status(request.action)
    updated_flag = update_review_flag(
        request.review_flag_id,
        status=next_status,
        note=request.note,
        current_value=modified_value,
        reviewer=request.reviewer,
        database_path=database_path,
    )
    action_record = create_review_action(
        review_flag_id=request.review_flag_id,
        review_session_id=int(review_session["id"]),
        action_type=request.action,
        reviewer=request.reviewer,
        note=request.note,
        original_value=original_value,
        modified_value=modified_value,
        database_path=database_path,
    )
    audit_record = log_audit_event(
        session_id=request.session_id,
        entity_type=_entity_type_for_flag(flag),
        entity_id=_entity_id_for_flag(flag),
        action_type=request.action,
        issue_category=issue_category,
        original_value=original_value,
        modified_value=modified_value,
        reviewer=request.reviewer,
        correction_source=correction_source,
        database_path=database_path,
    )
    return {
        "review_session": review_session,
        "review_flag": updated_flag,
        "review_action": action_record,
        "audit_event": audit_record,
        **extra_payload,
    }


def _resolve_flag_status(action: str) -> str:
    normalized = action.lower().strip()
    if normalized in {"accept", "mark_reviewed", "resolve"}:
        return "reviewed"
    if normalized == "reject":
        return "rejected"
    return "reviewed"


def _entity_type_for_flag(flag: dict[str, object]) -> str:
    if flag.get("speaker_segment_id") is not None and flag.get("word_object_id") is None:
        return "speaker_segment"
    if flag.get("word_object_id") is not None:
        return "word_object"
    return "transcript_block"


def _entity_id_for_flag(flag: dict[str, object]) -> int:
    for key in ("word_object_id", "speaker_segment_id", "transcript_block_id"):
        if flag.get(key) is not None:
            return int(flag[key])
    raise ValueError("Review flag does not reference a resolvable entity.")
