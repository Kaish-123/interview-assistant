# Interview Assistant — Product PRD & Feature Spec
**Source prototype:** `chatgpt_toggle_listener.py`  
**Purpose:** Paste this document into GenAI prompts so rebuilds preserve correct behavior, prioritize MVP correctly, and stay production-ready.

---

## 1. Product one-liner

macOS desktop interview copilot: capture interviewer audio (BlackHole/mic) or typed/pasted questions, stream GPT answers grounded in resume/JD/docs, with prompt libraries, chat history, screenshots, and global hotkeys for live interview use.

---

## 2. Correct end-to-end working flows (must preserve)

### Flow A — Listen → Answer
1. User toggles Listen (`🎤` or hotkey `` ` ``).
2. `AudioRecorder` captures 16 kHz mono int16 from BlackHole (internal) or first non-BlackHole mic (external).
3. Live UI shows “Listening…” + incremental “Live Question: …” via Whisper every ~2s on audio snapshots.
4. User stops → full WAV written → final Whisper transcription (with retries) → append as user message → stream GPT answer into response box (viewport scroll preserved) → autosave session.

### Flow B — Type / Paste → Answer
1. Text in input (Enter sends; Shift+Enter newline).
2. Paste text or clipboard images (compressed PNG) as pending attachments.
3. Optional multimodal message → stream answer → autosave.

### Flow C — Screenshot → Answer
1. Type `--` in input OR hotkey `!` (monitor under mouse) OR programmatic capture.
2. Compress screenshot → attach / send with analyze prompt → stream vision answer.

### Flow D — Context load
1. Hotkey `2+3` or Resume/JD button → native macOS file/folder picker.
2. Folders expanded recursively (skip binaries/build dirs, 5 MB/file cap).
3. Text extracted (txt/code/PDF/DOCX/XLSX/PPTX + textract fallback) → injected as system messages (50k char cap per doc).

### Flow E — Prompt library / interview bootstrap
1. Tabs → subtabs store named prompts in `tabs.json`.
2. Clicking a subtab appends prompt to input and auto-sends (with pending images).
3. Quick Setup / profiles / “default interview” (`Cmd+Shift+I`) runs selected prompts **one-by-one** (Intro first if named “Intro”), waiting for each stream to finish.

### Flow F — Session lifecycle
1. Autosave to `chats.json` title `"AutoSave - Last Session"` (deduped by title).
2. New chat / switch chat persists meaningful sessions; prune keeps ≤10 real chats + one AutoSave.
3. Bookmarks per session restored on load.

---

## 3. Complete feature inventory (as implemented)

### A. Audio & transcription
| ID | Feature | Behavior notes |
|----|---------|----------------|
| A1 | BlackHole internal capture | Prefer device name containing “BlackHole” |
| A2 | External mic toggle | Prefer first non-BlackHole input; UI label Mic / BlackHole |
| A3 | Record start/stop | Queue + worker thread; join on stop; write `interviewer.wav` |
| A4 | Audio snapshot | Thread-safe concatenate for live STT / level meter |
| A5 | Live transcription | ~2s Whisper loop while recording; updates “Live Question:” line |
| A6 | Final Whisper STT | `whisper-1`, optional prompt hint, 3 retries w/ backoff |
| A7 | Audio level meter | RMS of last ~0.1s → progress bar while recording |
| A8 | Interrupt busy state | New Listen can force-stop streaming/processing |

### B. LLM / chat engine
| ID | Feature | Behavior notes |
|----|---------|----------------|
| B1 | Streaming chat completions | OpenAI stream; cancelable; max_tokens 1600 |
| B2 | Model cycle | gpt-4o / gpt-4o-mini / gpt-4-turbo |
| B3 | Answer modes | default / quick / detailed / code → extra system instruction |
| B4 | Fast vs Full context | Optimization off = full history; on = summarize + recent rounds + image detail=low |
| B5 | Background summarization | gpt-4o-mini summary of older turns; sync if >20 rounds without summary |
| B6 | Aggressive context tiers | By message count: NORMAL → MODERATE → AGGRESSIVE → ULTRA (strip old images, truncate) |
| B7 | Token estimate / diagnostics | Dialog + console report; force summarize; new chat CTA |
| B8 | API retries | Chat + STT: 3 attempts, exponential backoff |
| B9 | Connection status | models.list every 60s → Connected / Offline |
| B10 | Scroll-safe streaming insert | Preserve `@0,0` absolute index while appending tokens |
| B11 | Code block highlight tag | Regex ``` blocks → `code` tag color |
| B12 | System prompt default | Interview assistant persona |

### C. Documents & multimodal
| ID | Feature | Behavior notes |
|----|---------|----------------|
| C1 | Robust file text extract | Native readers first; textract last resort |
| C2 | Folder recursive collect | Skip .git/node_modules/venv; skip media/binaries; 5 MB max |
| C3 | Native macOS picker | AppKit NSOpenPanel files+folders → osascript → tk fallback |
| C4 | Image compress JPEG/PNG | Resize ≤1024/1280; base64 for API |
| C5 | Clipboard image paste | Queue multiple pending attachments; placeholders in input |
| C6 | Full-screen capture under mouse | Multi-monitor via Quartz NSScreen + pyautogui region |
| C7 | `--` screenshot shortcut | Capture all monitors screenshot path → analyze |
| C8 | Copy Q + images export | Clipboard clean text; images to Desktop; Finder open |

### D. Prompt / profile system
| ID | Feature | Behavior notes |
|----|---------|----------------|
| D1 | Tabs + subtabs CRUD | Persist `tabs.json` (name, prompt, text_input) |
| D2 | Subtab click auto-send | Append to input + submit (with images) |
| D3 | Quick Setup dialog | Multi-select → apply one-by-one |
| D4 | Setup profiles | `setup_profiles.json`; sidebar list; double-click apply |
| D5 | Profile / default order editor | Move up/down; Intro always first when applying |
| D6 | Default interview set | Saved in `ui_prefs.json`; hotkey Cmd+Shift+I |
| D7 | Drag-reorder tabs/subtabs/chats | Persist order; subtabs move across tabs allowed |

### E. Chat history & persistence
| ID | Feature | Behavior notes |
|----|---------|----------------|
| E1 | `chats.json` sessions | title, messages, bookmarks |
| E2 | AutoSave last session | Update by title (not index); dedupe on load |
| E3 | Resume AutoSave on launch | Restore messages + display |
| E4 | Named session save | Title from attached doc names + timestamp |
| E5 | Switch-chat persist | Save working chat before load if dirty (hash) |
| E6 | Auto-prune | Keep ≤10 real + 1 AutoSave |
| E7 | Delete / rename chats | Delete keeps selection + AutoSave only |
| E8 | Display last N rounds | Default 20 Q&A pairs in UI (full msgs kept in memory) |

### F. Bookmarks / navigation
| ID | Feature | Behavior notes |
|----|---------|----------------|
| F1 | Bookmark at cursor / F4 / Cmd+B | Nearest QUESTION line; gold highlight |
| F2 | Bookmark panel | Jump / double-click delete; cycle F5 |
| F3 | Persist bookmarks per session | In chats.json |
| F4 | Context menu | Bookmark / remove / show all questions / copy Q+images |
| F5 | Chat scroll keys | PgUp/PgDn top/end; Up/Down paragraph when focus not in input |

### G. UI / window / prefs
| ID | Feature | Behavior notes |
|----|---------|----------------|
| G1 | Sidebar prompts + chats | Collapsible; vertical sash with minsizes |
| G2 | Always-on-top pin | Attribute toggle |
| G3 | Font A+/A− | 8–24 Consolas on response box |
| G4 | UI prefs persist | geometry, paned_sash, sidebar_sash, font, tab open state, ui_mode, default_interview_subtabs → `ui_prefs.json` |
| G5 | F1/F2/F3 | Print geometry / save prefs / apply prefs |
| G6 | Modern vs classic UI mode | Saved; restart required |
| G7 | Dark chat theme | #343541 bg, white text, code teal |
| G8 | Status bar messaging | Listening / processing / ready / errors |

### H. Global hotkeys (pynput)
| Hotkey | Action |
|--------|--------|
| `` ` `` | Toggle listen / stop+process |
| `~` | Force stop stream + reset flags |
| `!` | Screenshot monitor under mouse → attach |
| `1+2` | Focus chat input |
| `2+3` | Upload resume/files |
| `3+4` | Toggle BlackHole ↔ Mic |
| `5+6` | Listen on external mic then revert to BlackHole |
| Cmd+Ctrl+= / − | Font ± |
| Cmd+P | Pin window |
| Cmd+Shift+Z | Restart app |
| Cmd+Shift+I | Apply default interview prompts |
| Cmd+Shift+S | Open Quick Setup |
| Caps Lock | Ignored (stability) |

### I. Infra / config
| ID | Feature | Behavior notes |
|----|---------|----------------|
| I1 | `.env` OpenAI key | `OPENAI_API_KEY` via dotenv |
| I2 | Threading model | Audio, live STT, stream, summary, API check on daemon threads; UI via `after()` |
| I3 | Self-restart | Re-exec same Python + script; stop listener; hard exit |

---

## 4. Persistence files (contracts)

| File | Contents |
|------|----------|
| `.env` | `OPENAI_API_KEY` |
| `ui_prefs.json` | geometry, sashes, font, ui_mode, tab_tree_open, default_interview_subtabs |
| `tabs.json` | `{ "tabs": [ { "name", "subTabs": [ { "name", "prompt", "text_input" } ] } ] }` |
| `chats.json` | `[ { "title", "messages", "bookmarks": [[line_index, preview], ...] } ]` |
| `setup_profiles.json` | `{ "ProfileName": ["sub_0_0", "sub_0_1", ...] }` |
| `interviewer.wav` | Last full recording (ephemeral artifact) |

---

## 5. Phase-1 MVP checklist (rebuild these first)

Ship a **modular** desktop app that correctly implements:

### Must-have (P0)
- [ ] Config from `.env` + typed settings (sample rate, devices, models)
- [ ] Audio: BlackHole + mic modes, record/stop, WAV, level meter
- [ ] STT: final Whisper on stop (retries); **live STT optional but recommended**
- [ ] Streaming GPT answers into chat UI with cancel/stop
- [ ] Model selector (at least 4o / 4o-mini)
- [ ] Answer mode: default / quick / detailed / code
- [ ] Load resume/JD/docs into system context (PDF/DOCX/TXT/code minimum)
- [ ] Text chat input + Enter / Shift+Enter
- [ ] Paste image + screenshot analyze (`--` or hotkey)
- [ ] Chat autosave + resume last session + new chat
- [ ] Prompt tabs/subtabs load from `tabs.json` + click-to-send
- [ ] Default interview / Quick Setup one-by-one apply
- [ ] Always-on-top + font size
- [ ] Core global hotkeys: listen `` ` ``, stop `~`, screenshot `!`, upload, mic toggle
- [ ] Package layout: `audio`, `stt`, `llm`, `context`, `session`, `ui` (no monolith)
- [ ] README: BlackHole setup, `.env`, run instructions
- [ ] Unit tests: message build / extract text / session save-load

### Should-have in Phase 1 if time (P1)
- [ ] Fast/Full optimization + background summary
- [ ] Performance diagnostics dialog
- [ ] Bookmarks + persist
- [ ] Chat prune / rename / delete
- [ ] Setup profiles + order editor
- [ ] UI prefs geometry/sash restore
- [ ] Native AppKit file/folder picker

### Phase 1 acceptance criteria
1. With BlackHole + API key, user can Listen → Stop → see transcribed QUESTION → streamed ANSWER.
2. User can attach a resume PDF and get answers that reference it.
3. Screenshot or pasted image produces a vision answer.
4. Restarting the app restores AutoSave session.
5. Default interview hotkey runs prompts sequentially without overlapping streams.
6. No single-file monolith; interfaces for STT/LLM/Audio/SessionStore.

---

## 6. Explicitly OUT of Phase 1 (do not build yet)

- Multi-user auth, cloud sync, billing/metering SaaS
- Mobile / web client as primary surface
- Auto-inject answers into Zoom/Meet/Teams
- “Undetectable / stealth from interviewer” product claims
- Local Whisper-only offline mode (optional Phase 2)
- Fine-tuned private models
- Team admin / shared prompt marketplace
- Full classic/modern dual UI rebuild (one solid UI is enough)
- Billing/balance management UI (comment stub only in prototype)
- Windows/Linux parity (macOS-first)

---

## 7. Phase roadmap (after MVP)

| Phase | Focus |
|-------|--------|
| 2 | Local STT (faster-whisper), packaging (PyInstaller), crash/log telemetry, prompt versioning |
| 3 | Accounts, usage quotas, optional encrypted session sync |
| 4 | Multi-provider LLM, enterprise local-only mode, analytics |

---

## 8. Non-functional requirements

- Python 3.11+, type hints on new modules
- Secrets only via env; never commit `.env`
- Structured stage timings: `vad/record`, `stt_ms`, `llm_ttft_ms`, `total_ms`
- UI updates only on main thread (`after`)
- Graceful errors: missing device, bad API key, empty audio, unreadable file
- Privacy: local JSON persistence by default; no silent full-audio cloud retention beyond STT call
- Ethics: product assists the candidate; do not market as cheating/undetectable

---

## 9. Suggested target architecture

```
interview_copilot/
  apps/desktop/          # Tk (or successor) entry, overlay/main window
  packages/
    audio/               # device resolve, recorder, level
    stt/                 # Whisper adapter (+ future local)
    llm/                 # OpenAI stream, modes, context builder, summarize
    context/             # file extract, folder walk, image compress
    session/             # chats, bookmarks, prune, autosave
    prompts/             # tabs, profiles, default interview
    hotkeys/             # pynput bindings map
  shared/config|logging|types/
  tests/
  pyproject.toml
  README.md
```

**Adapters (Protocols):** `AudioSource`, `STTProvider`, `LLMProvider`, `SessionStore`, `PromptStore`.

---

## 10. Known prototype debt (fix in rebuild, don’t copy blindly)

- Monolith + nested/duplicate `capture_and_submit_screenshot` definitions
- Global `client` / `app` coupling; hard to test
- Live STT hammers Whisper API (~every 2s) — rate/cost risk; batch or local STT later
- Image base64 kept in chat JSON → huge files; strip or externalize blobs in rebuild
- Caps Lock / hotkey edge cases already patched — keep guards
- AutoSave bugs historically from index-based updates — **always key by title**
- UI thread safety: never touch Tk from worker threads without `after`

---

## 11. Paste-ready prompt addendum

Copy everything below into your GenAI build prompt:

```text
## SOURCE OF TRUTH — FEATURE & MVP SPEC
Implement from the product PRD for chatgpt_toggle_listener.py (Interview Assistant).

Preserve correct working flows:
- Listen (BlackHole/mic) → live optional STT → stop → final Whisper → stream GPT answer → autosave
- Text/paste (incl. images) → stream answer
- Screenshot (! or "--") → vision analyze
- Resume/JD/docs via native picker → system context
- tabs.json prompt library; Quick Setup / profiles / default interview one-by-one (Intro first)
- chats.json AutoSave by title + resume on launch; prune ≤10 real chats
- Global hotkeys: ` listen, ~ stop, ! screenshot, 1+2 focus, 2+3 upload, 3+4 mic toggle, 5+6 external listen, Cmd+Shift+I default interview

Phase 1 = P0 checklist only; modular packages with Protocols; no monolith; macOS-first.
Out of scope: auth/billing/cloud sync, auto-inject into meeting apps, stealth-cheating marketing, Windows-first.

Deliver: (1) architecture + module map, (2) migrate feature IDs A1–I3 into modules, (3) implement P0 incrementally with tests and README.
Do not invent unrelated features. Ask only if a P0 decision is blocked.
```

---

## 12. Recommended implementation order (for GenAI or engineers)

1. `shared/config` + logging  
2. `packages/audio` + tests  
3. `packages/stt` (Whisper)  
4. `packages/llm` (stream + answer modes + context builder)  
5. `packages/context` (extract + compress)  
6. `packages/session` (chats autosave)  
7. `packages/prompts` (tabs + default interview)  
8. Minimal desktop UI wiring Listen/Chat/Upload  
9. Hotkeys  
10. P1: optimize mode, bookmarks, profiles, prefs  

Each milestone: runnable demo + tests before next.
