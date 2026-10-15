from google import genai
from app.core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

for model in ["gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.6-flash"]:
    try:
        r = client.models.generate_content(model=model, contents="Reply with the single word: ok")
        print(f"{model}: WORKS -> {r.text.strip()}")
    except Exception as exc:
        print(f"{model}: FAILED -> {str(exc)[:120]}")