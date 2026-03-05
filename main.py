"""
main.py — JARVIS Main Entry Point (Voice-only mode)
For GUI mode, run: python backend/ws_bridge.py
Then open: frontend/jarvis_ui.html in Chrome
"""

import sys
import os
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from config import WAKE_WORD, USER_NAME, ASSISTANT_NAME
from voice_engine import speak, take_command, listen_for_wake_word
from command_router import route
from GreetMe import greet_startup, greet_wakeup
from reminder_daemon import start_reminder_daemon

# ─────────────────────────────────────────────────────────────
#  MODES
# ─────────────────────────────────────────────────────────────

MODE_SLEEP  = "SLEEP"    # Listening only for wake word
MODE_ACTIVE = "ACTIVE"   # Processing all commands
MODE_EXIT   = "EXIT"

SLEEP_PHRASES  = ["go to sleep", "quiet", "silent", "standby", "sleep mode"]
EXIT_PHRASES   = ["shut yourself down", "exit jarvis", "kill yourself", "goodbye forever"]
WAKEUP_PHRASES = ["wake up", "hey jarvis", "jarvis", "i need you", "i'm back", "hello jarvis"]


def in_list(query: str, phrases: list) -> bool:
    q = query.lower()
    return any(p in q for p in phrases)


# ─────────────────────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────────────────────

def main():
    print(f"""
╔══════════════════════════════════════════════╗
║  J.A.R.V.I.S — Desktop AI Assistant         ║
║  Version 2.0 — By Thanush Kumar              ║
╠══════════════════════════════════════════════╣
║  Say "{WAKE_WORD.upper()}" to wake up               ║
║  Say "go to sleep" to put me in standby     ║
║  For GUI mode: run ws_bridge.py              ║
╚══════════════════════════════════════════════╝
""")

    # Start background services
    start_reminder_daemon()

    # Startup greeting
    greet_startup()

    mode = MODE_ACTIVE  # Start in active mode

    while True:
        try:
            if mode == MODE_EXIT:
                speak(f"Shutting down {ASSISTANT_NAME}. Take care, {USER_NAME}.")
                sys.exit(0)

            elif mode == MODE_SLEEP:
                # Low-power mode: listen for wake word only
                print("[SLEEP] Listening for wake word...")
                query = take_command(timeout=4, phrase_limit=4)

                if query == "None":
                    continue

                if in_list(query, WAKEUP_PHRASES):
                    mode = MODE_ACTIVE
                    greet_wakeup()

            elif mode == MODE_ACTIVE:
                query = take_command(timeout=6, phrase_limit=15)

                if query == "None":
                    continue  # silence — just keep listening

                # Transition commands
                if in_list(query, EXIT_PHRASES):
                    mode = MODE_EXIT
                    continue

                if in_list(query, SLEEP_PHRASES):
                    mode = MODE_SLEEP
                    speak(f"Going to standby, {USER_NAME}. Say my name when you need me.")
                    continue

                # Route command
                response = route(query)

                if response == "__SLEEP__":
                    mode = MODE_SLEEP

        except KeyboardInterrupt:
            speak(f"Goodbye, {USER_NAME}.")
            sys.exit(0)
        except Exception as e:
            print(f"[Main Loop Error]: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
