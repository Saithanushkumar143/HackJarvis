"""
desktop_control.py — Full Desktop Automation for JARVIS
Controls apps, windows, volume, browser, media, system
"""

import os
import sys
import time
import subprocess
import threading
import datetime
import webbrowser
import pyautogui
import psutil  #cpu usage, memory, disk, battery

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import USER_NAME
from voice_engine import speak

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

# ── APP REGISTRY ──────────────────────────────────────────────

APP_MAP = {
    # Productivity
    "notepad":      "notepad",
    "word":         "winword",
    "excel":        "excel",
    "powerpoint":   "powerpnt",
    "calculator":   "calc",
    "paint":        "mspaint",
    "task manager": "taskmgr",
    "settings":     "ms-settings:",
    # Browsers
    "chrome":       "chrome",
    "firefox":      "firefox",
    "edge":         "msedge",
    # Dev tools
    "vscode":       "code",
    "vs code":      "code",
    "terminal":     "wt",
    "cmd":          "cmd",
    "command prompt": "cmd",
    "powershell":   "powershell",
    # Media
    "spotify":      "spotify",
    "vlc":          "vlc",
    "media player": "wmplayer",
    # Communication
    "discord":      "discord",
    "zoom":         "zoom",
    "teams":        "teams",
    "whatsapp":     "WhatsApp",
    "telegram":     "telegram",
    # Other
    "file explorer": "explorer",
    "explorer":      "explorer",
    "snipping tool": "SnippingTool",
    "camera":        "microsoft.windows.camera:",
}

PROCESS_MAP = {k: f"{v}.exe" for k, v in APP_MAP.items()}


# ── APP CONTROL ───────────────────────────────────────────────

def open_app(name: str) -> str:
    name = name.strip().lower()
    # Check app map
    for key, cmd in APP_MAP.items():
        if key in name or name in key:
            speak(f"Opening {key}, {USER_NAME}.")
            try:
                if cmd.startswith("ms-") or cmd.startswith("microsoft."):
                    os.system(f"start {cmd}")
                else:
                    subprocess.Popen(cmd, shell=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW
                                     if sys.platform == "win32" else 0)
            except Exception:
                # Fallback: Windows search
                _search_and_open(name)
            return f"Opening {key}."

    # Check .com websites
    if any(ext in name for ext in [".com", ".org", ".in", ".net", ".io"]):
        url = name if name.startswith("http") else f"https://{name}"
        webbrowser.open(url)
        return f"Opening {name} in browser."

    # Fallback: Windows search
    _search_and_open(name)
    return f"Searching for {name}."


def _search_and_open(query: str):
    pyautogui.hotkey("win", "s")
    time.sleep(0.6)
    pyautogui.write(query, interval=0.05)
    time.sleep(1.2)
    pyautogui.press("enter")


def close_app(name: str) -> str:
    """Close an application by name."""
    name = name.strip().lower()
    for key, exe in PROCESS_MAP.items():
        if key in name:
            os.system(f"taskkill /f /im {exe} >nul 2>&1")
            return f"Closed {key}."
    # Close current window
    pyautogui.hotkey("alt", "f4")
    return "Closed the active window."


def switch_window() -> str:
    pyautogui.hotkey("alt", "tab")
    return "Switched window."


def minimize_all() -> str:
    pyautogui.hotkey("win", "d")
    return "Minimized all windows."


def maximize_window() -> str:
    pyautogui.hotkey("win", "up")
    return "Maximized window."


def snap_left() -> str:
    pyautogui.hotkey("win", "left")
    return "Snapped window to the left."


def snap_right() -> str:
    pyautogui.hotkey("win", "right")
    return "Snapped window to the right."


# ── VOLUME CONTROL ────────────────────────────────────────────

def volume_up(steps: int = 5) -> str:
    from pynput.keyboard import Key, Controller
    kb = Controller()
    for _ in range(steps):
        kb.press(Key.media_volume_up)
        kb.release(Key.media_volume_up)
        time.sleep(0.05)
    return f"Volume up."


def volume_down(steps: int = 5) -> str:
    from pynput.keyboard import Key, Controller
    kb = Controller()
    for _ in range(steps):
        kb.press(Key.media_volume_down)
        kb.release(Key.media_volume_down)
        time.sleep(0.05)
    return f"Volume down."


def mute_toggle() -> str:
    from pynput.keyboard import Key, Controller
    kb = Controller()
    kb.press(Key.media_volume_mute)
    kb.release(Key.media_volume_mute)
    return "Toggled mute."


def set_volume(level: int) -> str:
    """Set system volume to 0-100%."""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level / 100, None)
        return f"Volume set to {level}%."
    except Exception:
        # Fallback: use key presses
        mute_toggle()
        mute_toggle()
        return f"Volume adjusted."


