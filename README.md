# 🤖 J.A.R.V.I.S — Desktop AI Assistant
### Just A Rather Very Intelligent System

> *Your best friend in the computer. Powered by Gemini AI, MediaPipe gestures, and pure Python.*

---

## 🌟 Features

### 🧠 AI Brain
- **Gemini 2.0 Flash** — Fast, smart, conversational AI
- **Persistent Memory** — Remembers your name, preferences, facts, mood
- **Offline Mode** — Works without internet for local commands
- **Personality** — Witty, warm, proactive. Not a search engine — a companion

### 🎙️ Voice Control
- Wake word detection (`"Jarvis"`)
- Google STT (online) + Sphinx fallback (offline)
- Natural language understanding — talk normally
- Speaks back with a natural voice (SAPI5/pyttsx3)

### 🖥️ Desktop Control
| Command | Action |
|---------|--------|
| "Open Chrome" | Launches app |
| "Volume up/down" | Adjusts system volume |
| "Next/Previous song" | Media control |
| "Take a screenshot" | Saves to Desktop |
| "Switch app" | Alt+Tab |
| "Lock screen" | Windows lock |
| "System stats" | CPU, RAM, Battery |
| "Type [text]" | Types text anywhere |
| "Copy/Paste/Cut" | Clipboard ops |
| "Snap left/right" | Window snapping |
| "Shutdown/Restart" | System power |

### 🖐️ Iron Man Gestures (Camera Required)
| Gesture | Action |
|---------|--------|
| ✊ Fist | Play/Pause |
| 🖐 Open Palm | Volume Up |
| 👌 Pinch | Volume Down |
| ☝ One Finger | Scroll Up |
| ✌ Two Fingers | Scroll Down |
| 👉 Swipe Right | Next Track |
| 👈 Swipe Left | Previous Track |

### 💬 Conversation & Memory
- "Remember that my project deadline is Friday"
- "What do you remember about me?"
- "Remind me to call mom in 30 minutes"
- "Add task: review the report"
- "Show my pending tasks"
- "Clear your memory"

### 🌐 Web & Search
- "Google search: latest AI news"
- "YouTube: play lofi hip hop"
- "Wikipedia: what is quantum computing"
- "Weather in Mumbai"
- "Latest technology news"
- "Translate hello to Telugu"

### 📱 Communication
- "Send WhatsApp message to Mom"
- "Check my emails" (IMAP)

### ⚡ n8n Automation (Optional)
Connect JARVIS to 400+ apps via n8n:
1. Morning briefing (Weather + News + Calendar)
2. Smart home control (Home Assistant)
3. Mood-based Spotify playlists
4. Voice notes → Notion/Google Docs
5. GitHub alerts
6. Google Calendar sync
7. Team messages read-aloud

---

## 🚀 Quick Start

### Requirements
- Windows 10/11
- Python 3.10+
- Chrome browser (for UI mode)
- Microphone
- Webcam (optional, for gestures)

### Installation

```bash
# 1. Clone or download this project
cd JARVIS

# 2. Run the startup script
start_jarvis.bat

# OR manually:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure API keys
copy .env.example .env
notepad .env   # Add your keys
```

