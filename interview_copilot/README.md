# Interview Copilot

macOS-first interview assistant rebuilt as modular packages (see `INTERVIEW_COPILOT_BUILD_FLOW.md`).

## Setup

```bash
cd /path/to/chatgpt_gui_mac
python3 -m pip install -r interview_copilot/requirements.txt
cp interview_copilot/env.example .env   # set OPENAI_API_KEY
```

**System audio (Mac):** install [BlackHole](https://existential.audio/blackhole/), create a Multi-Output Device (Speakers + BlackHole), set it as system output.

## Run Studio (P0 parity shell)

```bash
python3 -m interview_copilot.apps.studio
# or
python3 -m interview_copilot.main --studio
```

### Studio features (Milestone 8)

- Listen (BlackHole / Mic) → Whisper → streaming answers
- Text chat, paste images, screenshot (`📸` or type `--`)
- Attach PDF/DOCX/TXT
- Answer modes, Fast/Full context, model cycle
- Prompts sidebar (`tabs.json`), profiles, default interview (`Cmd+Shift+I`)
- Chat history + AutoSave (`data/chats.json`)
- Bookmarks (F4 / F5)
- Hotkeys: `` ` `` listen, `~` stop, `!` screenshot (global when available)
- Pin window, font A+/A−, save UI prefs (F2)

## Run Live overlay (desktop)

```bash
python3 -m interview_copilot.main
```

## Run Web companion (Studio + Live in browser)

```bash
python3 -m interview_copilot.apps.web
# → http://127.0.0.1:8787
```

See `apps/web/README.md`. Uses browser mic + screen capture; same `data/` JSON stores.

## Tests

```bash
python3 -m pytest interview_copilot/tests/ -q
```

## Package layout

`shared/` · `packages/{audio,stt,llm,context,session,prompts}` · `apps/{studio,web}`
