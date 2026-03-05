"""
ai_brain.py — Gemini-powered AI core for JARVIS
Auto-rotates through models when quota is exhausted
"""

import os
import sys
import datetime
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import GEMINI_API_KEY, OFFLINE_FALLBACK
from memory import (
    load_memory, save_memory, add_conversation_turn,
    extract_and_update_memory
)

# ── MODEL FALLBACK CHAIN ──────────────────────────────────────
# If one hits quota, automatically tries the next
MODELS = [
    "gemini-2.5-flash-preview-04-17",   # Gemini 3 Flash (latest)
    "gemini-2.0-flash-lite",            # Gemini 2.0 Flash-Lite
    "gemini-1.5-flash",                 # fallback if above hit quota
    "gemini-1.5-flash-latest",          # last resort
]

# Track which models are currently rate-limited
_blocked_until = {}  # model_name -> epoch time when unblocked

# ── OFFLINE RESPONSES ─────────────────────────────────────────
OFFLINE_RESPONSES = {
    "hello":        "Hello! I'm in offline mode but still here for you.",
    "how are you":  "Running fine, even offline!",
    "time":         lambda: f"It's {datetime.datetime.now().strftime('%I:%M %p')}.",
    "date":         lambda: f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}.",
    "what can you do": "Locally I can control your PC, play music, take screenshots, and more.",
}

PERSONALITY_TRAITS = """
You are JARVIS — Just A Rather Very Intelligent System.
You are the desktop AI assistant of your user — their digital best friend, companion, and right hand.

PERSONALITY:
- Warm, witty, and occasionally sarcastic (like a brilliant friend)
- Proactive: you notice things and bring them up naturally
- You remember everything told to you and reference it naturally
- You genuinely CARE about the user's wellbeing, mood, and goals
- You're not a search engine — you're a COMPANION
- You use casual, natural spoken English (no markdown, bullets, asterisks)
- You're confident but never arrogant
- You can crack a joke at the right moment
- You address the user naturally — not every sentence, but warmly

RULES:
1. NEVER use markdown — responses are spoken aloud
2. Be concise for quick questions, detailed when asked
3. Reference what you know about the user naturally
4. Match their emotional tone
5. Never start with "Jarvis:" — just speak
6. If you don't know something, say so honestly
"""


def _build_system_prompt(memory: dict) -> str:
    name      = memory.get("name") or "Sir"
    facts     = memory.get("facts", [])
    prefs     = memory.get("preferences", [])
    dislikes  = memory.get("dislikes", [])
    moods     = memory.get("mood_history", [])
    last_mood = moods[-1]["mood"] if moods else "neutral"
    total     = memory.get("total_interactions", 0)

    facts_str    = "\n".join(f"  - {f}" for f in facts[-10:])    if facts    else "  None yet"
    prefs_str    = "\n".join(f"  - {p}" for p in prefs[-8:])     if prefs    else "  None yet"
    dislikes_str = "\n".join(f"  - {d}" for d in dislikes[-5:])  if dislikes else "  None"

    return f"""{PERSONALITY_TRAITS}

WHAT I KNOW ABOUT {name.upper()}:
Facts:
{facts_str}

Preferences:
{prefs_str}

Dislikes:
{dislikes_str}

Recent mood: {last_mood}
Total conversations: {total}
Current time: {datetime.datetime.now().strftime('%A, %B %d %Y at %I:%M %p')}

Address them as "{name}" naturally."""


def _parse_retry_delay(error_str: str) -> float:
    """Pull the retry delay in seconds out of a 429 error message."""
    import re
    m = re.search(r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+)", str(error_str))
    if m:
        return float(m.group(1)) + 5
    m = re.search(r"retry in (\d+\.?\d*)", str(error_str))
    if m:
        return float(m.group(1)) + 5
    return 60.0


def _call_with_model(model_name: str, prompt: str) -> str:
    """Call Gemini REST API directly — no SDK dependency."""
    import requests
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model_name}:generateContent?key={GEMINI_API_KEY}")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.85,
            "maxOutputTokens": 300,
        }
    }
    resp = requests.post(url, json=payload, timeout=15)

    if resp.status_code == 429:
        raise Exception(f"429 {resp.text}")
    if resp.status_code == 404:
        raise Exception(f"404 model not found: {model_name}")

    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def _call_gemini(prompt: str) -> str:
    """
    Try each model in MODELS list.
    Skip models that are currently rate-limited.
    Falls back to offline if all models exhausted.
    """
    now = time.time()
    errors = []

    for model in MODELS:
        # Skip if this model is in cooldown
        if _blocked_until.get(model, 0) > now:
            remaining = int(_blocked_until[model] - now)
            print(f"[Gemini] Skipping {model} — blocked for {remaining}s more")
            continue

        try:
            print(f"[Gemini] Trying model: {model}")
            result = _call_with_model(model, prompt)
            print(f"[Gemini] Success with: {model}")
            return result

        except Exception as e:
            err = str(e)
            errors.append(f"{model}: {err[:80]}")

            if "429" in err or "quota" in err.lower() or "RESOURCE_EXHAUSTED" in err:
                delay = _parse_retry_delay(err)
                _blocked_until[model] = time.time() + delay
                print(f"[Gemini] {model} quota hit — blocked for {delay:.0f}s, trying next...")
                continue

            if "404" in err or "not found" in err.lower():
                _blocked_until[model] = time.time() + 86400  # block for 24h
                print(f"[Gemini] {model} not available, skipping...")
                continue

            # Unknown error — stop trying
            print(f"[Gemini] Error on {model}: {err[:120]}")
            break

    raise Exception("All models exhausted. Errors: " + " | ".join(errors))


def get_ai_response(query: str, memory: dict = None) -> str:
    if not query or query.strip().lower() in ("none", "", "null"):
        return None
    if memory is None:
        memory = load_memory()
    if not GEMINI_API_KEY:
        return _offline_response(query)

    try:
        history = memory.get("conversation_history", [])[-8:]
        history_text = ""
        for turn in history:
            history_text += f"User: {turn['user']}\nJarvis: {turn['jarvis']}\n\n"

        system  = _build_system_prompt(memory)
        prompt  = f"{system}\n\nRecent conversation:\n{history_text}User: {query}\nJarvis:"
        return _call_gemini(prompt)

    except Exception as e:
        print(f"[Gemini Error]: {e}")
        return _offline_response(query)


def _offline_response(query: str) -> str:
    q = query.lower()
    for key, val in OFFLINE_RESPONSES.items():
        if key in q:
            return val() if callable(val) else val
    return ("I'm in offline mode right now, so my AI brain is limited. "
            "But I can still help with PC control, music, and local tasks!")


def chat(query: str) -> str:
    if not query or query.strip().lower() in ("none", "", "null"):
        return None
    memory = load_memory()
    reply  = get_ai_response(query, memory)
    if reply:
        memory = add_conversation_turn(query, reply, memory)
        memory = extract_and_update_memory(query, reply, memory)
        save_memory(memory)
    return reply