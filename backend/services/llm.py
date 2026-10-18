"""呼叫 Gemini 寫一段文字。沒有設定金鑰或呼叫失敗時回傳 None，由呼叫端改用規則產生的文字。"""

import logging

from backend.core.config import read_env_value

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-3.8-flash"


def generate_text(system_instruction: str, content: str) -> str | None:
    api_key = read_env_value("GEMINI_API_KEY")
    if api_key is None:
        return None
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=read_env_value("GEMINI_MODEL") or DEFAULT_MODEL,
            contents=content,
            config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.3),
        )
    except Exception:
        logger.exception("呼叫 Gemini 失敗")
        return None
    text = (response.text or "").strip()
    return text or None
