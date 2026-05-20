from __future__ import annotations

from pathlib import Path

from backend.legal_review.colloquy_service import list_colloquy_groups
from backend.legal_review.exhibit_service import list_linked_exhibits
from backend.legal_review.interpreted_transcript import ensure_interpreted_segments
from backend.legal_review.issue_tracker import list_review_issues
from backend.legal_review.legal_navigation import get_navigation_index
from backend.legal_review.objection_service import list_objections
from backend.legal_review.transcript_annotations import list_annotations


def get_review_dashboard(
    session_id: int,
    database_path: Path | None = None,
) -> dict[str, object]:
    interpreted_segments = ensure_interpreted_segments(session_id, database_path)
    annotations = list_annotations(session_id, database_path)
    objections = list_objections(session_id, database_path)
    linked_exhibits = list_linked_exhibits(session_id, database_path)
    issues = list_review_issues(session_id, database_path)
    colloquy_groups = list_colloquy_groups(session_id, database_path)
    navigation = get_navigation_index(session_id, database_path)
    return {
        "session_id": session_id,
        "counts": {
            "annotations": len(annotations),
            "bookmarks": sum(
                1
                for annotation in annotations
                if str(annotation.get("annotation_type", "")).upper() == "BOOKMARK"
            ),
            "objections": len(objections),
            "linked_exhibits": len(linked_exhibits),
            "interpreted_segments": len(interpreted_segments),
            "issues": len(issues),
        },
        "annotations": annotations,
        "objections": objections,
        "linked_exhibits": linked_exhibits,
        "interpreted_segments": interpreted_segments,
        "issues": issues,
        "colloquy_groups": colloquy_groups,
        "navigation": navigation,
    }