### API Keys Needed
| Key | Where to Get | Required? |
|-----|-------------|-----------|
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) | ✅ Yes (free) |
| `WEATHER_API_KEY` | [weatherapi.com](https://weatherapi.com) | Optional |
| `GNEWS_API_KEY` | [gnews.io](https://gnews.io) | Optional |
| `WOLFRAM_API_KEY` | [wolframalpha.com](https://products.wolframalpha.com/api) | Optional |

### Running JARVIS

**GUI Mode (Recommended)**
```bash
python backend/ws_bridge.py
# Then open: frontend/jarvis_ui.html in Chrome
```

**Voice Only Mode**
```bash
python main.py
```

**Or double-click:**
```
start_jarvis.bat
```

---

## 🗣️ Voice Commands

### Wake & Sleep
```
"Jarvis"             → Wake up
"Go to sleep"        → Standby mode  
"Quiet"              → Standby mode
```

### Apps
```
"Open Chrome"
"Open Spotify"
"Open VS Code"
"Close Excel"
"Launch WhatsApp"
```

### Media
```
"Play/Pause"
"Next song" / "Previous song"
"Volume up by 10" / "Volume down"
"Mute" / "Unmute"
"Skip forward 30 seconds"
"Rewind 10 seconds"
"Fullscreen"
```

### System
```
"System diagnostics"
"Take a screenshot"
"Lock the screen"
"Check internet speed"
"Shutdown" / "Restart"
"Switch app"
"Minimize all"
```

### AI Conversation
```
"How am I doing today?"
"Tell me a joke"
"What's the meaning of life?"
"I'm feeling stressed"
"Help me think through this problem"
```

### Gestures (say "Gesture control on")
- Wave your hand in front of webcam
- See the gesture HUD window
- Press Q to close gesture window

---

## 🔧 Configuration (.env)

```env
GEMINI_API_KEY=your_key_here
WEATHER_API_KEY=your_key_here
USER_NAME=YourName
ASSISTANT_NAME=Jarvis
WAKE_WORD=jarvis
CITY=YourCity
VOICE_INDEX=1          # 0=Male, 1=Female
SPEECH_RATE=170        # Words per minute
OFFLINE_FALLBACK=true  # Use offline mode when no internet
```

---

## 🤖 n8n Automation Setup

```bash
# Install n8n
npm install -g n8n

# Start n8n
n8n start

# Open: http://localhost:5678
# Import the workflow templates from backend/n8n_integration.py
```

**Suggested Automations:**
- `"Jarvis, morning briefing"` → Weather + News + Calendar summary
- `"Jarvis, save a note"` → Saves to Notion/Google Docs
- `"Jarvis, turn off lights"` → Home Assistant command
- `"Jarvis, play focus music"` → Mood-based Spotify

---

## 📁 Project Structure

```
JARVIS/
├── main.py                    # Voice-only entry point
├── start_jarvis.bat           # Windows launcher
├── requirements.txt
├── .env.example
│
├── backend/
│   ├── config.py              # All settings
│   ├── voice_engine.py        # TTS + STT
│   ├── ai_brain.py            # Gemini AI integration
│   ├── memory.py              # Persistent memory system
│   ├── command_router.py      # Voice → Action routing
│   ├── desktop_control.py     # Windows automation
│   ├── gesture_control.py     # MediaPipe hand gestures
│   ├── ws_bridge.py           # WebSocket server (UI bridge)
│   ├── reminder_daemon.py     # Background reminder thread
│   ├── GreetMe.py             # Smart greetings
│   └── n8n_integration.py     # n8n workflow automation
│
├── frontend/
│   └── jarvis_ui.html         # Iron Man HUD interface
│
├── memory/
│   └── jarvis_memory.json     # Persistent user memory
│
└── logs/
    └── jarvis.log
```

---

## 🛠️ Troubleshooting

**"No module named X"**
```bash
pip install -r requirements.txt
```

**Microphone not working**
- Check Windows Sound Settings → Input devices
- Allow microphone access for Python

**Gemini errors**
- Verify API key in `.env`
- Check: https://aistudio.google.com

**Gestures not working**
- Ensure webcam is connected
- Install: `pip install mediapipe opencv-python`
- Good lighting required

**WebSocket not connecting**
- Make sure `ws_bridge.py` is running
- Check firewall isn't blocking port 8765

---

## 🙏 Credits

Built by **Thanush Kumar** (Yegoti Sai Thanush Kumar)
- AI: Google Gemini 2.0
- Gestures: MediaPipe
- Voice: pyttsx3 + SpeechRecognition  
- UI: Custom Iron Man HUD

---

*"Sometimes you gotta run before you can walk." — Tony Stark*
