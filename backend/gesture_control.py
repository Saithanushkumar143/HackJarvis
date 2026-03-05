"""
gesture_control.py — Iron Man-style Hand Gesture Controller
Uses MediaPipe to detect hand gestures and control the desktop
Run as a separate thread from main JARVIS
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import threading
import pyautogui
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (GESTURE_PINCH_CLOSE, GESTURE_PINCH_OPEN,
                    GESTURE_SWIPE_THRESH, GESTURE_FIST_THRESH)
from desktop_control import volume_up, volume_down, media_play_pause, switch_window
from voice_engine import speak_async

pyautogui.FAILSAFE = False

# ── LANDMARK INDICES ──────────────────────────────────────────
WRIST         = 0
THUMB_TIP     = 4
INDEX_TIP     = 8
MIDDLE_TIP    = 12
RING_TIP      = 16
PINKY_TIP     = 20
INDEX_MCP     = 5
MIDDLE_MCP    = 9
RING_MCP      = 13
PINKY_MCP     = 17


class GestureController:
    """
    Gesture → Action map:
    ─────────────────────────────────────────────────────
    👌 Pinch (thumb+index)        → Volume down / scroll down
    🖐 Open palm                  → Volume up / scroll up
    ✊ Fist                        → Play/Pause
    👈 Swipe left (all fingers)   → Previous / Switch window left
    👉 Swipe right (all fingers)  → Next / Switch window right
    ☝ One finger up              → Scroll up
    ✌ Two fingers up             → Scroll down
    🤚 Raise hand (stop)         → Freeze / Stop gesture mode
    🖐→🤜 Push forward           → Minimize all windows
    ─────────────────────────────────────────────────────
    """

    def __init__(self):
        self.mp_hands   = mp.solutions.hands
        self.mp_draw    = mp.solutions.drawing_utils
        self.hands      = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.75,
            min_tracking_confidence=0.65
        )
        self.cap = None
        self.running = False
        self._thread = None

        # State tracking
        self._last_gesture   = None
        self._last_action_t  = 0
        self._debounce       = 0.6   # seconds between actions
        self._prev_wrist_x   = None
        self._swipe_buffer   = []
        self._swipe_window   = 0.4   # seconds

        # Gesture overlay
        self._gesture_label  = ""
        self._label_timer    = 0

    # ── PUBLIC API ────────────────────────────────────────────

    def start(self):
        if self.running:
            return
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("[Gesture] Camera not available.")
            return
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        speak_async("Gesture control activated. I'm watching your hands.")
        print("[Gesture] Started.")

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        speak_async("Gesture control deactivated.")
        print("[Gesture] Stopped.")

    def is_running(self):
        return self.running

    # ── MAIN LOOP ─────────────────────────────────────────────

    def _loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)

            if results.multi_hand_landmarks:
                for hand_lm in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(
                        frame, hand_lm, self.mp_hands.HAND_CONNECTIONS,
                        self.mp_draw.DrawingSpec(color=(0, 212, 255), thickness=2, circle_radius=3),
                        self.mp_draw.DrawingSpec(color=(255, 170, 0), thickness=2)
                    )
                    self._detect_and_act(hand_lm, frame.shape)

            # Overlay
            self._draw_overlay(frame)
            cv2.imshow("JARVIS — Gesture Control (Q to quit)", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        self.running = False
        self.cap.release()
        cv2.destroyAllWindows()

    # ── GESTURE DETECTION ─────────────────────────────────────

    def _lm(self, hand, idx):
        """Return (x, y) normalized for a landmark index."""
        pt = hand.landmark[idx]
        return pt.x, pt.y

    def _dist(self, p1, p2):
        return np.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def _fingers_up(self, hand) -> list:
        """Return list of booleans: [thumb, index, middle, ring, pinky]."""
        tips = [THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]
        pips = [3,         6,          10,          14,       18]
        result = []
        for tip, pip in zip(tips, pips):
            tip_y = hand.landmark[tip].y
            pip_y = hand.landmark[pip].y
            result.append(tip_y < pip_y)  # up = smaller y
        return result

    def _detect_and_act(self, hand, shape):
        now = time.time()
        fingers = self._fingers_up(hand)

        thumb_tip  = self._lm(hand, THUMB_TIP)
        index_tip  = self._lm(hand, INDEX_TIP)
        middle_tip = self._lm(hand, MIDDLE_TIP)
        wrist      = self._lm(hand, WRIST)

        pinch_dist = self._dist(thumb_tip, index_tip)
        all_up     = all(fingers)
        all_down   = not any(fingers[1:])   # ignore thumb
        one_up     = fingers[1] and not any(fingers[2:])
        two_up     = fingers[1] and fingers[2] and not any(fingers[3:])
        peace      = fingers[1] and fingers[2] and not fingers[3] and not fingers[4]
        ok_sign    = pinch_dist < GESTURE_PINCH_CLOSE

        # ── SWIPE DETECTION ───────────────────────────────────
        wx = wrist[0]
        if self._prev_wrist_x is not None and all_up:
            delta = wx - self._prev_wrist_x
            self._swipe_buffer.append((now, delta))
            self._swipe_buffer = [(t, d) for t, d in self._swipe_buffer
                                  if now - t < self._swipe_window]
            total_delta = sum(d for _, d in self._swipe_buffer)
            if abs(total_delta) > GESTURE_SWIPE_THRESH:
                if total_delta > 0 and self._can_act(now):
                    self._fire("Swipe Right → Next", media_next_or_switch_right)
                    self._swipe_buffer.clear()
                elif total_delta < 0 and self._can_act(now):
                    self._fire("Swipe Left → Previous", media_prev_or_switch_left)
                    self._swipe_buffer.clear()
        self._prev_wrist_x = wx

        # ── FIST → Play/Pause ─────────────────────────────────
        if all_down and self._can_act(now):
            self._fire("✊ Fist → Play/Pause", media_play_pause)

        # ── OPEN PALM → Volume Up ─────────────────────────────
        elif all_up and pinch_dist > GESTURE_PINCH_OPEN and self._can_act(now):
            self._fire("🖐 Open Palm → Volume Up", volume_up)

        # ── PINCH → Volume Down ───────────────────────────────
        elif ok_sign and self._can_act(now):
            self._fire("👌 Pinch → Volume Down", volume_down)

        # ── ONE FINGER UP → Scroll Up ─────────────────────────
        elif one_up and self._can_act(now, 0.15):
            pyautogui.scroll(3)
            self._gesture_label = "☝ Scroll Up"
            self._label_timer = time.time()

        # ── TWO FINGERS UP → Scroll Down ──────────────────────
        elif two_up and not fingers[0] and self._can_act(now, 0.15):
            pyautogui.scroll(-3)
            self._gesture_label = "✌ Scroll Down"
            self._label_timer = time.time()

    def _can_act(self, now, debounce=None) -> bool:
        d = debounce or self._debounce
        if now - self._last_action_t > d:
            self._last_action_t = now
            return True
        return False

    def _fire(self, label: str, func):
        self._gesture_label = label
        self._label_timer = time.time()
        print(f"[Gesture] {label}")
        threading.Thread(target=func, daemon=True).start()

    def _draw_overlay(self, frame):
        h, w = frame.shape[:2]
        # HUD border
        cv2.rectangle(frame, (0, 0), (w-1, h-1), (0, 212, 255), 2)
        # Title
        cv2.putText(frame, "JARVIS GESTURE HUD", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 212, 255), 1)
        # Gesture label
        if time.time() - self._label_timer < 1.5:
            cv2.putText(frame, self._gesture_label, (10, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 170, 0), 2)
        # Gesture guide
        guide = ["Fist=Pause", "Open=VolUp", "Pinch=VolDown",
                 "1 Finger=Scroll Up", "2 Fingers=Scroll Down",
                 "Swipe=Next/Prev"]
        for i, g in enumerate(guide):
            cv2.putText(frame, g, (w - 200, 25 + i * 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 180, 200), 1)


def media_next_or_switch_right():
    from desktop_control import media_next
    media_next()


def media_prev_or_switch_left():
    from desktop_control import media_previous
    media_previous()


# ── Singleton ─────────────────────────────────────────────────
_gesture_controller = None

def get_gesture_controller() -> GestureController:
    global _gesture_controller
    if _gesture_controller is None:
        _gesture_controller = GestureController()
    return _gesture_controller