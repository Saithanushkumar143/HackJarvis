"""
reminder_daemon.py — Background Reminder & Mood Check System
Runs as a daemon thread, fires reminders at the right time
"""

import threading
import datetime
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import USER_NAME
from memory import load_memory, save_memory, get_pending_reminders, mark_reminder_done
from voice_engine import speak
from desktop_control import show_notification


class ReminderDaemon:
    def __init__(self, check_interval: int = 30):
        self.interval = check_interval
        self.running = False
        self._thread = None
        self._mood_check_interval = 3600  # 1 hour
        self._last_mood_check = 0
        self._last_birthday_check = 0

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("[Reminder Daemon] Started.")

    def stop(self):
        self.running = False

    def _loop(self):
        while self.running:
            try:
                self._check_reminders()
                self._check_birthday()
                self._check_scheduled_tasks()
            except Exception as e:
                print(f"[Reminder Daemon Error]: {e}")
            time.sleep(self.interval)

    def _check_reminders(self):
        reminders = get_pending_reminders()
        for r in reminders:
            text = r.get("text", "")
            show_notification("⏰ JARVIS Reminder", text)
            speak(f"Reminder, {USER_NAME}: {text}")
            mark_reminder_done(text)

    def _check_birthday(self):
        now = time.time()
        if now - self._last_birthday_check < 86400:  # once a day
            return
        self._last_birthday_check = now
        memory = load_memory()
        birthday = memory.get("birthday")
        if birthday:
            try:
                today = datetime.date.today()
                bday = datetime.date.fromisoformat(birthday)
                if bday.month == today.month and bday.day == today.day:
                    speak(f"Happy birthday, {USER_NAME}! Wishing you an amazing day!")
                    show_notification("🎂 Happy Birthday!", f"Happy Birthday, {USER_NAME}!")
            except Exception:
                pass

    def _check_scheduled_tasks(self):
        """Morning briefing at 8 AM and evening summary at 7 PM."""
        now = datetime.datetime.now()
        memory = load_memory()
        tasks = [t for t in memory.get("tasks", []) if not t.get("done")]

        # Morning briefing
        if now.hour == 8 and now.minute < 1:
            if tasks:
                summary = f"Good morning, {USER_NAME}. You have {len(tasks)} tasks for today."
                speak(summary)
                show_notification("📋 Morning Briefing", f"{len(tasks)} tasks today")

        # Evening wind-down
        if now.hour == 19 and now.minute < 1:
            pending = [t for t in tasks if not t.get("done")]
            done_count = len(tasks) - len(pending)
            summary = (f"Good evening, {USER_NAME}. You completed {done_count} tasks today "
                       f"and have {len(pending)} still pending.")
            speak(summary)


_daemon = None

def start_reminder_daemon():
    global _daemon
    _daemon = ReminderDaemon(check_interval=30)
    _daemon.start()
    return _daemon

def stop_reminder_daemon():
    global _daemon
    if _daemon:
        _daemon.stop()