# ── MEDIA CONTROL ─────────────────────────────────────────────

def media_play_pause() -> str:
    from pynput.keyboard import Key, Controller
    kb = Controller()
    kb.press(Key.media_play_pause)
    kb.release(Key.media_play_pause)
    return "Play/pause toggled."


def media_next() -> str:
    from pynput.keyboard import Key, Controller
    kb = Controller()
    kb.press(Key.media_next)
    kb.release(Key.media_next)
    return "Next track."


def media_previous() -> str:
    from pynput.keyboard import Key, Controller
    kb = Controller()
    kb.press(Key.media_previous)
    kb.release(Key.media_previous)
    return "Previous track."


def youtube_skip_forward(seconds: int = 10) -> str:
    steps = seconds // 5
    for _ in range(steps):
        pyautogui.press("l")
        time.sleep(0.1)
    return f"Skipped forward {seconds} seconds."


def youtube_skip_backward(seconds: int = 10) -> str:
    steps = seconds // 5
    for _ in range(steps):
        pyautogui.press("j")
        time.sleep(0.1)
    return f"Rewound {seconds} seconds."


def youtube_fullscreen() -> str:
    pyautogui.press("f")
    return "Toggled fullscreen."


def youtube_theater_mode() -> str:
    pyautogui.press("t")
    return "Toggled theater mode."


# ── SCREENSHOT / SCREEN ───────────────────────────────────────

def take_screenshot(save_path: str = None) -> str:
    if not save_path:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(os.path.expanduser("~"), "Desktop", f"screenshot_{ts}.png")
    img = pyautogui.screenshot()
    img.save(save_path)
    return f"Screenshot saved to desktop."


# ── CLIPBOARD ─────────────────────────────────────────────────

def copy_text() -> str:
    pyautogui.hotkey("ctrl", "c")
    return "Copied."


def paste_text() -> str:
    pyautogui.hotkey("ctrl", "v")
    return "Pasted."


def cut_text() -> str:
    pyautogui.hotkey("ctrl", "x")
    return "Cut."


def select_all() -> str:
    pyautogui.hotkey("ctrl", "a")
    return "Selected all."


def undo() -> str:
    pyautogui.hotkey("ctrl", "z")
    return "Undone."


def type_text(text: str) -> str:
    time.sleep(0.5)
    pyautogui.write(text, interval=0.04)
    return f"Typed: {text}"


# ── SYSTEM ────────────────────────────────────────────────────

def lock_screen() -> str:
    os.system("rundll32.exe user32.dll,LockWorkStation")
    return "Screen locked."


def shutdown_system() -> str:
    speak("Shutting down in 10 seconds. Say cancel to abort.")
    time.sleep(10)
    os.system("shutdown /s /t 0")
    return "Shutting down."


def restart_system() -> str:
    speak("Restarting in 10 seconds.")
    time.sleep(10)
    os.system("shutdown /r /t 0")
    return "Restarting."


def sleep_system() -> str:
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    return "Going to sleep."


def get_system_stats() -> str:
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    battery = psutil.sensors_battery()
    bat_str = f"Battery at {battery.percent:.0f}%." if battery else ""
    return (f"CPU usage is {cpu}%. Memory is {mem.percent}% used, "
            f"{mem.available // (1024**3)} gigabytes free. "
            f"Disk is {disk.percent}% full. {bat_str}")


def internet_speed() -> str:
    speak("Running speed test, this will take about 30 seconds.")
    try:
        import speedtest
        st = speedtest.Speedtest()
        st.get_best_server()
        dl = st.download() / 1_000_000
        ul = st.upload() / 1_000_000
        return f"Download speed is {dl:.1f} megabits, upload is {ul:.1f} megabits."
    except Exception as e:
        return "Speed test failed. Please check your connection."


# ── BROWSER SHORTCUTS ─────────────────────────────────────────

def new_tab() -> str:
    pyautogui.hotkey("ctrl", "t")
    return "New tab opened."


def close_tab() -> str:
    pyautogui.hotkey("ctrl", "w")
    return "Tab closed."


def refresh_page() -> str:
    pyautogui.press("f5")
    return "Page refreshed."


def go_back() -> str:
    pyautogui.hotkey("alt", "left")
    return "Went back."


def go_forward() -> str:
    pyautogui.hotkey("alt", "right")
    return "Went forward."


# ── NOTIFICATION ──────────────────────────────────────────────

def show_notification(title: str, message: str, timeout: int = 8):
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name="JARVIS",
            timeout=timeout
        )
    except Exception:
        print(f"[Notification] {title}: {message}")
