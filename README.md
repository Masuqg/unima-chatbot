# Unima — AI Chatbot (Internship Project)

A full-stack AI chatbot: **HTML/CSS/JS frontend** + **Python Flask backend** + a
**real LLM** connected through Groq's free API. Runs in a keyword-based *demo mode*
until you add an API key.

```
Browser (chat UI)  ──POST /api/chat──>  Flask backend (app.py)  ──HTTPS──>  Groq API (Llama 3.3)
        <──────────── reply ──────────                          <────────────
```

---

## 1. Run it locally (5 minutes)

```bash
cd chatbot
pip install -r requirements.txt     # installs Flask
python app.py                       # -> open http://localhost:5000
```

Windows users: the commands are the same in PowerShell / CMD.

## 2. Enable real AI (free, no credit card)

1. Go to **https://console.groq.com** → sign up → **API Keys** → *Create API Key*.
2. Set it as an environment variable, then restart the server:

```bash
# Linux / macOS
export GROQ_API_KEY=gsk_your_key_here

# Windows PowerShell
setx GROQ_API_KEY "gsk_your_key_here"   # then open a NEW terminal

python app.py
```

Free-tier models you can use (set with `MODEL=...`): `llama-3.3-70b-versatile`
(default, best quality), `llama-3.1-8b-instant` (fastest), `qwen3-32b`.

**Alternatives:** Google AI Studio (Gemini free tier) or OpenRouter — just change
`API_URL` + `MODEL` in `app.py`. The code speaks the OpenAI chat-completions format,
so any OpenAI-compatible endpoint works.

> ⚠️ **Never paste your API key into code or GitHub, and never enter it on a shared
> machine/preview link.** Environment variables only.

## 3. How it works (what to say in interviews/reports)

- **Frontend** (`static/index.html`): keeps the conversation in a JS array, sends it
  to the backend as JSON, renders bubbles + a typing indicator.
- **Backend** (`app.py`): stateless Flask server. `/api/chat` validates the message
  list, prepends the **system prompt** (the bot's personality), calls the LLM, and
  returns the reply. `/api/health` tells the UI which mode is active.
- **LLM**: a large language model (Llama 3.3 70B) hosted by Groq — inference happens
  on *their* GPUs, so this runs fine on any laptop.
- **Key concepts you now know:** REST APIs, JSON, environment variables, system
  prompts, conversation history / context, temperature, tokens, graceful fallbacks,
  and **token streaming over server-sent events** (`/api/chat/stream`).

## 4. Customise it (make it *yours* — interns who customise stand out)

| Goal | Change |
|---|---|
| Company FAQ / support bot | Edit `SYSTEM_PROMPT` in `app.py`: paste company policies/FAQs and tell it to answer only from them |
| New name & look | Edit the header + CSS variables in `static/index.html` |
| Different/cheaper model | `MODEL=llama-3.1-8b-instant python app.py` |
| Longer answers | Raise `max_tokens` in `ai_reply()` |

## 5. Extension ideas (pick one as your "stretch feature")

1. **RAG / document Q&A** — embed company PDFs (e.g. with `sentence-transformers` +
   a vector store) and let the bot answer from real documents. *The #1 résumé booster.*
2. **Persistence** — save chats to SQLite so users can return to old conversations.
3. ~~Streaming~~ ✅ **done** — replies stream token-by-token via `/api/chat/stream`.
4. **Deployment** — put it online free on Render / Railway / PythonAnywhere so your
   mentor can click a link instead of running code.
5. **Extras** — dark/light toggle, feedback buttons 👍👎, rate limiting, login.

## 6. Résumé bullet (steal this)

> *Built a full-stack AI chatbot (Flask, JavaScript, Llama 3.3 via Groq API) with
> token-by-token streaming replies, a system-prompt-configurable persona,
> conversation memory, and a rule-based fallback mode; deployed it for live demos.*

## Project structure

```
chatbot/
├── app.py               # Flask backend: routes, AI call, demo brain
├── requirements.txt     # one dependency: Flask
├── static/
│   └── index.html       # chat UI (inline CSS + JS, zero build tools)
└── README.md            # this file
```
