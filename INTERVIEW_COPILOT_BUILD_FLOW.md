# Interview Copilot — Professional Build Flow

**Status:** Source of truth for design & future development  
**Last updated:** 2026-08-07  
**Related:** `PRODUCT_PRD_chatgpt_toggle_listener.md` (feature inventory from prototype)

Use this document whenever designing, prompting GenAI, or implementing the rebuild. Do not invent a parallel architecture.

---

## 0. Platform policy (Mac first, Windows later)

### Priority rule (non-negotiable)

1. **macOS is the primary target.** All P0/P1 features must work correctly on Mac first.
2. **Windows is a planned enhancement**, not a blocker for Mac shipping.
3. If a feature conflicts or needs divergent OS APIs: **implement the Mac path fully**, stub or document the Windows path, and track it under “Windows enhancement backlog.”
4. Shared core logic stays OS-agnostic; OS-specific code lives only in thin adapters (`platform/macos/`, `platform/windows/`).

### Will all features work on both?

**Not 1:1 on day one.** Most product logic is cross-platform; several Studio/Live capabilities depend on OS audio, capture, and window APIs.

| Layer | Mac + Windows same? | Notes |
|-------|---------------------|-------|
| LLM, prompts, sessions, chats, bookmarks, answer modes, Fast/Full | Yes | Pure Python + files + OpenAI |
| File text extract (PDF/DOCX/code) | Yes | Library-based |
| Tk Studio/Live UI shell | Mostly yes | Same Tk; polish may differ |
| Mic recording | Yes | `sounddevice` |
| System / call audio (virtual cable) | Different drivers | Mac: **BlackHole**; Windows: **VB-Cable / Voicemeeter** |
| Native file/folder picker | Adapter | Mac: AppKit `NSOpenPanel`; Windows: Win32 / tk fallback |
| Multi-monitor screenshot under mouse | Adapter | Mac: Quartz/NSScreen; Windows: Win32 monitors |
| Global hotkeys | Mostly yes | `pynput`; modifiers: **Cmd** (Mac) vs **Ctrl** (Windows) |
| Always-on-top overlay | Yes | Tk attributes |
| Privacy: exclude from screen capture | Adapter | Mac: sharing/capture exclusion APIs; Windows: `WDA_EXCLUDEFROMCAPTURE` |
| Privacy: hide from Dock / taskbar | Adapter | Mac: Dock/LSUIElement; Windows: taskbar hide |
| Meeting auto-detect / packaging | Later per OS | Phase 5 |

### Design rule for adapters

```text
packages/audio/device.py          # Protocol: resolve_input_device(mode)
platform/macos/audio.py           # BlackHole name match
platform/windows/audio.py         # VB-Cable / Voicemeeter name match
platform/macos/picker.py          # NSOpenPanel
platform/windows/picker.py        # Win dialog / tk
platform/macos/privacy.py         # Capture exclude + Dock
platform/windows/privacy.py       # Capture exclude + taskbar
```

Core packages call Protocols only — never `import Quartz` or `win32api` inside `llm/` / `session/`.

### Windows enhancement backlog (identify, don’t block Mac)

When implementing any OS-sensitive feature on Mac, also add a checklist item:

- [ ] Windows adapter stub or `NotImplementedError` with clear message
- [ ] Entry in Windows backlog below (or issue/TODO with feature ID)

**Initial Windows backlog (post–Mac P0):**

| ID | Feature | Windows approach |
|----|---------|------------------|
| W1 | Internal/system audio | Detect VB-Audio Virtual Cable / Voicemeeter; README setup |
| W2 | Native multi file+folder picker | Win32 common dialog or tk + folder walk |
| W3 | Monitor-under-mouse screenshot | EnumDisplayMonitors / equivalent |
| W4 | Hotkey modifier map | Ctrl(+Shift) mirrors Cmd(+Shift) |
| W5 | Exclude overlay from capture | `SetWindowDisplayAffinity` / WDA_EXCLUDEFROMCAPTURE |
| W6 | Hide from taskbar | Tool window / WS_EX_TOOLWINDOW patterns |
| W7 | Packaging | PyInstaller / MSIX after Mac package works |
| W8 | Permission UX | Mic/screen permission guidance for Windows |

### Phase freeze (updated)

- **Phases 0–4:** Mac complete and shippable.
- **Windows adapters:** start after Mac Live (Phase 3) is accepted, unless a shared Protocol is trivial to stub earlier.
- Never delay a Mac milestone waiting for Windows parity.

---

## 1. Product vision

Build **one product** that combines:

1. **All power features** from the existing interview assistant (`chatgpt_toggle_listener.py`)
2. **Parakeet-class live UX** (floating overlay, auto listen/answer, screen analyze, post-call notes, privacy mode)

**Not** two separate apps. **Not** another single-file monolith.

### Product one-liner

**macOS-first** interview copilot (Windows via adapters later): Studio for setup/power tools + Live floating overlay for real-time assistance, sharing one modular core.

---

## 2. Dual-mode product model

