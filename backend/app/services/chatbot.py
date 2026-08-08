from app.core.config import get_settings
from app.services.agriculture import local_agriculture_answer

SYSTEM_PROMPT = """You are AgriSense, a concise agriculture assistant. Give safe, practical, climate-aware guidance. Do not invent local regulations, pesticide labels, or diagnoses. Recommend soil tests or qualified local advice when decisions have high risk."""

def answer(message: str, history: list[dict]) -> str:
    settings = get_settings()
    if not settings.openai_api_key:
        return local_agriculture_answer(message)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history[-10:], {"role": "user", "content": message}]
        response = client.chat.completions.create(model=settings.openai_model, messages=messages, temperature=.3, max_tokens=500)
        return response.choices[0].message.content or local_agriculture_answer(message)
    except Exception:
        return local_agriculture_answer(message)
