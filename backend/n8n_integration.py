"""
n8n_integration.py — n8n Workflow Automation Bridge for JARVIS

SETUP GUIDE:
1. Install n8n: npm install -g n8n  OR  docker run -it --rm -p 5678:5678 n8nio/n8n
2. Open: http://localhost:5678
3. Create workflows triggered by JARVIS webhooks

SUGGESTED N8N WORKFLOWS FOR JARVIS:
════════════════════════════════════════════════════════════════
1. EMAIL DIGEST     → Every morning, collect unread emails → summarize → speak
2. SMART HOME       → "Jarvis, turn off lights" → Home Assistant webhook
3. SPOTIFY MOOD     → Detect mood from voice → Auto-queue playlist
4. DAILY BRIEF      → Weather + News + Calendar events → Morning read
5. AUTO-SAVE NOTES  → Voice notes → Google Docs / Notion
6. GITHUB ALERTS    → New PR/issue → JARVIS notifies you
7. CALENDAR SYNC    → Google Calendar events → JARVIS reminders
8. FILE BACKUP      → "Jarvis, backup my project" → Cloud backup trigger
9. TEAMS MESSAGES   → Unread Teams msgs → JARVIS reads aloud
10. HABIT TRACKER   → Daily check-in → Log in Airtable/Sheets
════════════════════════════════════════════════════════════════
"""

import requests
import datetime
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import N8N_WEBHOOK_URL, USER_NAME
from voice_engine import speak


BASE_URL = N8N_WEBHOOK_URL.rstrip("/webhook/jarvis") if N8N_WEBHOOK_URL else "http://localhost:5678"
WORKFLOWS = {
    "email":      f"{BASE_URL}/webhook/jarvis-email",
    "calendar":   f"{BASE_URL}/webhook/jarvis-calendar",
    "smarthome":  f"{BASE_URL}/webhook/jarvis-home",
    "spotify":    f"{BASE_URL}/webhook/jarvis-spotify",
    "notes":      f"{BASE_URL}/webhook/jarvis-notes",
    "backup":     f"{BASE_URL}/webhook/jarvis-backup",
    "github":     f"{BASE_URL}/webhook/jarvis-github",
    "weather":    f"{BASE_URL}/webhook/jarvis-weather",
    "briefing":   f"{BASE_URL}/webhook/jarvis-briefing",
    "habit":      f"{BASE_URL}/webhook/jarvis-habit",
    "default":    N8N_WEBHOOK_URL,
}


def trigger(workflow: str = "default", payload: dict = None) -> dict:
    """
    Trigger an n8n workflow by name.
    Returns response JSON or error dict.
    """
    url = WORKFLOWS.get(workflow, WORKFLOWS["default"])
    data = {
        "source": "jarvis",
        "user": USER_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        **(payload or {})
    }
    try:
        resp = requests.post(url, json=data, timeout=8)
        resp.raise_for_status()
        return resp.json() if resp.text else {"status": "ok"}
    except requests.exceptions.ConnectionError:
        print(f"[n8n] Not connected — start n8n: http://localhost:5678")
        return {"error": "n8n not running"}
    except Exception as e:
        print(f"[n8n Error]: {e}")
        return {"error": str(e)}


def morning_briefing() -> str:
    """Trigger the morning briefing workflow."""
    result = trigger("briefing")
    if "error" in result:
        return "Morning briefing automation is not set up. Starting local briefing."
    summary = result.get("summary", "")
    if summary:
        speak(summary)
    return summary


def save_voice_note(note: str) -> str:
    """Save a voice note via n8n (to Notion, Google Docs, etc.)."""
    result = trigger("notes", {"note": note, "time": datetime.datetime.now().isoformat()})
    if "error" not in result:
        speak("Note saved.")
        return "Note saved."
    # Fallback: save locally
    _save_local_note(note)
    speak("Note saved locally.")
    return "Note saved locally."


def _save_local_note(note: str):
    notes_file = os.path.join(os.path.dirname(__file__), "notes.txt")
    with open(notes_file, "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        f.write(f"[{timestamp}] {note}\n")


def smart_home_command(command: str, device: str = None) -> str:
    """Control smart home devices via n8n → Home Assistant."""
    result = trigger("smarthome", {
        "command": command,
        "device": device or "all",
    })
    if "error" in result:
        return "Smart home automation not configured."
    return result.get("message", f"Smart home command sent: {command}")


def get_calendar_events() -> list:
    """Fetch today's calendar events via n8n → Google Calendar."""
    result = trigger("calendar", {"action": "today"})
    return result.get("events", [])


def detect_and_play_mood_music(mood: str) -> str:
    """Trigger Spotify mood playlist based on mood."""
    mood_playlists = {
        "happy": "happy pop",
        "sad": "melancholic indie",
        "focused": "lo-fi study beats",
        "energetic": "workout pump",
        "calm": "ambient meditation",
        "romantic": "romantic jazz",
        "angry": "metal release",
    }
    query = mood_playlists.get(mood.lower(), mood)
    result = trigger("spotify", {"action": "play", "query": query})
    if "error" in result:
        # Fallback: open YouTube
        import webbrowser
        webbrowser.open(f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}")
        return f"Playing {query} on YouTube."
    return f"Playing {query} playlist for your {mood} mood."


# ── EXAMPLE N8N WORKFLOW JSON TEMPLATES ──────────────────────
# Save these in n8n to get started quickly

N8N_TEMPLATE_MORNING_BRIEFING = {
    "name": "JARVIS Morning Briefing",
    "nodes": [
        {
            "type": "n8n-nodes-base.webhook",
            "name": "JARVIS Trigger",
            "parameters": {"path": "jarvis-briefing", "method": "POST"}
        },
        {
            "type": "n8n-nodes-base.httpRequest",
            "name": "Get Weather",
            "parameters": {"url": "http://api.weatherapi.com/v1/current.json"}
        },
        {
            "type": "n8n-nodes-base.httpRequest",
            "name": "Get News",
            "parameters": {"url": "https://gnews.io/api/v4/top-headlines"}
        },
        {
            "type": "n8n-nodes-base.code",
            "name": "Build Summary",
            "parameters": {
                "code": "return [{summary: `Good morning! Weather: ${$node['Get Weather'].json.current.condition.text}. Top news: ${$node['Get News'].json.articles[0].title}`}]"
            }
        }
    ]
}