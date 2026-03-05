"""
memory.py — Persistent Memory System for JARVIS
Stores user facts, preferences, reminders, conversation history
"""

import os
import json
import datetime
import threading
from typing import Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import MEMORY_FILE, USER_NAME, GEMINI_API_KEY

os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)

_save_lock = threading.Lock()


def _default_memory():
    return {
        "name": USER_NAME,
        "birthday": None,
        "facts": [],
        "preferences": [],
        "dislikes": [],
        "reminders": [],
        "mood_history": [],
        "conversation_history": [],
        "daily_notes": {},
        "contacts": {},
        "tasks": [],
        "topics_interested": [],
        "last_seen": None,
        "total_interactions": 0,
        "created_at": datetime.datetime.now().isoformat()
    }


def load_memory() -> dict:
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default = _default_memory()
                for k, v in default.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception:
            pass
    return _default_memory()


def save_memory(memory: dict):
    with _save_lock:
        try:
            os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
            memory["last_seen"] = datetime.datetime.now().isoformat()
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Memory save error]: {e}")


def remember_fact(fact: str, memory: Optional[dict] = None) -> dict:
    save_flag = memory is None
    if memory is None:
        memory = load_memory()
    fact = fact.strip()
    if fact and fact not in memory["facts"]:
        memory["facts"].append(fact)
        print(f"[Memory] Remembered: {fact}")
    if save_flag:
        save_memory(memory)
    return memory


def remember_preference(pref: str, memory: Optional[dict] = None) -> dict:
    save_flag = memory is None
    if memory is None:
        memory = load_memory()
    if pref and pref not in memory["preferences"]:
        memory["preferences"].append(pref)
    if save_flag:
        save_memory(memory)
    return memory


def add_reminder(text: str, time_str: str, memory: Optional[dict] = None) -> dict:
    save_flag = memory is None
    if memory is None:
        memory = load_memory()
    memory["reminders"].append({
        "text": text,
        "time": time_str,
        "created": datetime.datetime.now().isoformat(),
        "done": False
    })
    if save_flag:
        save_memory(memory)
    return memory


def get_pending_reminders(memory: Optional[dict] = None) -> list:
    if memory is None:
        memory = load_memory()
    now = datetime.datetime.now()
    pending = []
    for r in memory.get("reminders", []):
        if r.get("done"):
            continue
        try:
            if datetime.datetime.fromisoformat(r["time"]) <= now:
                pending.append(r)
        except Exception:
            pass
    return pending


def mark_reminder_done(reminder_text: str):
    memory = load_memory()
    for r in memory.get("reminders", []):
        if r.get("text") == reminder_text:
            r["done"] = True
    save_memory(memory)


def add_task(task: str, memory: Optional[dict] = None) -> dict:
    save_flag = memory is None
    if memory is None:
        memory = load_memory()
    memory["tasks"].append({
        "task": task,
        "created": datetime.datetime.now().isoformat(),
        "done": False
    })
    if save_flag:
        save_memory(memory)
    return memory


def get_pending_tasks(memory: Optional[dict] = None) -> list:
    if memory is None:
        memory = load_memory()
    return [t for t in memory.get("tasks", []) if not t.get("done")]


def add_conversation_turn(user_msg: str, jarvis_msg: str, memory: Optional[dict] = None) -> dict:
    save_flag = memory is None
    if memory is None:
        memory = load_memory()
    memory["conversation_history"].append({
        "user": user_msg,
        "jarvis": jarvis_msg,
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    memory["conversation_history"] = memory["conversation_history"][-60:]
    memory["total_interactions"] = memory.get("total_interactions", 0) + 1
    if save_flag:
        save_memory(memory)
    return memory


def clear_memory():
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)


def summarize_memory(memory: Optional[dict] = None) -> str:
    if memory is None:
        memory = load_memory()
    name  = memory.get("name") or USER_NAME
    facts = memory.get("facts", [])
    prefs = memory.get("preferences", [])
    dislikes = memory.get("dislikes", [])
    tasks = get_pending_tasks(memory)

    parts = [f"Here's what I know about you, {name}."]
    if facts:    parts.append("Facts: "       + ". ".join(facts[:5])    + ".")
    if prefs:    parts.append("Preferences: " + ". ".join(prefs[:5])    + ".")
    if dislikes: parts.append("You dislike: " + ". ".join(dislikes[:3]) + ".")
    if tasks:    parts.append(f"You have {len(tasks)} pending tasks.")
    if not facts and not prefs:
        parts.append("Tell me more about yourself so I can remember!")
    return " ".join(parts)


def _call_gemini_for_memory(prompt: str) -> str:
    """
    Call Gemini using whichever SDK works — 3 fallback strategies.
    Separate from ai_brain.py to avoid circular imports.
    """
    # Strategy 1: New google-genai SDK
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=300, temperature=0.1)
        )
        return response.text.strip()
    except ImportError:
        pass
    except Exception as e:
        raise e

    # Strategy 2: Old google-generativeai SDK
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        response = model.generate_content(prompt)
        return response.text.strip()
    except ImportError:
        pass
    except Exception as e:
        raise e

    # Strategy 3: Direct REST API (no SDK at all)
    import requests
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"gemini-2.0-flash-lite:generateContent?key={GEMINI_API_KEY}")
    resp = requests.post(url, json={
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 300, "temperature": 0.1}
    }, timeout=10)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def extract_and_update_memory(user_query: str, ai_reply: str, memory: dict) -> dict:
    """Use Gemini to extract facts from conversation turn."""
    if not GEMINI_API_KEY:
        return memory
    try:
        prompt = f"""Extract any personal information the USER shared in this exchange.
Return ONLY valid JSON, no markdown:
{{
  "name": "user name if mentioned else null",
  "new_facts": ["list of personal facts shared"],
  "new_preferences": ["things user likes"],
  "new_dislikes": ["things user dislikes"],
  "mood": "positive|negative|neutral",
  "birthday": "date if mentioned else null",
  "reminder": {{"text": "...", "time": "ISO datetime"}} or null
}}

User said: "{user_query}"
Jarvis replied: "{ai_reply}"

Return ONLY valid JSON."""

        raw = _call_gemini_for_memory(prompt)
        raw = raw.replace("```json", "").replace("```", "").strip()
        extracted = json.loads(raw)

        if extracted.get("name") and memory.get("name") in (None, USER_NAME, "Sir"):
            memory["name"] = extracted["name"]
        for f in extracted.get("new_facts", []):
            if f and f not in memory["facts"]:
                memory["facts"].append(f)
        for p in extracted.get("new_preferences", []):
            if p and p not in memory["preferences"]:
                memory["preferences"].append(p)
        for d in extracted.get("new_dislikes", []):
            if d and d not in memory["dislikes"]:
                memory["dislikes"].append(d)
        if extracted.get("mood"):
            memory["mood_history"].append({
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "mood": extracted["mood"]
            })
            memory["mood_history"] = memory["mood_history"][-30:]
        if extracted.get("birthday"):
            memory["birthday"] = extracted["birthday"]
        if extracted.get("reminder") and extracted["reminder"].get("text"):
            memory["reminders"].append({
                **extracted["reminder"],
                "created": datetime.datetime.now().isoformat(),
                "done": False
            })

    except Exception as e:
        print(f"[Memory extraction error]: {e}")
    return memory