"""
config.py — Central configuration for JARVIS
All settings loaded from .env with sensible defaults
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Identity ──────────────────────────────────────────────────
USER_NAME       = os.getenv("USER_NAME", "Sir")
ASSISTANT_NAME  = os.getenv("ASSISTANT_NAME", "Jarvis")
WAKE_WORD       = os.getenv("WAKE_WORD", "jarvis").lower()
CITY            = os.getenv("CITY", "Vijayawada")
COUNTRY         = os.getenv("COUNTRY", "India")

# ── API Keys ──────────────────────────────────────────────────
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY", "")
WEATHER_API_KEY  = os.getenv("WEATHER_API_KEY", "")
GNEWS_API_KEY    = os.getenv("GNEWS_API_KEY", "")
WOLFRAM_API_KEY  = os.getenv("WOLFRAM_API_KEY", "")
N8N_WEBHOOK_URL  = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/jarvis")
EMAIL_ADDRESS    = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD   = os.getenv("EMAIL_APP_PASSWORD", "")

# ── Voice ─────────────────────────────────────────────────────
VOICE_INDEX  = int(os.getenv("VOICE_INDEX", "1"))
SPEECH_RATE  = int(os.getenv("SPEECH_RATE", "170"))

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE  = os.path.join(BASE_DIR, "memory", "jarvis_memory.json")
LOG_FILE     = os.path.join(BASE_DIR, "logs", "jarvis.log")
ASSETS_DIR   = os.path.join(BASE_DIR, "assets")

# ── WebSocket ─────────────────────────────────────────────────
WS_HOST = "localhost"
WS_PORT = 8765

# ── Feature Flags ─────────────────────────────────────────────
OFFLINE_FALLBACK = os.getenv("OFFLINE_FALLBACK", "true").lower() == "true"

# ── Gesture Thresholds ────────────────────────────────────────
GESTURE_PINCH_CLOSE   = 0.04   # fingers touching = volume down / scroll down
GESTURE_PINCH_OPEN    = 0.12   # fingers apart = volume up / scroll up
GESTURE_SWIPE_THRESH  = 0.15   # wrist x-delta for app switch
GESTURE_FIST_THRESH   = 0.06   # all fingers curled = pause