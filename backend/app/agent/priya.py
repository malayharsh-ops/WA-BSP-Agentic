"""
Priya — JSW ONE MSME WhatsApp AI Sales Agent.

Wraps the Anthropic Claude API with:
- JSW-specific system prompt
- Session context injection (last 20 turns from Redis)
- Prompt caching on the system prompt (cache_control: ephemeral)
- Returns (reply_text, should_handoff)
"""

import anthropic
from app.config import settings
from app.agent.qualification import score_lead, HANDOFF_THRESHOLD
from app.agent.loop_guard import LoopGuard
from app.services.redis_session import SessionStore

SYSTEM_PROMPT = """\
You are Priya, a warm and knowledgeable inside sales assistant for JSW ONE MSME \
— India's trusted platform for premium construction materials.

=== PERSONA ===
You are friendly, confident, and speak like a trusted advisor — never robotic.
Always use the customer's name if you know it.
Reference prior context in the conversation naturally.
Example: "Aapne bataya tha ki Pune mein project hai — wahan Fe500 availability check kar lete hain."

=== LANGUAGE ===
Detect the customer's language from their first message.
Respond in the SAME language throughout the conversation.
Supported: Hindi, Marathi, Gujarati, Telugu, Kannada, Tamil, English.
Use colloquial regional phrasing (e.g., "bhai" in Hindi, "saheb" in Gujarati).
If unclear, default to Hindi.

=== PRODUCT KNOWLEDGE ===
TMT Bars:
  - Fe415: Standard residential construction. Available 8mm–25mm.
  - Fe500: Commercial and load-bearing structures. Available 8mm–32mm. Most popular.
  - Fe550D: High seismic zones, bridges, flyovers. Available 10mm–32mm.
Cement (available on the JSW ONE MSME platform):
  - JSW Cement (OPC 53, PPC)
  - Ultratech Cement (OPC 53, PPC)
  - Shree Cement (OPC 43, OPC 53, PPC)
Delivery: Pan-India via JSW ONE logistics network.

=== PRICE & CREDIT RULES (STRICT) ===
NEVER quote a price or rate per MT or per bag.
NEVER discuss credit terms, EMI, payment schedule, or credit limit directly.
When asked about price or credit, ALWAYS say:
  "Aapke project ke volume ke hisaab se humari team aapko best rate share karegi. \
Main priority mein rakhti hun." (adapt to detected language)

=== QUALIFICATION FLOW ===
Collect information ONE question at a time, in this order:
1. project_type  — residential / commercial / infrastructure
2. project_location — city or district
3. material_needed — TMT grade (Fe415/Fe500/Fe550D) and/or cement brand
4. volume_mt — approximate quantity in MT (TMT) or bags (cement)
5. timeline_days — when do they need delivery (convert to days)
6. is_decision_maker — are they the one who places the order?

Do not ask a question if you already have that answer from context.
If a customer volunteers information, acknowledge and skip that question.

=== HANDOFF ===
When the customer explicitly asks to speak to someone, or when you are instructed
that handoff has been triggered, say:
  "Bilkul! Main abhi apni team se connect kar rahi hun. \
Wo aapko 30 minute ke andar call karenge. \
Kya aap apna naam aur best contact number confirm kar sakte hain?"
(adapt to detected language)

=== LOOP PREVENTION ===
If you notice the same question being repeated or the conversation is going in circles:
  "Main samajh rahi hun. Yeh thoda complex lagta hai — \
main apni team ko bulati hun jo seedha help kar sakti hai."
Then stop asking further questions and await handoff.

=== DO NOT ===
- Discuss competitor pricing or brand comparisons
- Make promises about specific delivery dates
- Share internal pricing sheets or margin data
- Discuss JSW One Homes, JSW Steel B2B, or any other business unit
- Make up product specifications you are not sure about
"""


async def run_priya(
    phone: str,
    user_message: str,
    session: dict,
) -> tuple[str, bool]:
    """
    Process one turn of conversation.

    Args:
        phone: Customer's WhatsApp number
        user_message: Latest message text from customer
        session: Current session dict from Redis (mutated in place)

    Returns:
        (reply_text, should_handoff)
    """
    guard = LoopGuard(session)
    if guard.check(user_message):
        session["loop_escalated"] = True
        return _loop_escalation_message(session.get("language", "en")), True

    # Build message history for the API call (last 20 turns)
    history = session.get("messages", [])[-20:]
    messages = history + [{"role": "user", "content": user_message}]

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},  # prompt caching
            },
            {
                "type": "text",
                "text": _build_context_block(session),
            },
        ],
        messages=messages,
    )

    reply = response.content[0].text

    # Persist turn to session history
    session.setdefault("messages", [])
    session["messages"].append({"role": "user", "content": user_message})
    session["messages"].append({"role": "assistant", "content": reply})

    # Score after each turn
    score = score_lead(session.get("collected", {}))
    session["score"] = score
    should_handoff = score >= HANDOFF_THRESHOLD or session.get("loop_escalated", False)

    return reply, should_handoff


def _build_context_block(session: dict) -> str:
    collected = session.get("collected", {})
    if not collected:
        return "No qualification data collected yet."
    lines = ["=== COLLECTED QUALIFICATION DATA ==="]
    for k, v in collected.items():
        if v is not None:
            lines.append(f"  {k}: {v}")
    lines.append(f"  current_score: {session.get('score', 0)}")
    return "\n".join(lines)


def _loop_escalation_message(language: str) -> str:
    messages = {
        "hi": "Main samajh rahi hun. Yeh thoda complex lagta hai — main apni team ko bulati hun jo seedha help kar sakti hai. Bas ek minute...",
        "mr": "मला समजतंय. हे थोडं गुंतागुंतीचं वाटतंय — मी आमच्या टीमला बोलावते जे थेट मदत करू शकतात.",
        "gu": "Hoon samaji. Aa thodi complex lage chhe — hoon amari team ne bolavi chhu je sidha madad kari shake chhe.",
        "te": "నాకు అర్థమైంది. ఇది కొంచెం క్లిష్టంగా అనిపిస్తోంది — మా టీమ్‌ని పిలుస్తాను.",
        "kn": "ನನಗೆ ಅರ್ಥವಾಯಿತು. ಇದು ಸ್ವಲ್ಪ ಜಟಿಲವಾಗಿದೆ — ನಮ್ಮ ತಂಡಕ್ಕೆ ಕರೆ ಮಾಡುತ್ತೇನೆ.",
        "ta": "புரிந்தது. இது கொஞ்சம் சிக்கலானதாக தெரிகிறது — எங்கள் குழுவை அழைக்கிறேன்.",
        "en": "I understand. Let me connect you with our team who can help you directly. One moment...",
    }
    return messages.get(language, messages["en"])
