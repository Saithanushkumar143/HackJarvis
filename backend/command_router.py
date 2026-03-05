"""
command_router.py — JARVIS Command Intelligence
Routes spoken queries to the right handler
Handles both PC control commands and AI chat
"""

import os
import sys
import re
import datetime
import threading
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import USER_NAME, CITY, N8N_WEBHOOK_URL, WOLFRAM_API_KEY, GNEWS_API_KEY, WEATHER_API_KEY
from voice_engine import speak, take_command
from memory import (load_memory, save_memory, remember_fact, add_reminder,
                    add_task, get_pending_tasks, get_pending_reminders,
                    mark_reminder_done, summarize_memory, clear_memory)
from desktop_control import (
    open_app, close_app, switch_window, minimize_all,
    volume_up, volume_down, mute_toggle,
    media_play_pause, media_next, media_previous,
    youtube_skip_forward, youtube_skip_backward, youtube_fullscreen,
    take_screenshot, type_text, copy_text, paste_text, cut_text,
    lock_screen, get_system_stats, internet_speed,
    new_tab, close_tab, refresh_page, go_back, go_forward,
    show_notification, snap_left, snap_right, maximize_window
)
from ai_brain import chat


# ── COMMAND CATEGORIES ────────────────────────────────────────

PC_KEYWORDS = [
    "open", "close", "launch", "start", "exit", "quit",
    "play", "pause", "stop", "mute", "volume", "turn up", "turn down",
    "screenshot", "type", "write", "copy", "paste", "cut",
    "google", "youtube", "wikipedia", "search",
    "whatsapp", "message", "send",
    "weather", "news", "calculate", "math",
    "translate", "distance",
    "alarm", "timer", "remind", "reminder",
    "task", "schedule", "todo",
    "system", "cpu", "memory", "battery", "speed",
    "lock", "shutdown", "restart", "sleep",
    "skip", "rewind", "next", "previous", "forward", "back",
    "tab", "switch", "minimize", "maximize", "snap",
    "scroll", "click", "move",
    "remember", "forget", "memory",
    "spotify", "music", "song",
    "camera", "gesture",
    "email", "mail",
    "refresh", "reload",
    "fullscreen", "theater",
    "n8n", "automate",
]


def is_pc_command(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in PC_KEYWORDS)


# ── MAIN ROUTER ───────────────────────────────────────────────

