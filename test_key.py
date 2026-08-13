"""
test_key.py — verify your Groq API key works BEFORE running the chatbot.
Usage:  python test_key.py
"""

import json
import os
import sys
import urllib.request
import urllib.error

API_KEY = os.environ.get("GROQ_API_KEY")
MODEL = os.environ.get("MODEL", "llama-3.3-70b-versatile")

if not API_KEY:
    sys.exit("❌ GROQ_API_KEY is not set. Set it with setx, then open a NEW terminal and retry.")

print(f"Testing key gsk…{API_KEY[-4:]} with model '{MODEL}' …")

payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": "Reply with exactly: 'Groq connection successful!'"}],
    "max_tokens": 20,
}
req = urllib.request.Request(
    "https://api.groq.com/openai/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        # Groq's Cloudflare blocks the default 'Python-urllib' User-Agent
        # with "403 error code: 1010" — so we identify as a browser:
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        reply = json.loads(resp.read())["choices"][0]["message"]["content"]
        print("✅ AI replied:", reply)
        print("Your key works — now run:  python app.py")
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", "ignore")[:300]
    if e.code == 401:
        print("❌ 401 Unauthorized — the key is wrong or revoked. Create a fresh one at console.groq.com/keys")
    elif e.code == 404 or "decommissioned" in body:
        print(f"❌ Model problem: {body}\n→ Try a different model, e.g. $env:MODEL='llama-3.1-8b-instant'")
    elif e.code == 429:
        print("❌ 429 Rate limit — wait a minute and retry (free tier has per-minute caps).")
    else:
        print(f"❌ HTTP {e.code}: {body}")