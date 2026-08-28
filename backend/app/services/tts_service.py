import logging
import uuid
from pathlib import Path

import requests

from ..config import Config


LOGGER = logging.getLogger(__name__)
AUDIO_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "generated_audio"


def generate_audio(text: str) -> str:
    # Phase 4 - wire this up after MSG91 is tested.
    AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not Config.ELEVENLABS_API_KEY or not Config.ELEVENLABS_VOICE_ID:
        placeholder_path = AUDIO_OUTPUT_DIR / f"{uuid.uuid4()}.txt"
        placeholder_path.write_text(text, encoding="utf-8")
        LOGGER.warning("ElevenLabs credentials are missing, so a placeholder text file was created instead of audio.")
        return str(placeholder_path)

    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{Config.ELEVENLABS_VOICE_ID}",
        headers={
            "xi-api-key": Config.ELEVENLABS_API_KEY,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
        },
        timeout=60,
    )
    response.raise_for_status()

    audio_path = AUDIO_OUTPUT_DIR / f"{uuid.uuid4()}.mp3"
    audio_path.write_bytes(response.content)
    return str(audio_path)
