from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from backend.config import settings
from backend.database.models.transcript_models import TranscriptAssetRecord
from backend.database.repositories.assets_repo import get_assets_for_session
from backend.database.repositories.cases_repo import get_case
from backend.database.repositories.sessions_repo import get_session
from backend.database.repositories.transcript_repo import get_timeline_for_session
from backend.export.docx_exporter import write_docx_export
from backend.export.export_manifest import build_export_manifest
from backend.export.pdf_exporter import write_pdf_foundation
from backend.export.transcript_renderer import render_transcript_document
from backend.export.txt_exporter import write_txt_export
from backend.review.audit_logger import list_audit_events
from backend.system.logging_config import write_log_event


class ExportRequest(BaseModel):
    session_id: int
    include_pdf: bool = False
    include_fillers: bool = True
    package_label: str | None = None
    include_history: bool = True
    export_settings: dict[str, object] = Field(default_factory=dict)


def export_docx_bundle(
    request: ExportRequest,
    database_path: Path | None = None,
    data_root: Path | None = None,
) -> dict[str, object]:
    bundle = _prepare_bundle(request, database_path, data_root, export_type="docx")
    output_path = bundle["export_root"] / f"{bundle['stem']}.docx"
    write_docx_export(bundle["rendered_document"], output_path)
    return _finalize_export(bundle, [output_path], export_type="docx")


def export_txt_bundle(
    request: ExportRequest,
    database_path: Path | None = None,
    data_root: Path | None = None,
) -> dict[str, object]:
    bundle = _prepare_bundle(request, database_path, data_root, export_type="txt")
    output_path = bundle["export_root"] / f"{bundle['stem']}.txt"
    write_txt_export(bundle["rendered_document"], output_path)
    return _finalize_export(bundle, [output_path], export_type="txt")


def export_package_bundle(
    request: ExportRequest,
    database_path: Path | None = None,
    data_root: Path | None = None,
) -> dict[str, object]:
    bundle = _prepare_bundle(request, database_path, data_root, export_type="package")
    txt_path = bundle["export_root"] / f"{bundle['stem']}.txt"
    docx_path = bundle["export_root"] / f"{bundle['stem']}.docx"
    certificate_path = bundle["export_root"] / "certificate.txt"
    exhibit_path = bundle["export_root"] / "exhibit_index.json"
    pdf_path = bundle["export_root"] / f"{bundle['stem']}.pdf"

    write_txt_export(bundle["rendered_document"], txt_path)
    write_docx_export(bundle["rendered_document"], docx_path)
    certificate_path.write_text(
        "\n".join(bundle["rendered_document"]["certificate_lines"]) + "\n",
        encoding="utf-8",
    )
    exhibit_path.write_text(
        json.dumps(bundle["rendered_document"]["exhibit_index"], indent=2),
        encoding="utf-8",
    )
    exported_files = [txt_path, docx_path, certificate_path, exhibit_path]
    if request.include_pdf:
        write_pdf_foundation(bundle["rendered_document"], pdf_path)
        exported_files.append(pdf_path)

    package_path = bundle["export_root"] / f"{bundle['stem']}_package.zip"
    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in exported_files:
            archive.write(path, arcname=path.name)
    exported_files.append(package_path)
    return _finalize_export(bundle, exported_files, export_type="package")


def get_export_history(
    session_id: int,
    database_path: Path | None = None,
    data_root: Path | None = None,
) -> dict[str, object]:
    session_record = get_session(session_id, database_path)
    resolved_root = data_root if data_root is not None else settings.data_root
    history_root = (
        resolved_root / "cases" / str(session_record.case_id) / "exports" / f"session_{session_id}"
    )
    items: list[dict[str, object]] = []
    if history_root.exists():
        for manifest_path in sorted(history_root.glob("*/export_manifest.json"), reverse=True):
            items.append(json.loads(manifest_path.read_text(encoding="utf-8")))
    return {"session_id": session_id, "items": items}


def _prepare_bundle(
    request: ExportRequest,
    database_path: Path | None,
    data_root: Path | None,
    *,
    export_type: str,
) -> dict[str, object]:
    session_record = get_session(request.session_id, database_path)
    case_record = get_case(session_record.case_id, database_path)
    assets = get_assets_for_session(request.session_id, database_path)
    blocks = get_timeline_for_session(request.session_id, database_path)
    if not blocks:
        raise LookupError(f"Session {request.session_id} has no transcript timeline to export.")
    resolved_root = data_root if data_root is not None else settings.data_root
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    export_root = (
        resolved_root
        / "cases"
        / str(case_record.id)
        / "exports"
        / f"session_{request.session_id}"
        / timestamp
    )
    export_root.mkdir(parents=True, exist_ok=True)
    rendered_document = render_transcript_document(case_record, session_record, blocks)
    return {
        "request": request,
        "case_record": case_record,
        "session_record": session_record,
        "assets": assets,
        "blocks": blocks,
        "rendered_document": rendered_document,
        "export_root": export_root,
        "stem": _safe_stem(
            case_record.case_name, session_record.session_name, request.package_label
        ),
        "timestamp": timestamp,
        "export_type": export_type,
    }


def _finalize_export(
    bundle: dict[str, object],
    exported_files: list[Path],
    *,
    export_type: str,
) -> dict[str, object]:
    asset = _primary_asset(bundle["assets"])
    review_status = _review_status(int(bundle["session_record"].id))
    preprocessing_metadata = _load_json_path(asset.preprocessing_metadata_path)
    manifest = build_export_manifest(
        session_id=int(bundle["session_record"].id),
        case_id=int(bundle["case_record"].id),
        export_type=export_type,
        exported_files=exported_files,
        transcript_metadata={
            "block_count": len(bundle["blocks"]),
            "page_count": len(bundle["rendered_document"]["pages"]),
            "certificate_lines": len(bundle["rendered_document"]["certificate_lines"]),
        },
        export_settings={
            "include_pdf": bool(bundle["request"].include_pdf),
            "include_fillers": bool(bundle["request"].include_fillers),
            **bundle["request"].export_settings,
        },
        review_status=review_status,
        preprocessing_metadata=preprocessing_metadata,
    )
    manifest_path = Path(bundle["export_root"]) / "export_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_log_event(
        "export",
        f"export_completed:{export_type}",
        payload={
            "session_id": int(bundle["session_record"].id),
            "file_count": len(exported_files) + 1,
            "page_count": manifest["transcript_metadata"]["page_count"],
        },
    )
    return {
        "session_id": int(bundle["session_record"].id),
        "case_id": int(bundle["case_record"].id),
        "export_type": export_type,
        "files": [str(path) for path in [*exported_files, manifest_path]],
        "manifest": manifest,
        "history": get_export_history(int(bundle["session_record"].id))["items"],
    }


def _review_status(session_id: int) -> dict[str, object]:
    audit_items = list_audit_events(session_id)
    return {
        "audit_event_count": len(audit_items),
        "latest_review_action": audit_items[0] if audit_items else None,
    }


def _primary_asset(assets: list[TranscriptAssetRecord]) -> TranscriptAssetRecord:
    if not assets:
        raise LookupError("Transcript asset was not found for export.")
    return next((asset for asset in assets if asset.is_primary), assets[0])


def _load_json_path(path_value: str | None) -> dict[str, object]:
    if not path_value:
        return {}
    path = Path(path_value)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_stem(case_name: str, session_name: str, label: str | None) -> str:
    parts = [part for part in [case_name, session_name, label] if part]
    raw = "_".join(parts)
    return (
        "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in raw).strip("_")
        or "depo_pro_export"
    )
