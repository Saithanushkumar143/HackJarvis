"""
Run this in your VS Code terminal to diagnose the real issue:
    python check_imports.py
"""

import sys
print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")
print()

tests = [
    ("google.genai (new SDK)",        "from google import genai; print('  client =', genai.Client)"),
    ("google.generativeai (old SDK)", "import google.generativeai as g; print('  module =', g)"),
    ("requests (REST fallback)",      "import requests; print('  OK')"),
    ("pyttsx3",                       "import pyttsx3; print('  OK')"),
    ("speech_recognition",            "import speech_recognition; print('  OK')"),
    ("pyautogui",                     "import pyautogui; print('  OK')"),
    ("websockets",                    "import websockets; print('  OK')"),
    ("pycaw (volume)",                "from pycaw.pycaw import AudioUtilities; print('  OK')"),
]

print("=" * 50)
for name, code in tests:
    try:
        exec(code)
        print(f"[OK]   {name}")
    except Exception as e:
        print(f"[FAIL] {name}")
        print(f"       Error: {e}")

print()
print("=" * 50)
print("Google packages installed:")
import subprocess
result = subprocess.run(["pip", "list"], capture_output=True, text=True)
for line in result.stdout.splitlines():
    if "google" in line.lower():
        print(" ", line)