def route(query: str) -> str:
    """
    Main routing function.
    Returns response text (already spoken internally by most handlers).
    """
    if not query or query.strip().lower() in ("none", "", "null"):
        return None

    q = query.lower().strip()

    # ══ MEMORY COMMANDS ══════════════════════════════════════

    if "remember that" in q or ("remember" in q and "that" in q):
        fact = re.sub(r"(jarvis|remember that|remember)", "", q).strip()
        remember_fact(fact)
        response = f"Got it. I've stored that: {fact}"
        speak(response)
        return response

    if any(p in q for p in ["what do you remember", "what do you know", "tell me what you know"]):
        response = summarize_memory()
        speak(response)
        return response

    if "clear your memory" in q or "forget everything" in q or "wipe memory" in q:
        clear_memory()
        response = "Memory cleared. Fresh start, as if we just met."
        speak(response)
        return response

    # ══ REMINDERS / TASKS ════════════════════════════════════

    if "remind me" in q or "set a reminder" in q:
        return _handle_reminder(q)

    if "show my reminders" in q or "pending reminders" in q:
        return _show_reminders()

    if "add task" in q or "add a task" in q or "todo" in q:
        task = re.sub(r"(jarvis|add task|add a task|todo)", "", q).strip()
        if not task:
            speak("What's the task?")
            task = take_command()
        add_task(task)
        response = f"Task added: {task}"
        speak(response)
        return response

    if "show tasks" in q or "my tasks" in q or "pending tasks" in q:
        tasks = get_pending_tasks()
        if tasks:
            task_list = ", ".join(t["task"] for t in tasks[:5])
            response = f"You have {len(tasks)} tasks. Here are the first few: {task_list}"
        else:
            response = "No pending tasks. You're all caught up!"
        speak(response)
        return response

    # ══ TIME / DATE ══════════════════════════════════════════

    if "the time" in q or "what time" in q:
        t = datetime.datetime.now().strftime("%I:%M %p")
        response = f"It's {t}, {USER_NAME}."
        speak(response)
        return response

    if "the date" in q or "what day" in q or "today's date" in q:
        d = datetime.datetime.now().strftime("%A, %B %d, %Y")
        response = f"Today is {d}."
        speak(response)
        return response

    # ══ GREETINGS ════════════════════════════════════════════

    if _is_greeting(q):
        return _handle_greeting(q)

    # ══ GESTURE CONTROL ══════════════════════════════════════

    if "gesture" in q or "hand control" in q or "iron man" in q:
        if "stop" in q or "off" in q or "disable" in q:
            from gesture_control import get_gesture_controller
            get_gesture_controller().stop()
            response = "Gesture control deactivated."
            speak(response)
            return response
        else:
            from gesture_control import get_gesture_controller
            get_gesture_controller().start()
            return "Gesture control activated."

    # ══ VOLUME ═══════════════════════════════════════════════

    if "volume up" in q or "increase volume" in q or "louder" in q:
        steps = _extract_number(q, 5)
        volume_up(steps)
        response = f"Volume increased."
        speak(response)
        return response

    if "volume down" in q or "decrease volume" in q or "quieter" in q or "lower volume" in q:
        steps = _extract_number(q, 5)
        volume_down(steps)
        response = f"Volume decreased."
        speak(response)
        return response

    if "mute" in q:
        mute_toggle()
        response = "Muted." if "unmute" not in q else "Unmuted."
        speak(response)
        return response

    # ══ MEDIA ════════════════════════════════════════════════

    if any(p in q for p in ["play pause", "pause", "resume"]) and "music" not in q:
        response = media_play_pause()
        speak(response)
        return response

    if "next song" in q or "next track" in q:
        response = media_next()
        speak(response)
        return response

    if "previous song" in q or "previous track" in q or "last song" in q:
        response = media_previous()
        speak(response)
        return response

    if "skip" in q and ("second" in q or "forward" in q):
        secs = _extract_number(q, 10)
        response = youtube_skip_forward(secs)
        speak(response)
        return response

    if "rewind" in q or ("skip" in q and "back" in q):
        secs = _extract_number(q, 10)
        response = youtube_skip_backward(secs)
        speak(response)
        return response

    if "fullscreen" in q or "full screen" in q:
        response = youtube_fullscreen()
        speak(response)
        return response

    if "theater mode" in q:
        response = youtube_theater_mode()
        speak(response)
        return response

    # ══ APP CONTROL ══════════════════════════════════════════

    if "open" in q or "launch" in q or "start" in q:
        app_name = re.sub(r"(jarvis|open|launch|start)", "", q).strip()
        response = open_app(app_name)
        return response

    if "close" in q or "exit" in q or "quit" in q:
        if "tab" in q:
            response = close_tab()
            speak(response)
            return response
        app_name = re.sub(r"(jarvis|close|exit|quit)", "", q).strip()
        response = close_app(app_name)
        speak(response)
        return response

    if "switch" in q and ("app" in q or "window" in q):
        response = switch_window()
        speak(response)
        return response

    if "minimize all" in q or "show desktop" in q:
        response = minimize_all()
        speak(response)
        return response

    if "maximize" in q:
        response = maximize_window()
        speak(response)
        return response

    if "snap left" in q:
        response = snap_left()
        speak(response)
        return response

    if "snap right" in q:
        response = snap_right()
        speak(response)
        return response

    # ══ SCREENSHOT ═══════════════════════════════════════════

    if "screenshot" in q:
        response = take_screenshot()
        speak(response)
        return response

    # ══ SYSTEM ═══════════════════════════════════════════════

    if "system" in q and ("status" in q or "stats" in q or "info" in q or "diagnostics" in q):
        response = get_system_stats()
        speak(response)
        return response

    if "internet speed" in q or "network speed" in q:
        threading.Thread(target=_run_speed_test, daemon=True).start()
        return "Running speed test..."

    if "lock" in q and "screen" in q:
        response = lock_screen()
        speak(response)
        return response

    if "shutdown" in q:
        speak("Are you sure? Say yes to confirm.")
        confirm = take_command(timeout=5)
        if "yes" in confirm.lower():
            from desktop_control import shutdown_system
            shutdown_system()
        else:
            speak("Shutdown cancelled.")
        return ""

    if "restart" in q or "reboot" in q:
        speak("Are you sure? Say yes to confirm.")
        confirm = take_command(timeout=5)
        if "yes" in confirm.lower():
            from desktop_control import restart_system
            restart_system()
        else:
            speak("Restart cancelled.")
        return ""

    # ══ SEARCH ═══════════════════════════════════════════════

    if "youtube" in q and ("search" in q or "play" in q or "find" in q):
        return _search_youtube(q)

    if "google" in q or "search" in q:
        return _search_google(q)

    if "wikipedia" in q:
        return _search_wikipedia(q)

    # ══ WEATHER ══════════════════════════════════════════════

    if "weather" in q or "temperature" in q:
        return _get_weather(q)

    # ══ NEWS ═════════════════════════════════════════════════

    if "news" in q:
        threading.Thread(target=_get_news, args=(q,), daemon=True).start()
        return "Fetching the latest news for you."

    # ══ CALCULATE ════════════════════════════════════════════

    if "calculate" in q or "what is" in q and any(op in q for op in ["+", "-", "*", "/", "plus", "minus", "times", "divided"]):
        return _calculate(q)

    # ══ TRANSLATE ════════════════════════════════════════════

    if "translate" in q:
        return _translate(q)

    # ══ WHATSAPP ═════════════════════════════════════════════

    if "whatsapp" in q or "send message" in q or "send a message" in q:
        threading.Thread(target=_send_whatsapp, daemon=True).start()
        return "Opening WhatsApp."

    # ══ BROWSER ══════════════════════════════════════════════

    if "new tab" in q:
        response = new_tab()
        speak(response)
        return response

    if "close tab" in q:
        response = close_tab()
        speak(response)
        return response

    if "refresh" in q or "reload" in q:
        response = refresh_page()
        speak(response)
        return response

    if "go back" in q:
        response = go_back()
        speak(response)
        return response

    if "go forward" in q:
        response = go_forward()
        speak(response)
        return response

    # ══ TYPING ═══════════════════════════════════════════════

    if "type" in q and len(q) > 6:
        text = re.sub(r"(jarvis|type|write that|write)", "", q).strip()
        speak("Typing now.")
        threading.Thread(target=type_text, args=(text,), daemon=True).start()
        return f"Typed: {text}"

    # ══ CLIPBOARD ════════════════════════════════════════════

    if "copy" in q:
        response = copy_text()
        speak(response)
        return response

    if "paste" in q:
        response = paste_text()
        speak(response)
        return response

    if "cut" in q:
        response = cut_text()
        speak(response)
        return response

    # ══ MUSIC / SPOTIFY ══════════════════════════════════════

    if "play music" in q or "play songs" in q or "spotify" in q:
        return _play_spotify(q)

    # ══ N8N AUTOMATION ═══════════════════════════════════════

    if "automate" in q or "n8n" in q or "workflow" in q:
        return _trigger_n8n(q)

    # ══ SLEEP MODE ═══════════════════════════════════════════

    if "go to sleep" in q or "sleep mode" in q or "quiet" in q:
        response = f"Going to standby, {USER_NAME}. Just say my name when you need me."
        speak(response)
        return "__SLEEP__"

    # ══ FAREWELL ═════════════════════════════════════════════

    if any(w in q for w in ["goodbye", "good night", "bye", "take care"]):
        _farewell_response(q)
        return "__SLEEP__"

    # ══ JOKES ════════════════════════════════════════════════

    if "joke" in q or "make me laugh" in q or "tell me something funny" in q:
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything.",
            "I told my computer I needed a break. Now it won't stop sending me Kit-Kat ads.",
            "Why do programmers prefer dark mode? Because light attracts bugs.",
            "I'm reading a book about anti-gravity. It's impossible to put down.",
            "Why did the scarecrow win an award? Because he was outstanding in his field."
        ]
        import random
        joke = random.choice(jokes)
        speak(joke)
        return joke

    # ══ FALLBACK: AI CHAT ════════════════════════════════════

    response = chat(query)
    if response:
        speak(response)
    return response


