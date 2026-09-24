# Interview Copilot — Web companion (Parakeet-style)

Browser Studio + Live overlay on the same Python packages as the desktop app.

## Features

| Mode | What you get |
|------|----------------|
| **Studio** | Chat stream, mic listen → STT → answer, attach docs, paste images, screen capture analyze, prompt tabs/subtabs, profiles, default interview, chat history + AutoSave, bookmarks, answer modes, Fast/Full, model select |
| **Live** | Session setup (resume/JD/extra/lang/model), floating overlay, Listen, Auto Q→A loop, mid-call chat, screen analyze, post-call notes, dim overlay |

Audio uses the **browser mic** (and optional tab/screen capture via browser APIs). Desktop BlackHole remains the desktop app path on macOS; on Windows use VB-Cable / Voicemeeter when you want system audio in the desktop app.

**Windows:** landing, login, Studio, and Live run in the browser the same as on Mac. Hide from share spawns the native overlay (`WDA_EXCLUDEFROMCAPTURE` + hidden taskbar button). Close / click-through: `Ctrl+Shift+W` / `Ctrl+Shift+O`. Python 3.11+, same `python -m interview_copilot.apps.web`.

## Run

```bash
# from repo root — needs OPENAI_API_KEY in .env
pip install -r interview_copilot/requirements.txt
pip install -r interview_copilot/apps/web/requirements.txt

python3 -m interview_copilot.apps.web
# open http://127.0.0.1:8787          landing
#      http://127.0.0.1:8787/login    Google + email OTP
#      http://127.0.0.1:8787/app      Studio + Live
```

Copy `interview_copilot/env.example` into `.env`. For Google sign-in, create an OAuth client and set the authorized redirect URI to:

`http://127.0.0.1:8787/api/auth/google/callback`

Set `AUTH_REQUIRED=true` to gate `/app` and APIs. Email codes print to the server log; with `AUTH_DEV_SHOW_CODE=true` they also appear on the login screen (disable that in production).

Or:

```bash
uvicorn interview_copilot.apps.web.server:app --host 127.0.0.1 --port 8787
```

## Hotkeys (browser focused)

| Key | Action |
|-----|--------|
| `` ` `` | Toggle Listen |
| `!` | Screen capture → analyze |

## API

- `GET /api/status`
- `POST /api/engines` — create Studio/Live engine
- `POST /api/chat/stream` — SSE chat
- `POST /api/listen/stream` — audio upload → STT → optional answer (SSE)
- `POST /api/documents/upload`, `POST /api/screen/analyze`
- `GET/POST /api/chats`, `/api/prompts`, `/api/profiles`, `/api/live/notes`

Persistence reuses `interview_copilot/data/` (`chats.json`, `tabs.json`, …) and `sessions/`.
