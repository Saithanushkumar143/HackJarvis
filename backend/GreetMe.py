"""
GreetMe.py — Smart Greeting System
Greets based on time of day, mood history, pending reminders
"""

import datetime
import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import USER_NAME
from voice_engine import speak
from memory import load_memory, get_pending_reminders, get_pending_tasks


def greet_startup():
    """
    Full startup greeting with system status,
    pending tasks, and time-aware message.
    """
    memory = load_memory()
    name = memory.get("name") or USER_NAME
    hour = datetime.datetime.now().hour

    # Time-based greeting
    if 5 <= hour < 12:
        time_greeting = f"Good morning, {name}!"
        quip = random.choice([
            "Ready to seize the day?",
            "Hope you slept well.",
            "The early bird gets the worm. Let's get started.",
            "Coffee ready? Let's crush it today."
        ])
    elif 12 <= hour < 17:
        time_greeting = f"Good afternoon, {name}!"
        quip = random.choice([
            "Hope your morning went well.",
            "The day is half done — still plenty of time.",
            "Ready to continue?"
        ])
    elif 17 <= hour < 21:
        time_greeting = f"Good evening, {name}!"
        quip = random.choice([
            "Winding down or just getting started?",
            "How was your day?",
            "Evening. I'm here if you need anything."
        ])
    else:
        time_greeting = f"It's late, {name}."
        quip = random.choice([
            "You're burning the midnight oil again.",
            "Don't forget to rest. Even Tony Stark slept sometimes.",
            "Working late? I've got you."
        ])

    greeting = f"{time_greeting} {quip}"

    # Check mood history
    mood_history = memory.get("mood_history", [])
    if mood_history:
        last_mood = mood_history[-1].get("mood", "neutral")
        if last_mood == "negative":
            greeting += " I noticed you seemed a bit stressed last time. I hope you're feeling better."

    speak(greeting)

    # Pending reminders
    reminders = get_pending_reminders()
    if reminders:
        r_list = ", ".join(r["text"] for r in reminders[:2])
        speak(f"You have {len(reminders)} pending reminder{'s' if len(reminders) > 1 else ''}. Including: {r_list}.")

    # Pending tasks
    tasks = get_pending_tasks()
    if tasks:
        speak(f"You also have {len(tasks)} task{'s' if len(tasks) > 1 else ''} on your list.")

    # Total interactions milestone
    total = memory.get("total_interactions", 0)
    if total > 0 and total % 100 == 0:
        speak(f"By the way, this is our {total}th conversation. It's been a pleasure working with you.")


def greet_wakeup():
    """Brief greeting when Jarvis wakes from standby."""
    memory = load_memory()
    name = memory.get("name") or USER_NAME
    responses = [
        f"Yes, {name}?",
        f"Right here, {name}. What do you need?",
        f"At your service, {name}.",
        f"I'm listening, {name}.",
        f"Ready. What can I do for you?",
    ]
    speak(random.choice(responses))