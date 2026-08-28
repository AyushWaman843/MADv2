import logging

from ..database import get_db
from ..models import CallJob
from ..services.msg91_service import place_call
from ..services.tts_service import generate_audio


LOGGER = logging.getLogger(__name__)


def execute_call(job_id: str) -> None:
    db_session = get_db()
    try:
        call_job = db_session.query(CallJob).filter(CallJob.id == job_id).first()
        if call_job is None:
            LOGGER.error("Call job %s was not found when the scheduler tried to execute it.", job_id)
            return

        audio_url = generate_audio(call_job.rephrased_message or call_job.original_message)
        msg91_request_id = place_call(call_job.contact_number, audio_url)
        call_job.msg91_request_id = msg91_request_id
        call_job.status = "calling"
        db_session.commit()
    except Exception:
        db_session.rollback()
        LOGGER.exception("Call execution failed for job %s.", job_id)
        failed_session = get_db()
        try:
            failed_job = failed_session.query(CallJob).filter(CallJob.id == job_id).first()
            if failed_job is not None:
                failed_job.status = "failed"
                failed_session.commit()
        except Exception:
            failed_session.rollback()
            LOGGER.exception("Failed to mark call job %s as failed after execution error.", job_id)
        finally:
            failed_session.close()
    finally:
        db_session.close()