| Mode | Purpose | Source of features |
|------|---------|-------------------|
| **Studio** | Full assistant: prompts, history, bookmarks, docs, diagnostics, hotkeys | Existing `chatgpt_toggle_listener.py` |
| **Live** | Compact floating session: auto Q→A, screen analyze, notes | Parakeet-style UX |

Both modes call the **same packages** (`audio`, `stt`, `llm`, `context`, `session`, `prompts`, `screen`, `notes`, `hotkeys`). UI never owns business logic.

```text
┌─────────────────┐     ┌─────────────────┐
│  Studio App     │     │  Live Overlay   │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
         ┌───────────────────────┐
         │  Core packages        │
         │  audio stt llm …      │
         └───────────────────────┘
```

---

## 3. Architecture target

```text
interview_copilot/
  apps/
    studio/                 # Full power UI (parity with chatgpt_toggle_listener)
    live/                   # Floating overlay + session setup
  packages/
    audio/                  # BlackHole / mic, record, VAD, level
    stt/                    # Whisper (+ future local)
    llm/                    # Stream, models, answer modes, context builder, summarize
    context/                # File/folder extract, image compress
    session/                # chats.json, AutoSave, prune, bookmarks
    prompts/                # tabs.json, profiles, default interview
    screen/                 # Screenshot / analyze coding
    notes/                  # Post-call AI notes → sessions/
    hotkeys/                # Global + in-app shortcuts
  shared/
    config/                 # .env + typed settings
    logging/                # Stage timings
    types/
  tests/
  pyproject.toml
  README.md
```

### Required Protocols (interfaces)

- `AudioSource`
- `STTProvider`
- `LLMProvider`
- `SessionStore`
- `PromptStore`

Dependency rule: **UI → use-cases → adapters**. No UI imports inside core packages.

### Persistence contracts (preserve)

| File | Role |
|------|------|
| `.env` | `OPENAI_API_KEY` |
| `ui_prefs.json` | Geometry, sashes, font, default interview, UI mode |
| `tabs.json` | Prompt tabs / subtabs |
| `chats.json` | Sessions + bookmarks; AutoSave by **title** not index |
| `setup_profiles.json` | Named prompt profiles |
| `sessions/` | Live session transcripts + post-call notes |

---

## 4. Feature merge strategy

### From existing assistant — KEEP 100%

- Manual listen → Whisper → stream answer (BlackHole / mic)
- Live transcription while recording
- Text chat, paste images, screenshot (`--` / `!`)
- Resume/JD/docs (native picker, folder walk, multi-format extract)
- Prompt tabs, Quick Setup, profiles, default interview (`Cmd+Shift+I`), Intro-first one-by-one
- Chat AutoSave, prune, rename/delete, drag-reorder
- Bookmarks + navigation
- Answer modes (default / quick / detailed / code)
- Fast vs Full context + background summarize + diagnostics
- Rich global hotkeys, always-on-top, font, UI prefs
- API connection check, model cycle, retries

Reference detail: `PRODUCT_PRD_chatgpt_toggle_listener.md`

### From Parakeet — ADD (product UX)

| ID | Feature | Phase |
|----|---------|-------|
| PK1 | Session setup (resume, JD, extra, model, language, audio, auto-answer) | 3 |
| PK2 | Floating always-on-top Live overlay | 3 |
| PK3 | Hands-free VAD → auto question → STT → auto answer | 3 |
| PK4 | Analyze Screen (coding) in overlay | 3 |
| PK5 | Post-call AI notes | 3 |
| PK6 | Live transcript panel | 3 |
| PK7 | Minimal live hotkeys | 3 |
| PK8 | Multi-model path (OpenAI first; Claude later) | 1 / 5 |
| PK9 | Language picker | 3 |
| PK10 | Documents knowledge base (beyond resume) | 2–3 |
| PK11 | Meeting auto-detect | 5 |
| PK12 | Browser companion | 5 |
| PK13 | Mobile web companion | 5 |
| PK14 | Accounts / credits / billing | 5 |

### Privacy Mode — INCLUDE (honest)

| Include | Do **not** build as product goals |
|---------|-----------------------------------|
| Exclude overlay from screen capture | Task Manager / Activity Monitor disguise |
| Hide from Dock / menubar-only | Cursor spoofing for proctors |
| Opacity / click-through overlay | Tab-switch deception |

Rationale: capture-exclude and Dock hide are legitimate privacy UX. Process masquerading and anti-proctor tricks are out of scope for this product.

---

## 5. Correct working flows (must preserve / implement)

### Studio flows (from prototype)

- **A** Listen → (live STT) → stop → final STT → stream answer → autosave  
- **B** Type/paste (+ images) → stream answer  
- **C** Screenshot → vision analyze  
- **D** Load docs → system context  
- **E** Prompt library / default interview one-by-one  
- **F** Session lifecycle (AutoSave by title, prune ≤10)

### Live flows (Parakeet-class)

- **L1** Setup session → open overlay  
- **L2** Start listen → VAD segments question → STT → auto answer (stream)  
- **L3** Manual ask / stop anytime  
- **L4** Analyze Screen → coding help  
- **L5** End → AI notes saved under `sessions/`  
- **L6** Optional Privacy Mode (capture exclude + Dock hide)

---