# ── HANDLER HELPERS ───────────────────────────────────────────

def _is_greeting(q: str) -> bool:
    greets = ["hello", "hi ", "hey ", "good morning", "good afternoon",
              "good evening", "good night", "what's up", "how are you"]
    return any(g in q for g in greets)


def _handle_greeting(q: str) -> str:
    hour = datetime.datetime.now().hour
    if "how are you" in q:
        response = f"I'm running perfectly, {USER_NAME}. All systems are optimal. How are you doing?"
    elif "good morning" in q or hour < 12:
        response = f"Good morning, {USER_NAME}! Ready to have a productive day? I'm at your service."
    elif "good afternoon" in q or hour < 17:
        response = f"Good afternoon, {USER_NAME}. Hope your day is going well. What can I do for you?"
    elif "good evening" in q or hour < 22:
        response = f"Good evening, {USER_NAME}. Time to wind down, or are you still going strong?"
    else:
        response = f"It's getting late, {USER_NAME}. Still burning the midnight oil?"

    # Check for pending reminders and mention them
    reminders = get_pending_reminders()
    if reminders:
        response += f" By the way, you have {len(reminders)} pending reminder{'s' if len(reminders) > 1 else ''}."

    speak(response)
    return response


def _farewell_response(q: str):
    hour = datetime.datetime.now().hour
    tasks = get_pending_tasks()
    task_note = f" Don't forget, you still have {len(tasks)} tasks pending." if tasks else ""
    if "good night" in q or hour >= 21:
        speak(f"Good night, {USER_NAME}. Sleep well.{task_note} I'll be here when you wake up.")
    else:
        speak(f"See you later, {USER_NAME}.{task_note} Call me anytime.")


