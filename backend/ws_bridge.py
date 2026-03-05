"""
ws_bridge.py — WebSocket Server: HTML UI ↔ Python Backend
Run this to start JARVIS with the web UI
"""

import asyncio
import json
import threading
import websockets
import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import WS_HOST, WS_PORT, USER_NAME, ASSISTANT_NAME
from voice_engine import speak
from command_router import route
from memory import load_memory, save_memory, add_conversation_turn
from reminder_daemon import start_reminder_daemon

connected_clients = set()
_speak_lock = threading.Lock()


def _speak_safe(text: str):
    with _speak_lock:
        speak(text)


async def handler(websocket):
    connected_clients.add(websocket)
    print(f"[WS] Client connected. Total: {len(connected_clients)}")

    # Send welcome status
    await _send(websocket, {"type": "status", "text": "connected"})
    await _send(websocket, {"type": "info", "name": ASSISTANT_NAME, "user": USER_NAME})

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type", "")

                if msg_type == "activate":
                    print("[JARVIS] Activated")
                    await _send(websocket, {"type": "status", "text": "listening"})

                elif msg_type == "deactivate":
                    print("[JARVIS] Standby")
                    await _send(websocket, {"type": "status", "text": "standby"})

                elif msg_type == "query":
                    query = data.get("text", "").strip()
                    if query:
                        print(f"[USER] {query}")
                        await _send(websocket, {"type": "status", "text": "processing"})

                        loop = asyncio.get_event_loop()

                        # Route command in thread
                        response = await loop.run_in_executor(None, _handle_query, query)

                        if response and response not in ("__SLEEP__", None):
                            # Send response back to UI
                            await _send(websocket, {
                                "type": "response",
                                "text": response,
                                "timestamp": datetime.datetime.now().strftime("%H:%M")
                            })
                            # Speak in background
                            # (route() already spoke, so we don't double-speak)

                        if response == "__SLEEP__":
                            await _send(websocket, {"type": "status", "text": "standby"})
                        else:
                            await _send(websocket, {"type": "status", "text": "listening"})

                elif msg_type == "memory_request":
                    from memory import summarize_memory
                    summary = summarize_memory()
                    await _send(websocket, {"type": "memory", "text": summary})

                elif msg_type == "ping":
                    await _send(websocket, {"type": "pong"})

            except json.JSONDecodeError:
                pass
            except Exception as e:
                print(f"[WS Handler Error]: {e}")

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.discard(websocket)
        print(f"[WS] Client disconnected. Total: {len(connected_clients)}")


def _handle_query(query: str) -> str:
    """Route query and return response string."""
    try:
        response = route(query)
        return response
    except Exception as e:
        print(f"[Route Error]: {e}")
        err_msg = f"I ran into a problem with that, {USER_NAME}. Let me try again."
        speak(err_msg)
        return err_msg


async def _send(websocket, data: dict):
    try:
        await websocket.send(json.dumps(data))
    except Exception:
        pass


async def broadcast(data: dict):
    """Send to all connected clients."""
    if connected_clients:
        await asyncio.gather(
            *[_send(ws, data) for ws in connected_clients],
            return_exceptions=True
        )


async def main():
    # Start background services
    start_reminder_daemon()
    print("=" * 55)
    print(f"  {ASSISTANT_NAME.upper()} — WebSocket Server")
    print(f"  ws://{WS_HOST}:{WS_PORT}")
    print(f"  Open jarvis_ui.html in Chrome")
    print(f"  User: {USER_NAME}")
    print("=" * 55)

    # Greeting on startup
    from GreetMe import greet_startup
    threading.Thread(target=greet_startup, daemon=True).start()

    async with websockets.serve(handler, WS_HOST, WS_PORT,
                                ping_interval=20, ping_timeout=10):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
