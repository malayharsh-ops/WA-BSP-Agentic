"""
Language detection for incoming WhatsApp messages.
Falls back gracefully if langdetect is unavailable.
"""

SUPPORTED_LANGUAGES = {"hi", "mr", "gu", "te", "kn", "ta", "en"}
DEFAULT_LANGUAGE = "hi"


def detect_language(text: str) -> str:
    """
    Detect language from text. Returns ISO 639-1 code.
    Falls back to DEFAULT_LANGUAGE on any error.
    """
    try:
        from langdetect import detect, LangDetectException
        code = detect(text)
        # langdetect returns zh-cn etc — normalise
        code = code.split("-")[0].lower()
        return code if code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    except Exception:
        return DEFAULT_LANGUAGE


# Greeting templates per language (used for outbound campaign openers)
GREETINGS = {
    "hi": "नमस्ते! मैं Priya हूँ, JSW ONE MSME से।",
    "mr": "नमस्कार! मी Priya आहे, JSW ONE MSME मधून।",
    "gu": "નમસ્તે! હું Priya છું, JSW ONE MSME તરફથી।",
    "te": "నమస్కారం! నేను Priya, JSW ONE MSME నుండి।",
    "kn": "ನಮಸ್ಕಾರ! ನಾನು Priya, JSW ONE MSME ಯಿಂದ।",
    "ta": "வணக்கம்! நான் Priya, JSW ONE MSME இல் இருந்து।",
    "en": "Hello! I'm Priya from JSW ONE MSME.",
}


def greeting_for(language: str) -> str:
    return GREETINGS.get(language, GREETINGS["en"])