def _handle_reminder(q: str) -> str:
    speak("What should I remind you about?")
    text = take_command()
    if text in ("None", ""):
        return "No reminder set."
    speak("When? Please say the time.")
    time_str = take_command()
    # Parse time - for simplicity, store as string and parse later
    now = datetime.datetime.now()
    reminder_time = _parse_reminder_time(time_str, now)
    add_reminder(text, reminder_time.isoformat() if reminder_time else "")
    response = f"Reminder set: {text}."
    speak(response)
    return response


def _show_reminders() -> str:
    reminders = get_pending_reminders()
    if not reminders:
        response = "No pending reminders."
    else:
        items = [r["text"] for r in reminders[:4]]
        response = f"You have {len(reminders)} pending reminders: " + ", ".join(items) + "."
    speak(response)
    return response


def _parse_reminder_time(time_str: str, base: datetime.datetime) -> datetime.datetime:
    """Simple time parser — expand as needed."""
    t = time_str.lower()
    try:
        if "minute" in t:
            mins = _extract_number(t, 5)
            return base + datetime.timedelta(minutes=mins)
        if "hour" in t:
            hrs = _extract_number(t, 1)
            return base + datetime.timedelta(hours=hrs)
        # Try parsing HH:MM format
        for fmt in ["%I:%M %p", "%H:%M", "%I %p"]:
            try:
                parsed = datetime.datetime.strptime(t, fmt)
                dt = base.replace(hour=parsed.hour, minute=parsed.minute, second=0)
                if dt < base:
                    dt += datetime.timedelta(days=1)
                return dt
            except Exception:
                pass
    except Exception:
        pass
    # Default: 5 minutes from now
    return base + datetime.timedelta(minutes=5)


