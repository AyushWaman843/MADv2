import json
import logging
import re

from openai import OpenAI

from ..config import Config
from ..utils.helpers import ensure_ist_datetime


LOGGER = logging.getLogger(__name__)


def _build_fallback_message(user_name: str, contact_name: str, message: str) -> str:
    cleaned_message = " ".join(message.strip().split())
    prefix = f"Hi {contact_name}, this is an automated message on behalf of {user_name}."
    if not cleaned_message:
        return prefix
    if cleaned_message.endswith("."):
        return f"{prefix} {cleaned_message}"
    return f"{prefix} {cleaned_message}."


def _extract_json_payload(raw_content: str) -> dict:
    stripped_content = raw_content.strip()
    if stripped_content.startswith("```"):
        stripped_content = re.sub(r"^```(?:json)?\s*", "", stripped_content)
        stripped_content = re.sub(r"\s*```$", "", stripped_content)
    json_match = re.search(r"\{.*\}", stripped_content, re.DOTALL)
    if not json_match:
        raise ValueError("LLM response did not contain a JSON object.")
    return json.loads(json_match.group(0))


def _normalize_result(payload: dict, user_name: str, contact_name: str, message: str) -> dict:
    rephrased_message = str(payload.get("rephrased_message") or "").strip()
    if not rephrased_message:
        rephrased_message = _build_fallback_message(user_name, contact_name, message)

    required_prefix = f"Hi {contact_name}, this is an automated message on behalf of {user_name}"
    if not rephrased_message.startswith(required_prefix):
        suffix_message = rephrased_message.lstrip(" ,.-")
        rephrased_message = f"{required_prefix}. {suffix_message}".strip()

    scheduled_time = None
    if payload.get("scheduled_time"):
        scheduled_time = ensure_ist_datetime(str(payload["scheduled_time"])).isoformat()

    time_extracted = bool(payload.get("time_extracted") and scheduled_time)
    return {
        "scheduled_time": scheduled_time,
        "rephrased_message": rephrased_message,
        "time_extracted": time_extracted,
    }


def process_message(message: str, user_name: str, contact_name: str, current_time_ist) -> dict:
    fallback_result = {
        "scheduled_time": None,
        "rephrased_message": _build_fallback_message(user_name, contact_name, message),
        "time_extracted": False,
    }

    if not Config.DEEPSEEK_API_KEY:
        LOGGER.warning("DEEPSEEK_API_KEY is not configured, so the backend is using the fallback message flow.")
        return fallback_result

    client = OpenAI(api_key=Config.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    system_prompt = (
        "Return ONLY a JSON object with these exact keys: "
        '"scheduled_time", "rephrased_message", and "time_extracted". '
        "scheduled_time must be an ISO8601 string with +05:30 offset or null if no time is found. "
        "rephrased_message must be a natural spoken message that always starts with "
        f'"Hi {contact_name}, this is an automated message on behalf of {user_name}". '
        "time_extracted must be true only when a valid time was found. "
        "Handle natural language times like tomorrow 6pm, after 2 hours, next Saturday 10am, "
        "this Friday 3pm, call in 30 minutes, and next week Tuesday."
    )
    user_prompt = (
        f"Current IST time: {current_time_ist.isoformat()}\n"
        f"User name: {user_name}\n"
        f"Contact name: {contact_name}\n"
        f"Original message: {message}"
    )

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )
        raw_content = response.choices[0].message.content or ""
        payload = _extract_json_payload(raw_content)
        return _normalize_result(payload, user_name, contact_name, message)
    except Exception:
        LOGGER.exception("DeepSeek message processing failed, so the backend is using the fallback message flow.")
        return fallback_result
