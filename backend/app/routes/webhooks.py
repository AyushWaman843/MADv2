from flask import Blueprint, jsonify, request

from ..database import get_db
from ..models import CallJob


webhooks_bp = Blueprint("webhooks", __name__)


def _extract_msg91_request_id(payload: dict):
    return payload.get("msg91_request_id") or payload.get("request_id") or payload.get("id")


def _map_status(raw_status: str) -> str:
    normalized_status = str(raw_status or "").strip().lower()
    if normalized_status in {"connected", "completed", "success", "answered"}:
        return "connected"
    if normalized_status in {"failed", "busy", "no-answer", "no answer", "cancelled", "rejected"}:
        return "failed"
    return ""


@webhooks_bp.post("/webhook/msg91")
def msg91_webhook():
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    request_id = _extract_msg91_request_id(payload)
    mapped_status = _map_status(
        payload.get("status") or payload.get("call_status") or payload.get("event")
    )

    if not request_id:
        return jsonify({"status": "ignored", "message": "msg91_request_id not provided."}), 200

    if not mapped_status:
        return jsonify({"status": "ignored", "message": "No terminal call status found."}), 200

    db_session = get_db()
    try:
        call_job = db_session.query(CallJob).filter(CallJob.msg91_request_id == request_id).first()
        if call_job is None:
            return jsonify({"status": "ignored", "message": "Matching call job not found."}), 200

        call_job.status = mapped_status
        db_session.commit()
    except Exception:
        db_session.rollback()
        return jsonify({"status": "error", "message": "Failed to update call status."}), 500
    finally:
        db_session.close()

    return jsonify({"status": "ok"}), 200