def _extract_number(text: str, default: int) -> int:
    numbers = re.findall(r"\d+", text)
    return int(numbers[0]) if numbers else default


def _search_youtube(q: str) -> str:
    term = re.sub(r"(jarvis|youtube|search|play|find|on|in)", "", q).strip()
    url = f"https://www.youtube.com/results?search_query={term.replace(' ', '+')}"
    webbrowser.open(url)
    response = f"Searching YouTube for {term}."
    speak(response)
    return response


def _search_google(q: str) -> str:
    term = re.sub(r"(jarvis|google|search|search about|search for)", "", q).strip()
    try:
        import wikipedia
        speak(f"Searching for {term}.")
        webbrowser.open(f"https://www.google.com/search?q={term.replace(' ', '+')}")
        try:
            summary = wikipedia.summary(term, sentences=2)
            speak(summary)
            return summary
        except Exception:
            return f"Opened Google search for {term}."
    except ImportError:
        webbrowser.open(f"https://www.google.com/search?q={term.replace(' ', '+')}")
        return f"Opened Google for {term}."


def _search_wikipedia(q: str) -> str:
    term = re.sub(r"(jarvis|wikipedia|search|look up)", "", q).strip()
    try:
        import wikipedia
        speak(f"Looking up {term} on Wikipedia.")
        result = wikipedia.summary(term, sentences=3)
        speak(result)
        return result
    except Exception:
        response = f"Couldn't find that on Wikipedia."
        speak(response)
        return response


def _get_weather(q: str) -> str:
    if not WEATHER_API_KEY:
        return "Weather API key not set. Please add it to your .env file."
    try:
        import requests
        # Extract location from query
        words = q.lower().split()
        location = CITY  # default
        if "in" in words:
            idx = words.index("in")
            if idx + 1 < len(words):
                location = words[idx + 1]

        url = (f"http://api.weatherapi.com/v1/current.json"
               f"?key={WEATHER_API_KEY}&q={location}&aqi=no")
        data = requests.get(url, timeout=5).json()

        if "error" in data:
            return f"Couldn't get weather for {location}."

        city      = data["location"]["name"]
        temp_c    = data["current"]["temp_c"]
        condition = data["current"]["condition"]["text"]
        feels    = data["current"]["feelslike_c"]
        humidity  = data["current"]["humidity"]
        wind      = data["current"]["wind_kph"]

        response = (f"It's {temp_c}°C in {city} right now with {condition.lower()}. "
                    f"Feels like {feels}°C. Humidity is {humidity}%, "
                    f"wind at {wind} kilometres per hour.")
        speak(response)
        return response
    except Exception as e:
        response = "Sorry, I couldn't fetch the weather right now."
        speak(response)
        return response


def _get_news(q: str):
    if not GNEWS_API_KEY:
        speak("News API key not configured.")
        return
    try:
        import requests
        speak("Which category? Business, technology, sports, health, or entertainment?")
        category = take_command(timeout=5).lower()
        categories = ["business", "technology", "sports", "health", "entertainment", "science", "world"]
        cat = next((c for c in categories if c in category), "world")

        url = (f"https://gnews.io/api/v4/top-headlines"
               f"?topic={cat}&lang=en&apikey={GNEWS_API_KEY}&max=5")
        data = requests.get(url, timeout=5).json()
        articles = data.get("articles", [])

        if not articles:
            speak("No news found for that category.")
            return

        speak(f"Here are the top {cat} headlines.")
        for i, article in enumerate(articles[:5], 1):
            title = article.get("title", "")
            if title:
                speak(f"{i}. {title}")
    except Exception as e:
        speak("I couldn't fetch the news right now.")


