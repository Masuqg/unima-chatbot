"""
AI Chatbot — internship starter project
========================================
Backend: Flask (Python). Frontend: static/index.html.

Two modes:
  1. AI MODE   — if the GROQ_API_KEY environment variable is set, messages are
                 answered by a real LLM through Groq's free, OpenAI-compatible API.
  2. DEMO MODE — without a key, a small built-in rule-based brain answers, so the
                 app always runs (great for demos and for understanding the flow).

The server is stateless: the browser sends the conversation history with every
request, and we prepend a "system prompt" that defines the bot's personality.
"""

import os
import re
import time
import json
import urllib.request
import urllib.error
from datetime import datetime

from flask import Flask, Response, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="")

# ---------------------------------------------------------------------------
# Configuration (everything is overridable with environment variables)
# ---------------------------------------------------------------------------
API_KEY = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
API_URL = os.environ.get("API_URL", "https://api.groq.com/openai/v1/chat/completions")
MODEL = os.environ.get("MODEL", "llama-3.3-70b-versatile")  # free on Groq

# The system prompt controls the bot's personality. CUSTOMISE THIS — it is the
# easiest way to turn this generic bot into e.g. a company FAQ/support bot.
SYSTEM_PROMPT = os.environ.get(
    "SYSTEM_PROMPT",
    "You are Unima, a friendly and concise assistant built as an internship "
    "project. Answer in short, clear paragraphs. If you don't know something, "
    "say so honestly.",
)


# ---------------------------------------------------------------------------
# Demo-mode brain (only used when no API key is configured)
# ---------------------------------------------------------------------------
def demo_reply(user_text: str) -> str:
    """Tiny rule-based responder so the UI works with zero setup."""
    t = user_text.lower()

    if re.search(r"\b(hello|hi|hey|namaste)\b", t):
        return ("Hello! 👋 I'm running in demo mode right now, so my answers are "
                "pre-written. Plug in a free Groq API key (see README) and I'll "
                "become a real AI assistant.")
    if "who are you" in t or "your name" in t:
        return "I'm Unima, a demo chatbot built with Python + Flask as an internship project."
    if "internship" in t or "project" in t:
        return ("This project is a full-stack chatbot: an HTML/JS frontend, a Flask "
                "backend, and an LLM connected through an API. Customise the system "
                "prompt in app.py to turn me into a support bot, FAQ bot, or tutor!")
    if "api" in t or "key" in t or "demo" in t:
        return ("To enable real AI answers: 1) create a free key at console.groq.com, "
                "2) run `export GROQ_API_KEY=your_key`, 3) restart this server. "
                "Details are in README.md.")
    if "joke" in t:
        return "Why do programmers prefer dark mode? Because light attracts bugs. 🐛"
    if "time" in t or "date" in t:
        return "The server says it's currently " + datetime.now().strftime("%A, %d %B %Y, %H:%M") + "."
    if "thank" in t:
        return "You're welcome! 😊"
    if "bye" in t:
        return "Goodbye! Good luck with your internship. 🚀"

    return (f'You said: "{user_text}". In demo mode I can only match a few keywords '
            "(try: hello, internship, joke, api key, time). Connect a free Groq API "
            "key and a real LLM will answer anything.")


# ---------------------------------------------------------------------------
# Real AI call (OpenAI-compatible chat completions — works with Groq,
# OpenRouter, Ollama, or OpenAI by changing API_URL / MODEL)
# ---------------------------------------------------------------------------
def ai_reply(messages):
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        "temperature": 0.7,
        "max_tokens": 1024,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            # Groq's Cloudflare blocks the default 'Python-urllib' User-Agent
            # with "403 error code: 1010" — so we identify as a browser.
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/api/health")
def health():
    """The frontend calls this on load to know which mode we're in."""
    return jsonify({"mode": "ai" if API_KEY else "demo", "model": MODEL if API_KEY else None})


@app.post("/api/chat")
def chat():
    body = request.get_json(silent=True) or {}
    messages = body.get("messages", [])

    # Basic validation: keep only well-formed user/assistant turns, cap history.
    clean = [
        {"role": m["role"], "content": str(m["content"])[:4000]}
        for m in messages[-20:]
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]
    if not clean:
        return jsonify({"error": "No message provided"}), 400

    try:
        if API_KEY:
            reply = ai_reply(clean)
            return jsonify({"reply": reply, "mode": "ai"})
        reply = demo_reply(clean[-1]["content"])
        return jsonify({"reply": reply, "mode": "demo"})
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:300]
        return jsonify({"error": f"AI API error {e.code}: {detail}. "
                                 "Check your API key and model name."}), 502
    except Exception as e:  # noqa: BLE001 — show a friendly message, never crash
        return jsonify({"error": f"Something went wrong: {e}"}), 500


@app.post("/api/chat/stream")
def chat_stream():
    """Streaming endpoint — the reply is sent token-by-token (plain text chunks)
    so the browser can render it as it arrives, ChatGPT-style."""
    body = request.get_json(silent=True) or {}
    messages = body.get("messages", [])
    clean = [
        {"role": m["role"], "content": str(m["content"])[:4000]}
        for m in messages[-20:]
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]
    if not clean:
        return jsonify({"error": "No message provided"}), 400

    # --- Demo mode: fake the typewriter effect word-by-word -----------------
    if not API_KEY:
        text = demo_reply(clean[-1]["content"])

        def demo_gen():
            for word in text.split(" "):
                yield word + " "
                time.sleep(0.05)

        return Response(demo_gen(), mimetype="text/plain; charset=utf-8",
                        headers={"Cache-Control": "no-cache"})

    # --- AI mode: proxy Groq's server-sent-events stream --------------------
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + clean,
        "temperature": 0.7,
        "max_tokens": 1024,
        "stream": True,   # <-- this one flag makes the LLM stream its tokens
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        },
        method="POST",
    )
    try:
        # HTTP errors (bad key, rate limit…) happen here, BEFORE streaming starts
        resp = urllib.request.urlopen(req, timeout=60)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:300]
        return jsonify({"error": f"AI API error {e.code}: {detail}"}), 502

    def gen():
        try:
            for raw in resp:                      # read SSE lines as they arrive
                line = raw.decode("utf-8", "ignore").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    delta = json.loads(data)["choices"][0]["delta"].get("content")
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
                if delta:
                    yield delta                   # forward each token to browser
        finally:
            resp.close()

    return Response(gen(), mimetype="text/plain; charset=utf-8",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Mode: {'AI (' + MODEL + ')' if API_KEY else 'DEMO (no API key)'}")
    app.run(host="0.0.0.0", port=port, debug=False)
