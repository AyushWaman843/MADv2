import logging
import uuid

from ..config import Config


LOGGER = logging.getLogger(__name__)


def place_call(contact_number: str, audio_url: str) -> str:
    # Phase 4 - wire this up after TTS is tested.
    if not Config.MSG91_AUTH_KEY or not Config.MSG91_VIRTUAL_NUMBER:
        mock_request_id = f"mock-{uuid.uuid4()}"
        LOGGER.warning(
            "MSG91 credentials are missing, so the backend generated a mock request id %s for %s using %s.",
            mock_request_id,
            contact_number,
            audio_url,
        )
        return mock_request_id

    # This placeholder keeps the background flow testable until the live MSG91 payload is finalized.
    mock_request_id = f"queued-{uuid.uuid4()}"
    LOGGER.info(
        "MSG91 live call payload still needs account-specific wiring, so request %s was simulated for %s using %s.",
        mock_request_id,
        contact_number,
        audio_url,
    )
    return mock_request_id