## 6. Phased build plan

Never rebuild everything in one shot. Each phase ends with something runnable + tests.

### Phase 0 — Spec lock

- [x] Approach documented (this file)
- [x] Prototype PRD exists
- [ ] Merged P0/P1 backlog approved before coding surge
- Freeze: **macOS-first** (Windows = enhancement backlog), **OpenAI-first**, **local JSON persistence**
- See **§0 Platform policy** for Mac vs Windows compatibility and conflict priority

### Phase 1 — Core platform

Interfaces + implementations only (minimal harness UI ok).

1. `shared/config` + logging (stage timings: stt_ms, llm_ttft_ms, total_ms)
2. `packages/audio` (BlackHole / mic, record, snapshot, level)
3. `packages/stt` (Whisper + retries)
4. `packages/llm` (stream, modes, context builder)
5. `packages/context` (extract + image compress)
6. `packages/session` + `packages/prompts`
7. Unit tests for extract, session save/load, message build

**Done when:** harness can listen → transcribe → answer → save.

### Phase 2 — Studio MVP

Port full `chatgpt_toggle_listener` behavior onto packages.

**Done when:** daily-driver parity with current assistant (prompts, history, hotkeys, docs, modes).

### Phase 3 — Live overlay (Parakeet UX)

- Setup window  
- Floating overlay + VAD auto-answer  
- Analyze Screen + End + Notes  
- Privacy Mode (capture exclude + Dock hide)  
- Wire Studio prompts / default interview into Live context  

**Done when:** a full interview can be run from Live alone.

### Phase 4 — Polish & packaging

Unified hotkeys, resilience, PyInstaller/brief, README (BlackHole + `.env`), crash-safe threads.

### Phase 5 — Scale

Meeting detect, browser/mobile, multi-LLM, accounts/billing.

---

## 7. Implementation order (milestones)

| # | Milestone | Exit criteria |
|---|-----------|---------------|
| 1 | Config + logging | `.env` loads; settings typed |
| 2 | Audio package | Record BlackHole/mic → WAV |
| 3 | STT package | Whisper returns text with retries |
| 4 | LLM package | Streaming answer + answer modes |
| 5 | Context package | PDF/DOCX/TXT + image compress |
| 6 | Session + prompts stores | JSON contracts compatible |
| 7 | Studio UI shell | Chat + listen wired to packages |
| 8 | Studio parity | Match prototype P0 features |
| 9 | Live setup + overlay | Floating session works |
| 10 | VAD auto-answer | Hands-free Q→A |
| 11 | Screen + notes | Coding analyze + post-call notes |
| 12 | Privacy Mode | Capture exclude + Dock hide |
| 13 | Package + docs | Installable + README |

Working method with GenAI/agent:

1. Approve backlog / this flow  
2. Implement **one milestone only**  
3. Review → next milestone  
4. Keep `chatgpt_toggle_listener.py` as reference until Phase 2 acceptance  

---

## 8. Non-functional requirements

- Python 3.11+, type hints on new code  
- Secrets only via env; never commit `.env`  
- UI updates only on main thread (`after`)  
- Structured logs with stage timings  
- Graceful errors: missing device, bad API key, empty audio, bad file  
- Privacy: local-first storage; no silent full-audio cloud retention beyond STT  
- Ethics: assist the candidate; do **not** market or implement “undetectable cheating” / proctor evasion  

### Prototype debt — fix, don’t copy

- Monolith + duplicate screenshot helpers  
- Global `client` / `app` coupling  
- Live STT API spam (~2s) — rate-limit or local STT later  
- Base64 images bloating `chats.json` — externalize or strip  
- AutoSave must key by **title**, never index 0  

---

## 9. Definition of done (product)

- [ ] Studio ≈ current assistant feature-complete  
- [ ] Live ≈ Parakeet usable UX (overlay, auto, coding, notes, privacy)  
- [ ] One modular codebase with Protocols + tests  
- [ ] README: run in <15 minutes (API key + BlackHole)  
- [ ] Ready to add SaaS later without rewriting core  

---

## 10. Prompt addendum (paste into GenAI)

```text
Follow INTERVIEW_COPILOT_BUILD_FLOW.md as the source of truth.
Product = Studio (full chatgpt_toggle_listener features) + Live (Parakeet-class overlay).
Shared modular packages with Protocols. macOS-first (Windows via adapters later — never block Mac),
OpenAI-first, local JSON.
Implement only the agreed milestone. Do not create a monolith.
Privacy Mode = capture exclude + Dock hide only — no Task Manager disguise,
cursor spoofing, or tab-switch deception.
Preserve flows A–F and Live flows L1–L6. Keep persistence contracts compatible.
Reference PRODUCT_PRD_chatgpt_toggle_listener.md for feature IDs and acceptance.
On OS-specific work: Mac path first; stub Windows and list under Windows backlog (§0).
```

---

## 11. Change log

| Date | Change |
|------|--------|
| 2026-08-07 | Initial build flow: dual-mode, phases, Parakeet merge, privacy stance |
| 2026-08-07 | §0 Platform policy: Mac-first priority; Windows adapters + enhancement backlog |