def _calculate(q: str) -> str:
    expr = re.sub(r"(jarvis|calculate|what is|compute)", "", q).strip()
    expr = (expr.replace("plus", "+").replace("minus", "-")
                .replace("times", "*").replace("multiplied by", "*")
                .replace("divided by", "/").replace("x", "*"))
    if WOLFRAM_API_KEY:
        try:
            import wolframalpha
            client = wolframalpha.Client(WOLFRAM_API_KEY)
            res = client.query(expr)
            answer = next(res.results).text
            response = f"The answer is {answer}."
            speak(response)
            return response
        except Exception:
            pass
    # Fallback: Python eval (safe-ish for math)
    try:
        result = eval(expr, {"__builtins__": {}}, {})
        response = f"The answer is {result}."
        speak(response)
        return response
    except Exception:
        response = "I couldn't calculate that."
        speak(response)
        return response


def _translate(q: str) -> str:
    text = re.sub(r"(jarvis|translate|translation of)", "", q).strip()
    if not text:
        speak("What should I translate?")
        text = take_command()
    speak("Which language? For example: Hindi, Telugu, Spanish, French...")
    lang_input = take_command(timeout=6).lower()

    lang_map = {
        "hindi": "hi", "telugu": "te", "tamil": "ta", "kannada": "kn",
        "spanish": "es", "french": "fr", "german": "de", "japanese": "ja",
        "chinese": "zh", "arabic": "ar", "portuguese": "pt", "russian": "ru",
        "korean": "ko", "italian": "it", "bengali": "bn", "urdu": "ur"
    }
    lang_code = next((v for k, v in lang_map.items() if k in lang_input), "hi")

    try:
        from googletrans import Translator
        translator = Translator()
        result = translator.translate(text, dest=lang_code)
        translated = result.text
        speak(f"Here is the translation: {translated}")
        from gtts import gTTS
        from playsound import playsound
        tts = gTTS(text=translated, lang=lang_code, slow=False)
        tts.save("_temp_translate.mp3")
        threading.Thread(target=lambda: (playsound("_temp_translate.mp3"),
                         os.remove("_temp_translate.mp3")), daemon=True).start()
        return translated
    except Exception as e:
        speak("Translation failed.")
        return "Translation failed."


def _send_whatsapp():
    try:
        speak("Who should I message?")
        from voice_engine import take_command as tc
        whom = tc(timeout=5).lower()
        if "cancel" in whom:
            speak("Cancelled.")
            return
        speak("What's the message?")
        message = tc(timeout=8).lower()
        import pyautogui, time
        # Open WhatsApp
        open_app("whatsapp")
        time.sleep(3)
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.5)
        pyautogui.write(whom, interval=0.07)
        time.sleep(1.5)
        pyautogui.press("down")
        time.sleep(0.5)
        pyautogui.press("enter")
        time.sleep(0.5)
        pyautogui.write(message, interval=0.05)
        pyautogui.press("enter")
        speak(f"Message sent to {whom}.")
    except Exception as e:
        speak("I couldn't send that message.")


def _play_spotify(q: str) -> str:
    import pyautogui, time
    if "next" in q:
        pyautogui.hotkey("ctrl", "right")
        speak("Next track.")
        return "Next track."
    if "previous" in q or "back" in q:
        pyautogui.hotkey("ctrl", "left")
        speak("Previous track.")
        return "Previous track."
    open_app("spotify")
    time.sleep(3)
    pyautogui.press("space")
    speak("Resuming Spotify.")
    return "Playing Spotify."


def _trigger_n8n(q: str) -> str:
    """Trigger an n8n workflow via webhook."""
    try:
        import requests
        payload = {"query": q, "source": "jarvis", "user": USER_NAME,
                   "timestamp": datetime.datetime.now().isoformat()}
        resp = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=5)
        if resp.status_code == 200:
            response = "Automation triggered successfully."
        else:
            response = f"Automation returned status {resp.status_code}."
        speak(response)
        return response
    except Exception:
        response = "Couldn't reach the automation server."
        speak(response)
        return response


def _run_speed_test():
    result = internet_speed()
    speak(result)


def youtube_theater_mode():
    import pyautogui
    pyautogui.press("t")
    return "Theater mode toggled."
