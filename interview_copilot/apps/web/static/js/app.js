/* Interview Copilot — Studio + Live web client */
(() => {
  const state = {
    studioId: null,
    liveId: null,
    sessionId: null,
    sessionConnection: "real",
    sessionPlatform: "browser",
    status: null,
    messages: [],
    bookmarks: [],
    pendingImages: [],
    fontSize: 14,
    listening: false,
    liveListening: false,
    liveAuto: false,
    autoLoop: null,
    mic: new CallAudioCapture(),
    liveMic: new CallAudioCapture(),
    bubbles: [],
    lastQuestion: "",
    qText: "",
    qAt: 0,
    qHold: null,
    qPartialBusy: false,
    answering: false,
    answerGen: 0,
    prefetch: { gen: 0, text: "", acc: "", inflight: false, done: false },
    captioner: null,
    qPartialQueued: null,
    queuedUtterance: null,
    liveStt: null,
    liveSttOk: false,
    liveSttAcc: "",
    timerStarted: 0,
    timerHandle: null,
    currentMode: "sessions",
    answerSync: null,
    lastListenToggleAt: 0,
    liveLogTimer: null,
    liveAnswer: "",
    liveCaptionLive: false,
    qType: { shown: "", want: "", timer: null, where: "live" },
  };

  const $ = (id) => document.getElementById(id);
  const setStatus = (el, text) => { if (el) el.textContent = text; };

  function esc(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  const QA_IDLE =
    "Waiting for a question…\n\nQuestions and answers stay in this pane. Scroll to review every turn.";

  function messageText(m) {
    const c = m && m.content;
    if (Array.isArray(c)) {
      return c
        .map((part) => (part && part.type === "text" ? part.text : "[Image]"))
        .filter(Boolean)
        .join("\n");
    }
    return String(c || "");
  }

  function stickToBottom(el) {
    if (!el) return true;
    return el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  }

  function qaBlockHtml(kind, body, extraClass) {
    const kicker = kind === "q" ? "Question" : "Answer";
    const extra = extraClass ? ` ${extraClass}` : "";
    return `<article class="qa-block ${kind}${extra}"><div class="qa-kicker">${kicker}</div><div class="qa-body">${esc(body)}</div></article>`;
  }

  function renderQaLog(container, messages, extras = {}) {
    if (!container) return;
    const skipSystem = extras.skipSystem !== false;
    const blocks = [];
    for (const m of messages || []) {
      if (skipSystem && m.role === "system") continue;
      const body = messageText(m).trim();
      if (!body) continue;
      if (m.role === "user") blocks.push({ kind: "q", body });
      else if (m.role === "assistant") blocks.push({ kind: "a", body });
    }
    const liveQ = String(extras.liveQuestion || "").trim();
    const liveA = String(extras.liveAnswer || "").trim();
    const lastQ = [...blocks].reverse().find((b) => b.kind === "q");
    if (liveQ && liveQ !== "Listening…") {
      const last = blocks[blocks.length - 1];
      if (last && last.kind === "q") {
        last.body = liveQ;
        last.live = !!extras.live;
      } else if (lastQ && lastQ.body.trim() === liveQ) {
        lastQ.live = !!extras.live;
      } else {
        blocks.push({ kind: "q", body: liveQ, live: !!extras.live });
      }
    }
    if (liveA) {
      const last = blocks[blocks.length - 1];
      if (last && last.kind === "a") {
        last.body = liveA;
        last.streaming = !!extras.streaming;
      } else if (last && last.kind === "q") {
        blocks.push({ kind: "a", body: liveA, streaming: !!extras.streaming });
      }
    }
    const html = blocks.length
      ? blocks.map((b) => qaBlockHtml(b.kind, b.body, [b.live ? "is-live" : "", b.streaming ? "streaming" : ""].filter(Boolean).join(" "))).join("")
      : `<div class="qa-idle">${esc(extras.idle || QA_IDLE)}</div>`;
    if (container.dataset.qaHtml === html) {
      container.scrollTop = container.scrollHeight;
      return;
    }
    container.dataset.qaHtml = html;
    container.innerHTML = html;
    const lastQEl = container.querySelector(".qa-block.q:last-of-type .qa-body");
    if (lastQEl && container.id === "live-answer") lastQEl.id = "live-transcript-body";
    container.scrollTop = container.scrollHeight;
  }

  function renderMessages(container, messages, { skipSystem = true } = {}) {
    renderQaLog(container, messages, {
      skipSystem,
      liveQuestion: "",
      liveAnswer: "",
      idle: "No messages yet. Listen, type, or pick a prompt.",
    });
  }

  function renderLiveLog() {
    const el = $("live-answer");
    if (!el) return;
    const liveQ = (state.qText || "").trim();
    const liveA = state.liveAnswer || "";
    const lastBlock = el.querySelector(".qa-block:last-of-type");
    const lastQBody = el.querySelector(".qa-block.q:last-of-type .qa-body");
    const lastABody = el.querySelector(".qa-block.a:last-of-type .qa-body");
    const canPatch = !!lastBlock && !el.querySelector(".qa-idle");
    if (canPatch && liveQ && liveQ !== "Listening…" && lastBlock.classList.contains("q") && lastQBody) {
      if (lastQBody.textContent !== liveQ) lastQBody.textContent = liveQ;
      if (liveA) {
        if (lastBlock.nextElementSibling && lastBlock.nextElementSibling.classList.contains("a")) {
          const body = lastBlock.nextElementSibling.querySelector(".qa-body");
          if (body && shouldApplyAnswer(body.textContent || "", liveA)) body.textContent = liveA;
        } else {
          lastBlock.insertAdjacentHTML("afterend", qaBlockHtml("a", liveA, state.answering ? "streaming" : ""));
        }
      }
      el.scrollTop = el.scrollHeight;
      return;
    }
    if (canPatch && lastBlock.classList.contains("a") && lastABody && liveA) {
      if (liveQ && lastQBody && !sameQuestion(lastQBody.textContent || "", liveQ)) {
        lastBlock.insertAdjacentHTML("afterend", qaBlockHtml("q", liveQ, "is-live"));
        if (liveA) {
          el.insertAdjacentHTML("beforeend", qaBlockHtml("a", liveA, state.answering ? "streaming" : ""));
        }
        el.scrollTop = el.scrollHeight;
        return;
      }
      if (shouldApplyAnswer(lastABody.textContent || "", liveA)) lastABody.textContent = liveA;
      if (liveQ && lastQBody && lastQBody.textContent !== liveQ) lastQBody.textContent = liveQ;
      el.scrollTop = el.scrollHeight;
      return;
    }
    renderQaLog(el, state.messages, {
      liveQuestion: liveQ,
      liveAnswer: liveA,
      live: !!state.liveListening || !!state.liveCaptionLive,
      streaming: !!state.answering,
    });
  }

  function resetQuestionType() {
    const qt = state.qType;
    if (qt.timer) {
      clearInterval(qt.timer);
      qt.timer = null;
    }
    qt.shown = "";
    qt.want = "";
  }

  function snapQuestion() {
    const qt = state.qType;
    if (!qt.want) return;
    if (qt.timer) {
      clearInterval(qt.timer);
      qt.timer = null;
    }
    qt.shown = qt.want;
    commitQuestionPaint(qt.shown, qt.where);
  }

  function commitQuestionPaint(text, where) {
    if (where === "studio") {
      state.studioLiveQ = text;
      const box = $("messages");
      renderQaLog(box, state.messages, { liveQuestion: text, live: true, idle: "No messages yet." });
      if (box) box.scrollTop = box.scrollHeight;
      setStatus($("status-line"), "Hearing question…");
      return;
    }
    state.qText = text;
    state.qAt = Date.now();
    const caption = $("live-caption-text");
    if (caption) caption.textContent = text;
    $("live-question-caption")?.classList.toggle("is-live", true);
    state.liveCaptionLive = true;
    renderLiveLog();
    if (window.OverlayPrivacy) {
      clearTimeout(state.qSync);
      state.qSync = setTimeout(() => {
        OverlayPrivacy.syncLiveState({ transcript: text, status: "Hearing question…" });
      }, 40);
    }
    setStatus($("live-status"), "Hearing question…");
  }

  function ingestQuestion(next, where) {
    const Q = window.QuestionText;
    const want = String(next || "").trim();
    if (!want || want === "Listening…") return;
    const qt = state.qType;
    qt.want = want;
    qt.where = where || qt.where || "live";
    const shown = qt.shown || "";
    const rest = want.startsWith(shown) ? want.slice(shown.length) : want;
    const restWords = rest.trim().split(/\s+/).filter(Boolean).length;
    const smallStep = rest.length <= 18 || restWords <= 1;
    if (shown && want.startsWith(shown) && smallStep) {
      qt.shown = want;
      if (qt.timer) {
        clearInterval(qt.timer);
        qt.timer = null;
      }
      commitQuestionPaint(qt.shown, qt.where);
      return;
    }
    if (!shown && restWords <= 1) {
      qt.shown = want;
      commitQuestionPaint(qt.shown, qt.where);
      return;
    }
    if (!qt.timer) qt.timer = setInterval(flushQuestionWords, 42);
    flushQuestionWords();
  }

  function flushQuestionWords() {
    const Q = window.QuestionText;
    const qt = state.qType;
    const chunk = Q && Q.nextWordChunk ? Q.nextWordChunk(qt.shown, qt.want) : null;
    if (!chunk) {
      if (qt.timer) {
        clearInterval(qt.timer);
        qt.timer = null;
      }
      return;
    }
    if (qt.want && qt.shown && !qt.want.startsWith(qt.shown) && !(qt.shown + chunk === qt.want || qt.want.startsWith(qt.shown + chunk))) {
      qt.shown = chunk;
    } else {
      qt.shown = (qt.shown || "") + chunk;
    }
    commitQuestionPaint(qt.shown, qt.where);
    if (qt.shown === qt.want && qt.timer) {
      clearInterval(qt.timer);
      qt.timer = null;
    }
  }

  function appendStreaming(container, role, text) {
    let node = container.querySelector(".qa-block.streaming, .msg.streaming");
    if (!node) {
      node = document.createElement("article");
      const kind = role === "user" ? "q" : "a";
      node.className = `qa-block ${kind} streaming`;
      node.innerHTML = `<div class="qa-kicker">${role === "user" ? "Question" : "Answer"}</div><div class="qa-body"></div>`;
      container.appendChild(node);
    }
    const body = node.querySelector(".qa-body, .body");
    if (body) body.textContent = text;
    container.scrollTop = container.scrollHeight;
  }

  function finishStreaming(container) {
    const node = container.querySelector(".qa-block.streaming, .msg.streaming");
    if (node) node.classList.remove("streaming");
  }

  async function refreshStatus() {
    const s = await API.get("/api/status");
    state.status = s;
    const pill = $("conn-status");
    if (s.api_key_configured) {
      pill.textContent = "API ready";
      pill.className = "pill pill-ok";
    } else {
      pill.textContent = "Set OPENAI_API_KEY";
      pill.className = "pill pill-bad";
    }
    $("model-pill").textContent = s.default_model || "—";
    fillModelSelects(s.models || [], s.default_model);
  }

  function fillModelSelects(models, selected) {
    for (const id of ["select-model", "live-model", "create-model"]) {
      const el = $(id);
      if (!el) continue;
      el.innerHTML = models.map((m) => `<option value="${esc(m)}">${esc(m)}</option>`).join("");
      if (selected) el.value = selected;
    }
  }

  function showMode(mode) {
    state.currentMode = mode;
    document.body.dataset.mode = mode;
    const viewId =
      mode === "studio" ? "view-studio" :
      mode === "live" ? "view-live" :
      mode === "resumes" || mode === "documents" ? "view-library" :
      "view-sessions";
    document.querySelectorAll(".view").forEach((v) => v.classList.add("hidden"));
    $(viewId)?.classList.remove("hidden");
    document.querySelectorAll(".mode-tab").forEach((t) => {
      t.classList.toggle("active", t.dataset.mode === mode || (viewId === "view-sessions" && t.dataset.mode === "sessions"));
    });
    document.querySelectorAll(".nav-item[data-mode]").forEach((t) => {
      t.classList.toggle("active", t.dataset.mode === mode);
    });
    if ((mode === "resumes" || mode === "documents") && window.SessionsUI) {
      SessionsUI.showLibrary(mode);
    }
  }

  function fmtClock(total) {
    const s = Math.max(0, Math.floor(total));
    const m = Math.floor(s / 60);
    const r = s % 60;
    return r ? `${m}m ${r}s` : `${m}m`;
  }

  function startTimer() {
    stopTimer();
    state.timerStarted = Date.now();
    const tick = () => {
      const el = $("live-timer");
      if (el) el.textContent = fmtClock((Date.now() - state.timerStarted) / 1000);
    };
    tick();
    state.timerHandle = setInterval(tick, 1000);
    if (window.SessionsUI) SessionsUI.setLiveBadge(true);
  }

  function stopTimer() {
    if (state.timerHandle) clearInterval(state.timerHandle);
    state.timerHandle = null;
  }

  function renderBubbles() {
    const root = $("live-bubbles");
    if (!root) return;
    if (!state.bubbles.length) {
      root.innerHTML = `<p class="muted">No messages yet. Speak, or click Answer after a question is heard.</p>`;
      return;
    }
    root.innerHTML = state.bubbles
      .map((b) => {
        const who = b.role === "you" ? "You" : "Interviewer";
        const extra = b.partial ? " partial" : "";
        return `<div class="bubble ${esc(b.role)}${extra}">${esc(b.text)}<span class="who">${who} · ${esc(b.clock || "00:00")}</span></div>`;
      })
      .join("");
    root.scrollTop = root.scrollHeight;
  }

  const LEFT_CAPTION_IDLE = "Waiting for the interviewer…";
  const OVERLAY_QUESTION_IDLE = "Captions appear as the interviewer speaks.";

  function showLiveCaption(text, { live = false } = {}) {
    const Q = window.QuestionText;
    const cleaned = Q ? Q.collapseSnowball(text || "") : String(text || "").trim();
    const caption = $("live-caption-text");
    // Left pane: live line only. Committed Q&A lives in the overlay log.
    if (caption) caption.textContent = live && cleaned ? cleaned : LEFT_CAPTION_IDLE;
    $("live-question-caption")?.classList.toggle("is-live", !!live);
    state.liveCaptionLive = !!live;
    renderLiveLog();
  }

  function sameQuestion(a, b) {
    const Q = window.QuestionText;
    const x = String(a || "").trim();
    const y = String(b || "").trim();
    if (!x || !y) return false;
    if (x === y) return true;
    if (Q && Q.isCloseEnoughForPrefetch(x, y)) return true;
    const xl = x.toLowerCase();
    const yl = y.toLowerCase();
    return xl.includes(yl) || yl.includes(xl);
  }

  function shouldApplyAnswer(prev, nxt) {
    if (nxt === prev) return false;
    if (!nxt && prev) return false;
    if (prev && nxt && prev.startsWith(nxt) && prev.length > nxt.length + 12) return false;
    return true;
  }

  function setLiveAnswer(text, { restart = false } = {}) {
    const next = String(text || "");
    const prev = state.liveAnswer || "";
    if (!restart && !shouldApplyAnswer(prev, next)) return;
    if (next) snapQuestion();
    state.liveAnswer = restart && !next ? "" : next;
    renderLiveLog();
    if (window.OverlayPrivacy) {
      clearTimeout(state.answerSync);
      state.answerSync = setTimeout(() => {
        OverlayPrivacy.syncLiveState({ answer: state.liveAnswer || next });
      }, 100);
    }
  }

  function startBrowserCaptions() {
    if (state.sessionConnection === "mock") return;
    if (!window.LiveCaptioner) return;
    if (!state.captioner) state.captioner = new LiveCaptioner();
    const lang = $("live-room-lang")?.value || $("live-lang")?.value || "en";
    state.captioner.start({
      lang,
      onText: (text) => applyBrowserCaption(text),
    });
  }

  function stopBrowserCaptions() {
    try { state.captioner?.stop(); } catch (_) {}
  }

  function applyBrowserCaption(text) {
    if (state.liveSttOk) return;
    if (!text || !state.liveListening || state.sessionConnection === "mock") return;
    const Q = window.QuestionText;
    const incoming = Q ? Q.collapseSnowball(text) : text;
    const next = Q ? Q.coalesceTranscript(state.qText, incoming) : incoming;
    const shown = Q ? Q.collapseSnowball(next) : next;
    if (!shown) return;
    ingestQuestion(shown, "live");
    upsertInterviewer(shown, { commit: false });
    // Live captions are preview only — never start or refresh an answer.
  }

  function addBubble(role, text) {
    if (!text) return;
    const clock = fmtClock((Date.now() - (state.timerStarted || Date.now())) / 1000);
    state.bubbles.push({ role, text, clock, partial: false });
    if (role === "interviewer") {
      state.lastQuestion = text;
      showLiveCaption(text, { live: false });
    }
    renderBubbles();
    if (state.sessionId) {
      API.post(`/api/sessions/${state.sessionId}/transcript`, {
        role,
        text,
        t: Math.floor((Date.now() - (state.timerStarted || Date.now())) / 1000),
      }).catch(() => {});
    }
  }

  function resetQuestionAssembly() {
    if (state.qHold) {
      clearTimeout(state.qHold);
      state.qHold = null;
    }
    state.qText = "";
    state.qAt = 0;
    state.qPartialBusy = false;
    state.qPartialQueued = null;
    state.queuedUtterance = null;
    state.answering = false;
    state.answerGen += 1;
    state.prefetch = { gen: state.prefetch.gen + 1, text: "", acc: "", inflight: false, done: false };
  }

  function upsertInterviewer(text, { commit = false } = {}) {
    if (!text) return;
    const Q = window.QuestionText;
    const shown = Q ? Q.collapseSnowball(text) : String(text).trim();
    if (!shown) return;
    const clock = fmtClock((Date.now() - (state.timerStarted || Date.now())) / 1000);
    state.lastQuestion = shown;
    showLiveCaption(shown, { live: !commit });
    if (commit) {
      const last = state.bubbles[state.bubbles.length - 1];
      if (last && last.role === "interviewer" && (last.partial || sameQuestion(last.text, shown))) {
        last.text = shown;
        last.clock = clock;
        last.partial = false;
      } else {
        const dup = state.bubbles.some(
          (b) => b.role === "interviewer" && !b.partial && sameQuestion(b.text, shown)
        );
        if (!dup) state.bubbles.push({ role: "interviewer", text: shown, clock, partial: false });
      }
      renderBubbles();
      if (state.sessionId) {
        API.post(`/api/sessions/${state.sessionId}/transcript`, {
          role: "interviewer",
          text: shown,
          t: Math.floor((Date.now() - (state.timerStarted || Date.now())) / 1000),
        }).catch(() => {});
      }
    }
    if (window.OverlayPrivacy) OverlayPrivacy.syncLiveState({ transcript: shown });
  }

  async function transcribeBlob(blob, { prompt = "" } = {}) {
    if (!blob || blob.size < 400 || !state.liveId) return { text: "", looksLikeQuestion: false };
    const fd = new FormData();
    fd.append("engine_id", state.liveId);
    const wav = (blob.type || "").includes("wav");
    fd.append("file", blob, wav ? "live.wav" : "live.webm");
    if (prompt) fd.append("prompt", prompt);
    try {
      const res = await fetch("/api/stt", { method: "POST", body: fd });
      const data = await res.json();
      return {
        text: (data.text || "").trim(),
        looksLikeQuestion: !!data.looks_like_question,
      };
    } catch (_) {
      return { text: "", looksLikeQuestion: false };
    }
  }

  function assembleFragment(text) {
    const Q = window.QuestionText;
    if (!Q || !text) return text || state.qText;
    const prev = state.qText || "";
    if (!prev) {
      state.qText = Q.collapseSnowball(text);
      state.qAt = Date.now();
      return state.qText;
    }
    state.qText = Q.collapseSnowball(Q.coalesceTranscript(prev, text));
    state.qAt = Date.now();
    return state.qText;
  }

  function autoAnswerLive() {
    return !!(state.liveAuto || state.sessionConnection === "real");
  }

  function cancelPrematureAnswer() {
    if (!state.answering && !state.qHold) return;
    state.answerGen += 1;
    state.answering = false;
    if (state.liveId) {
      API.post(`/api/engines/${state.liveId}/cancel`).catch(() => {});
    }
    setLiveAnswer("", { restart: true });
    setStatus($("live-status"), "Hearing rest of question…");
  }

  function scheduleAnswerCommit({ autoAnswer = false, force = false } = {}) {
    const Q = window.QuestionText;
    if (state.qHold) {
      clearTimeout(state.qHold);
      state.qHold = null;
    }
    const text = (state.qText || "").trim();
    if (!text) return;
    if (force) {
      finalizeAssembled(text, { autoAnswer: true, force: true }).catch(() => {});
      return;
    }
    const hold = Q ? Q.answerHoldMs(text) : 1600;
    state.qHold = setTimeout(() => {
      state.qHold = null;
      const latest = (state.qText || text).trim();
      const quiet = Date.now() - (state.qAt || 0);
      if (!latest) return;
      if (Q && !Q.questionReadyToAnswer(latest, quiet, false)) {
        if (quiet < 4000) {
          scheduleAnswerCommit({ autoAnswer });
          return;
        }
      }
      finalizeAssembled(latest, { autoAnswer, force: false }).catch(() => {});
    }, hold);
  }

  async function finalizeAssembled(text, { autoAnswer = false, force = false } = {}) {
    const Q = window.QuestionText;
    if (state.qHold) {
      clearTimeout(state.qHold);
      state.qHold = null;
    }
    const full = (text || state.qText || "").trim();
    if (!full) return;
    if (state.answering) return;
    if (!force && Q && !Q.questionReadyToAnswer(full, Date.now() - (state.qAt || 0), false)) {
      scheduleAnswerCommit({ autoAnswer });
      return;
    }
    upsertInterviewer(full, { commit: true });
    state.lastQuestion = full;
    const shouldAnswer = !!(force || autoAnswer);
    const isQ = !Q || Q.looksLikeQuestion(full) || force;
    if (!shouldAnswer) {
      setStatus($("live-status"), isQ ? "Question heard — press ` or Stop & Process" : "Heard speech");
      state.qText = "";
      return;
    }
    if (!isQ) {
      setStatus($("live-status"), "Heard speech (not a question) — press ` to answer anyway");
      return;
    }
    await answerLastQuestion();
    state.qText = "";
  }

  async function ingestPartial(blob) {
    if (!state.liveListening || state.answering) return;
    if (state.qPartialBusy) {
      state.qPartialQueued = blob;
      return;
    }
    state.qPartialBusy = true;
    try {
      const { text } = await transcribeBlob(blob);
      if (!text || !state.liveListening) return;
      const Q = window.QuestionText;
      const shown = Q ? Q.collapseSnowball(text) : text;
      const prev = state.qText || "";
      // Full-buffer snapshot: replace the live line, like the desktop Live Question.
      if (!prev || shown.length >= prev.length * 0.85) {
        state.qText = shown;
      } else {
        state.qText = Q ? Q.collapseSnowball(Q.coalesceTranscript(prev, shown)) : shown;
      }
      state.qAt = Date.now();
      upsertInterviewer(state.qText, { commit: false });
      showLiveCaption(state.qText, { live: true });
      renderLiveLog();
      setStatus($("live-status"), "Hearing question…");
    } finally {
      state.qPartialBusy = false;
      const queued = state.qPartialQueued;
      state.qPartialQueued = null;
      if (queued && state.liveListening) ingestPartial(queued);
    }
  }

  async function ingestUtterance(blob, { force = false, autoAnswer = false } = {}) {
    if (state.answering && !force) {
      state.queuedUtterance = blob;
      return;
    }
    const preview = state.qText || "";
    const { text } = await transcribeBlob(blob, { prompt: preview });
    const Q = window.QuestionText;
    const raw = (text || preview || "").trim();
    const question = Q ? Q.collapseSnowball(raw) : raw;
    if (!question) {
      setStatus($("live-status"), "Listening…");
      return;
    }
    if (state.sessionConnection === "mock" && !force) {
      addBubble("you", question);
      return;
    }
    if (!force && state.lastQuestion && sameQuestion(question, state.lastQuestion)) {
      setStatus($("live-status"), "Listening…");
      return;
    }
    state.qText = question;
    state.qAt = Date.now();
    await finalizeAssembled(question, {
      autoAnswer: !!(force || autoAnswer),
      force: true,
    });
  }

  // ── Studio bootstrap ────────────────────────────────────────────

  async function initStudio() {
    const eng = await API.post("/api/engines", { kind: "studio" });
    state.studioId = eng.engine_id;
    state.messages = eng.messages || [];
    state.bookmarks = eng.bookmarks || [];
    renderMessages($("messages"), state.messages);
    renderBookmarks();
    await Promise.all([refreshPrompts(), refreshChats(), refreshProfiles()]);
    syncModeButtons(eng);
    setStatus($("status-line"), "Studio ready");
  }

  function syncModeButtons(eng) {
    if (eng.answer_mode) $("btn-cycle-mode").textContent = `Mode: ${eng.answer_mode}`;
    if (typeof eng.optimization_mode === "boolean") {
      $("btn-fast").textContent = eng.optimization_mode ? "Fast" : "Full";
    }
    if (eng.model && $("select-model")) $("select-model").value = eng.model;
  }

  async function refreshPrompts() {
    const data = await API.get("/api/prompts");
    const root = $("prompt-tree");
    root.innerHTML = "";
    (data.tabs || []).forEach((tab, ti) => {
      const wrap = document.createElement("div");
      wrap.className = "tree-tab";
      wrap.innerHTML = `<div class="tree-tab-name">${esc(tab.name || "Tab")}</div>`;
      (tab.subTabs || []).forEach((sub, si) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "tree-sub";
        btn.textContent = sub.name || `Prompt ${si + 1}`;
        btn.onclick = () => sendPromptSubtab(ti, si);
        wrap.appendChild(btn);
      });
      const add = document.createElement("button");
      add.type = "button";
      add.className = "tree-sub";
      add.style.color = "var(--muted)";
      add.textContent = "+ subtab";
      add.onclick = async () => {
        const name = prompt("Subtab name?");
        if (!name) return;
        const body = prompt("Prompt body?", "") || "";
        await API.post("/api/prompts/subtabs", { tab_index: ti, name, text_input: body, prompt: body });
        refreshPrompts();
      };
      wrap.appendChild(add);
      root.appendChild(wrap);
    });
  }

  async function sendPromptSubtab(tabIndex, subIndex) {
    const info = await API.get(`/api/prompts/subtab-body?tab_index=${tabIndex}&subtab_index=${subIndex}`);
    if (!info.body) return;
    $("input").value = info.body;
    await sendChat();
  }

  async function refreshProfiles() {
    const data = await API.get("/api/profiles");
    const root = $("profile-list");
    root.innerHTML = "";
    (data.names || []).forEach((name) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "list-item";
      btn.innerHTML = `<span>${esc(name)}</span>`;
      btn.onclick = async () => {
        const ids = (data.profiles[name] || []);
        for (const sid of ids) {
          const m = /^sub_(\d+)_(\d+)$/.exec(sid);
          if (!m) continue;
          await sendPromptSubtab(+m[1], +m[2]);
        }
      };
      root.appendChild(btn);
    });
  }

  async function refreshChats() {
    const data = await API.get("/api/chats");
    const root = $("chat-list");
    root.innerHTML = "";
    (data.sessions || []).forEach((s) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "list-item";
      btn.innerHTML = `<span>${esc(s.title)}</span><span class="meta">${s.message_count}</span>`;
      btn.onclick = async () => {
        const loaded = await API.post("/api/chats/load", { engine_id: state.studioId, index: s.index });
        state.messages = loaded.messages || [];
        state.bookmarks = loaded.bookmarks || [];
        renderMessages($("messages"), state.messages);
        renderBookmarks();
        setStatus($("status-line"), `Loaded: ${loaded.title}`);
      };
      root.appendChild(btn);
    });
  }

  function renderBookmarks() {
    const root = $("bookmark-list");
    root.innerHTML = "";
    (state.bookmarks || []).forEach((b, i) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "list-item";
      const preview = Array.isArray(b) ? b[1] : String(b);
      btn.innerHTML = `<span>${esc(preview || `Bookmark ${i + 1}`)}</span>`;
      btn.onclick = () => {
        $("messages").scrollTop = 0;
      };
      btn.ondblclick = async () => {
        const res = await API.del(`/api/bookmarks/${state.studioId}/${i}`);
        state.bookmarks = res.bookmarks || [];
        renderBookmarks();
      };
      root.appendChild(btn);
    });
  }

  async function sendChat(textOverride) {
    const text = (textOverride != null ? textOverride : $("input").value).trim();
    const images = state.pendingImages.slice();
    if (!text && !images.length) return;
    $("input").value = "";
    state.pendingImages = [];
    renderPending();
    setStatus($("status-line"), "Streaming…");
    let acc = "";
    try {
      await API.streamPost(
        "/api/chat/stream",
        { engine_id: state.studioId, text, image_data_urls: images },
        {
          onEvent: (ev) => {
            if (ev.type === "delta") {
              acc += ev.text || "";
              appendStreaming($("messages"), "assistant", acc);
            }
            if (ev.type === "done" && ev.messages) {
              state.messages = ev.messages;
              finishStreaming($("messages"));
              renderMessages($("messages"), state.messages);
              refreshChats();
            }
            if (ev.type === "error") setStatus($("status-line"), ev.message || "Error");
          },
        }
      );
      setStatus($("status-line"), "Ready");
    } catch (e) {
      setStatus($("status-line"), e.message || String(e));
    }
  }

  function renderPending() {
    const root = $("pending-images");
    root.innerHTML = state.pendingImages
      .map((url, i) => `<img src="${url}" alt="pending ${i}" title="Click to remove" data-i="${i}" />`)
      .join("");
    root.querySelectorAll("img").forEach((img) => {
      img.onclick = () => {
        state.pendingImages.splice(+img.dataset.i, 1);
        renderPending();
      };
    });
  }

  function audioKindLabel(kind) {
    if (kind === "call") return "Hearing meeting/tab audio";
    if (kind === "loopback") return "Hearing BlackHole / VB-Cable (system audio)";
    if (kind === "mic") return "Microphone on — hearing YouTube/call playback like Mock";
    return "Not connected";
  }

  async function grantLiveAudio() {
    const statusEl = $("audio-grant-status");
    try {
      setStatus(statusEl, "Waiting for microphone permission…");
      if ($("audio-source")) $("audio-source").value = "mic";
      const kind = await state.liveMic.acquireMic({ loopbackFirst: true });
      setStatus(statusEl, audioKindLabel(kind));
      setStatus($("live-status"), audioKindLabel(kind));
      return kind;
    } catch (e) {
      setStatus(statusEl, "Permission denied. Allow Microphone in the browser prompt.");
      throw e;
    }
  }

  function acceptListenToggle() {
    const now = Date.now();
    if (now - (state.lastListenToggleAt || 0) < 400) return false;
    state.lastListenToggleAt = now;
    return true;
  }

  function markStudioListen(on) {
    const btn = $("btn-listen");
    state.listening = !!on;
    if (!btn) return;
    btn.classList.toggle("active-listen", !!on);
    btn.textContent = on ? "Stop & Process" : "Listen";
  }

  async function startDisplayCaptions() {
    if (state._displayCaptions) return;
    state._displayCaptions = true;
    try {
      if (!state.liveMic.live) await grantLiveAudio();
      state.liveMic.startCaptionTap();
      startLiveStt();
      startBrowserCaptions();
    } catch (_) {
      state._displayCaptions = false;
    }
  }

  function stopDisplayCaptions() {
    state._displayCaptions = false;
    stopLiveStt();
    stopBrowserCaptions();
    try { state.liveMic._questionOpen = false; } catch (_) {}
  }

  function startStudioListenCaptions() {
    stopStudioListenCaptions();
    const box = $("messages");
    const Q = window.QuestionText;
    let acc = "";
    const paint = (text) => {
      const shown = Q ? Q.collapseSnowball(text) : text;
      if (!shown) return;
      ingestQuestion(shown, "studio");
    };
    if (window.LiveTranscribeSocket && state.studioId) {
      state.studioStt = new LiveTranscribeSocket({
        engineId: state.studioId,
        lang: "en",
        onDelta: (piece) => {
          acc += piece || "";
          paint(acc);
        },
        onCompleted: (full) => {
          acc = full || acc;
          paint(acc);
        },
      });
      state.studioStt.connect();
      try { state.mic.startCaptionTap(); } catch (_) {}
      state.mic.onPcmStream = (samples) => {
        const rate = (state.mic.ctx && state.mic.ctx.sampleRate) || 48000;
        state.studioStt?.pushFloat32(samples, rate);
      };
    }
  }

  function stopStudioListenCaptions() {
    try { state.mic.onPcmStream = null; } catch (_) {}
    try { state.studioStt?.close(); } catch (_) {}
    state.studioStt = null;
  }

  async function pollStudioAfterListen() {
    const box = $("messages");
    const id = state.studioId;
    if (!id || !box) return;
    let n = 0;
    const tick = async () => {
      n += 1;
      try {
        const snap = await API.get(`/api/engines/${id}`);
        state.messages = snap.messages || [];
        const ov = (snap.meta && snap.meta.overlay) || {};
        if (ov.transcript && ov.transcript !== "Listening…") ingestQuestion(ov.transcript, "studio");
        if (ov.answer) snapQuestion();
        renderQaLog(box, state.messages, {
          liveQuestion: state.qType.shown || state.studioLiveQ || "",
          liveAnswer: ov.answer || snap.partial || "",
          streaming: /writing|answer/i.test(String(ov.status || "")),
          idle: "No messages yet.",
        });
        box.scrollTop = box.scrollHeight;
        const busy = /transcrib|answer|writing/i.test(String(ov.status || ""));
        if (busy && n < 90) setTimeout(tick, 180);
        else setStatus($("status-line"), ov.status || "Ready");
      } catch (_) {}
    };
    tick();
  }

  function routeListenToggle(cmd) {
    // Overlay / OS-global ` are handled by the Python BlackHole recorder.
    // Only paint the UI here — a second MediaRecorder would double-capture.
    const live = !!state.liveId;
    if (cmd === "listen") {
      if (live) {
        setListenButtons(true);
        resetQuestionType();
        state.qText = state.qText || "Listening…";
        state.liveAnswer = "";
        setStatus($("live-status"), "Listening to internal audio…");
        renderLiveLog();
        startDisplayCaptions();
      } else if (state.studioId) {
        markStudioListen(true);
        setStatus($("status-line"), "Listening to internal audio…");
        resetQuestionType();
        renderQaLog($("messages"), state.messages, { liveQuestion: "Listening…", live: true });
        startStudioListenCaptions();
      }
      return;
    }
    if (cmd === "stop_listen") {
      if (live) {
        setListenButtons(false);
        stopDisplayCaptions();
        setStatus($("live-status"), "Transcribing…");
        hydrateLiveLog();
      } else if (state.studioId) {
        markStudioListen(false);
        stopStudioListenCaptions();
        setStatus($("status-line"), "Transcribing…");
        pollStudioAfterListen();
      }
      return;
    }
    if (live) {
      if (state.liveListening) {
        setListenButtons(false);
        stopDisplayCaptions();
        setStatus($("live-status"), "Transcribing…");
        hydrateLiveLog();
      } else {
        setListenButtons(true);
        resetQuestionType();
        state.qText = "Listening…";
        state.liveAnswer = "";
        setStatus($("live-status"), "Listening to internal audio…");
        renderLiveLog();
        startDisplayCaptions();
      }
      return;
    }
    if (state.studioId) {
      markStudioListen(!state.listening);
      setStatus($("status-line"), state.listening ? "Listening to internal audio…" : "Transcribing…");
      if (state.listening) {
        resetQuestionType();
        renderQaLog($("messages"), state.messages, { liveQuestion: "Listening…", live: true });
        startStudioListenCaptions();
      } else {
        stopStudioListenCaptions();
        pollStudioAfterListen();
      }
      return;
    }
    markStudioListen(!state.listening);
  }

  async function toggleNativeListen(engineId) {
    if (!engineId) return false;
    if (!(window.OverlayPrivacy && OverlayPrivacy.isNative && OverlayPrivacy.isNative())) return false;
    await API.post("/api/privacy/command", { engine_id: engineId, command: "toggle_listen" });
    return true;
  }

  async function toggleListen(opts = {}) {
    if (!opts.skipDebounce && !acceptListenToggle()) return;
    if (await toggleNativeListen(state.studioId)) return;
    const micOn = !!(state.mic && state.mic.recording);
    if (state.listening && !micOn) {
      await API.post("/api/privacy/command", { engine_id: state.studioId, command: "stop_listen" });
      markStudioListen(false);
      setStatus($("status-line"), "Transcribing…");
      return;
    }
    const btn = $("btn-listen");
    if (!state.listening) {
      try {
        if (!state.mic.live) await state.mic.acquirePreferred();
        await state.mic.startHold();
        state.listening = true;
        btn.classList.add("active-listen");
        btn.textContent = "Stop & Process";
        setStatus($("status-line"), "Listening to internal audio…");
        resetQuestionType();
        renderQaLog($("messages"), state.messages, { liveQuestion: "Listening…", live: true });
        startStudioListenCaptions();
      } catch (e) {
        setStatus($("status-line"), "Mic permission denied");
      }
      return;
    }
    btn.classList.remove("active-listen");
    btn.textContent = "Listen";
    state.listening = false;
    stopStudioListenCaptions();
    setStatus($("status-line"), "Transcribing…");
    const blob = await state.mic.stop();
    if (!blob || blob.size < 500) {
      setStatus($("status-line"), "No audio captured");
      return;
    }
    const fd = new FormData();
    fd.append("engine_id", state.studioId);
    fd.append("force", "true");
    fd.append("file", blob, "listen.webm");
    let acc = "";
    const box = $("messages");
    try {
      await API.streamForm("/api/listen/stream", fd, {
        onEvent: (ev) => {
          if (ev.type === "transcript") {
            ingestQuestion(ev.text, "studio");
            setStatus($("status-line"), `Q: ${ev.text}`);
          }
          if (ev.type === "delta") {
            snapQuestion();
            acc += ev.text || "";
            appendStreaming(box, "assistant", acc);
            box.scrollTop = box.scrollHeight;
          }
          if (ev.type === "done" && ev.messages) {
            state.messages = ev.messages;
            finishStreaming(box);
            renderMessages(box, state.messages);
            box.scrollTop = box.scrollHeight;
            refreshChats();
          }
        },
      });
      setStatus($("status-line"), "Ready");
    } catch (e) {
      setStatus($("status-line"), e.message || String(e));
    }
  }

  async function analyzeScreen(engineId, answerEl, statusEl) {
    setStatus(statusEl, "Pick a screen/tab…");
    try {
      const blob = await captureScreenPng();
      if (!blob) return;
      const fd = new FormData();
      fd.append("engine_id", engineId);
      fd.append("file", blob, "screen.png");
      let acc = "";
      await API.streamForm("/api/screen/analyze", fd, {
        onEvent: (ev) => {
          if (ev.type === "delta") {
            acc += ev.text || "";
            if (answerEl === $("messages")) appendStreaming(answerEl, "assistant", acc);
            else if (answerEl === $("live-answer")) setLiveAnswer(acc);
            else answerEl.textContent = acc;
          }
          if (ev.type === "done") {
            if (ev.messages) state.messages = ev.messages;
            if (answerEl === $("messages")) {
              finishStreaming(answerEl);
              renderMessages(answerEl, state.messages);
            } else if (answerEl === $("live-answer")) {
              state.liveAnswer = acc || state.liveAnswer;
              state.answering = false;
              renderLiveLog();
            }
          }
        },
      });
      setStatus(statusEl, "Ready");
    } catch (e) {
      setStatus(statusEl, e.message || String(e));
    }
  }

  // ── Live ────────────────────────────────────────────────────────

  async function hydrateLiveLog() {
    if (!state.liveId) {
      renderLiveLog();
      return;
    }
    if (state.answering && state.liveMic && state.liveMic.recording) return;
    try {
      const snap = await API.get(`/api/engines/${state.liveId}`);
      state.messages = snap.messages || [];
      const ov = (snap.meta && snap.meta.overlay) || {};
      if (ov.transcript && ov.transcript !== "Listening…") {
        const typed = (state.qType.shown || "").trim();
        if (!typed || ov.transcript.length >= typed.length) ingestQuestion(ov.transcript, "live");
      }
      if (ov.answer && shouldApplyAnswer(state.liveAnswer || "", ov.answer)) {
        snapQuestion();
        state.liveAnswer = ov.answer;
      } else if (ov.answer && ov.answer === (state.liveAnswer || "")) {
        state.liveAnswer = ov.answer;
      }
      if (!state.liveListening) {
        const lastUser = [...state.messages].reverse().find((m) => m.role === "user");
        const lastAsst = [...state.messages].reverse().find((m) => m.role === "assistant");
        const busy = /transcrib|answer|writing/i.test(String(ov.status || ""));
        const typing = !!state.qType.timer || (!!state.qType.want && state.qType.shown !== state.qType.want);
        if (!busy && !typing && lastUser && lastAsst && sameQuestion(messageText(lastUser), state.qText)) {
          state.qText = "";
        }
        if (!busy && lastAsst && (state.liveAnswer || "") === messageText(lastAsst)) {
          state.liveAnswer = "";
        }
      }
    } catch (_) {}
    renderLiveLog();
  }

  function startLiveLogSync() {
    if (state.liveLogTimer) return;
    state.liveLogTimer = setInterval(() => {
      if (!state.liveId) return;
      if (state.answering && state.liveMic && state.liveMic.recording) return;
      hydrateLiveLog();
    }, 200);
  }

  function stopLiveLogSync() {
    if (state.liveLogTimer) {
      clearInterval(state.liveLogTimer);
      state.liveLogTimer = null;
    }
  }

  async function startLive() {
    const eng = await API.post("/api/engines", {
      kind: "live",
      model: $("live-model").value || undefined,
      language: $("live-lang").value || "en",
      resume: $("live-resume").value || "",
      job_description: $("live-jd").value || "",
      extra: $("live-extra").value || "",
    });
    state.liveId = eng.engine_id;
    $("live-setup").classList.add("hidden");
    $("live-stage").classList.remove("hidden");
    $("live-answer") && setLiveAnswer("", { restart: true });
    showLiveCaption("", { live: false });
    state.bubbles = [];
    renderBubbles();
    resetQuestionAssembly();
    await hydrateLiveLog();
    startLiveLogSync();
    showMode("live");
    startTimer();
    setStatus($("live-status"), "Ready — allow mic or share tab audio, then click Float for the overlay");
    try {
      await grantLiveAudio();
      await beginLiveCapture();
    } catch (_) {}
  }

  async function startCallSession(sessionId, connection, platform, opts = {}) {
    const joined = await API.post(`/api/sessions/${sessionId}/join`, { connection, platform });
    state.liveId = joined.engine_id;
    state.sessionId = sessionId;
    state.sessionConnection = connection;
    state.sessionPlatform = platform;
    if ($("live-lang")) $("live-lang").value = joined.language || "en";
    if ($("live-room-lang")) $("live-room-lang").value = joined.language || "en";
    if ($("audio-source")) $("audio-source").value = "mic";
    $("live-setup").classList.add("hidden");
    $("live-stage").classList.remove("hidden");
    $("live-answer") && setLiveAnswer("", { restart: true });
    showLiveCaption("", { live: false });
    state.bubbles = [];
    renderBubbles();
    resetQuestionAssembly();
    await hydrateLiveLog();
    startLiveLogSync();
    $("btn-mock-next")?.classList.toggle("hidden", connection !== "mock");
    showMode("live");
    startTimer();
    setStatus($("live-status"), "Allow the microphone — same capture as Mock (YouTube / call audio from speakers or BlackHole)");
    if (opts.review) return joined;
    try {
      await grantLiveAudio();
      await beginLiveCapture();
    } catch (e) {
      setStatus($("live-status"), e.message || "Audio permission needed");
    }
    if (connection === "mock") {
      try {
        const q = await API.post(`/api/sessions/${sessionId}/mock-question`);
        addBubble("interviewer", q.question);
      } catch (_) {}
    }
    if (joined.auto_answer) await startLiveAuto();
    else setStatus($("live-status"), "Ready — press Listen or ` to capture internal audio");
    if (platform === "desktop" && window.OverlayPrivacy) {
      OverlayPrivacy.enableHideFromShare().catch((e) => setStatus($("live-status"), e.message));
    }
    return joined;
  }

  async function beginLiveCapture() {
    const canvas = $("live-wave");
    state.liveMic.attachWaveform(canvas);
    state.liveMic.startMeter((rms) => {
      const label = $("live-wave-label");
      if (label) {
        label.textContent = rms > 0.012 ? "Hearing audio…" : "Listening…";
      }
    });
  }

  function paintListenButtons(on) {
    ["btn-live-listen", "btn-room-listen"].forEach((id) => {
      const btn = $(id);
      if (!btn) return;
      btn.classList.toggle("active-listen", on);
      btn.textContent = on ? "Stop & Process" : "Listen";
    });
  }

  function setListenButtons(on) {
    state.liveListening = on;
    paintListenButtons(on);
  }

  async function stopLiveListenAndAnswer() {
    const wasListening = !!state.liveListening;
    setListenButtons(false);
    try { state.liveMic.stopVad(); } catch (_) {}
    stopLiveStt();
    stopBrowserCaptions();
    if (window.OverlayPrivacy) OverlayPrivacy.syncLiveState({ listening: false, status: "Transcribing…" });
    let blob = null;
    if (wasListening) {
      try { blob = await state.liveMic.stop(); } catch (_) {}
    }
    setStatus($("live-status"), "Transcribing…");
    const heard = (state.qText || state.lastQuestion || "").trim();
    const usable = heard && heard !== "Listening…";
    try {
      if (blob && blob.size > 400) {
        await processLiveAudio(blob, true, true);
      } else if (usable) {
        await finalizeAssembled(heard, { autoAnswer: true, force: true });
      } else {
        setStatus($("live-status"), "No speech detected");
        if (window.OverlayPrivacy) OverlayPrivacy.syncLiveState({ listening: false, status: "No speech detected" });
      }
    } finally {
      const box = $("live-answer");
      if (box) box.scrollTop = box.scrollHeight;
      await hydrateLiveLog();
      if (box) box.scrollTop = box.scrollHeight;
    }
  }

  function stopLiveStt() {
    try { state.liveMic.onPcmStream = null; } catch (_) {}
    try { state.liveStt?.close(); } catch (_) {}
    state.liveStt = null;
    state.liveSttOk = false;
    state.liveSttAcc = "";
  }

  function applyLiveDelta(piece) {
    if (!piece || !state.liveListening) return;
    const Q = window.QuestionText;
    state.liveSttAcc = (state.liveSttAcc || "") + piece;
    const shown = Q ? Q.collapseSnowball(state.liveSttAcc) : state.liveSttAcc;
    if (!shown) return;
    ingestQuestion(shown, "live");
  }

  function applyLiveCompleted(text) {
    const Q = window.QuestionText;
    const raw = (text || state.liveSttAcc || state.qText || "").trim();
    const question = Q ? Q.collapseSnowball(raw) : raw;
    state.liveSttAcc = "";
    if (!question || !state.liveListening) return;
    ingestQuestion(question, "live");
  }

  function startLiveStt() {
    stopLiveStt();
    if (!window.LiveTranscribeSocket || !state.liveId) return;
    const lang = $("live-room-lang")?.value || $("live-lang")?.value || "en";
    state.liveStt = new LiveTranscribeSocket({
      engineId: state.liveId,
      lang,
      onReady: () => {
        state.liveSttOk = true;
        setStatus($("live-status"), "Live captions…");
      },
      onSpeechStarted: () => {
        state.liveSttAcc = "";
        resetQuestionType();
        try { state.captioner?.resetUtterance?.(); } catch (_) {}
      },
      onDelta: (piece) => applyLiveDelta(piece),
      onCompleted: (full) => applyLiveCompleted(full),
      onError: () => {
        state.liveSttOk = false;
      },
    });
    state.liveStt.connect();
    state.liveMic.onPcmStream = (samples) => {
      const rate = (state.liveMic.ctx && state.liveMic.ctx.sampleRate) || 48000;
      state.liveStt?.pushFloat32(samples, rate);
    };
  }

  async function startLiveCaptureLoop() {
    if (!state.liveMic.live) await grantLiveAudio();
    setListenButtons(true);
    setStatus($("live-status"), "Listening to internal audio…");
    if (window.OverlayPrivacy) OverlayPrivacy.syncLiveState({ listening: true, status: "Listening…" });
    resetQuestionType();
    state.qText = "Listening…";
    state.liveAnswer = "";
    renderLiveLog();
    try { state.liveMic.stopVad(); } catch (_) {}
    await state.liveMic.startHold();
    startLiveStt();
    startBrowserCaptions();
  }

  async function startLiveVadLoop() {
    if (!state.liveMic.live) await grantLiveAudio();
    setListenButtons(true);
    setStatus($("live-status"), "Auto: listening…");
    if (window.OverlayPrivacy) OverlayPrivacy.syncLiveState({ listening: true, status: "Auto listening…" });
    startLiveStt();
    state.liveMic.startVad(
      async (blob) => {
        if (!state.liveId || !state.liveListening) return;
        if (state.liveSttOk) return;
        const autoAnswer = state.liveAuto || state.sessionConnection === "real";
        await processLiveAudio(blob, false, autoAnswer);
      },
      {
        endSilenceMs: 2200,
        minSpeechMs: 400,
        prefetchEveryMs: 2000,
        onSpeechStart: () => {
          try { state.captioner?.resetUtterance?.(); } catch (_) {}
          showLiveCaption(state.qText || "Listening…", { live: true });
          setStatus($("live-status"), "Captions live…");
        },
        onPartial: (blob) => {
          if (!state.liveId || !state.liveListening) return;
          if (state.sessionConnection === "mock") return;
          if (state.liveSttOk) return;
          ingestPartial(blob);
        },
      }
    );
    startBrowserCaptions();
  }

  async function toggleLiveListen(opts = {}) {
    if (!opts.skipDebounce && !acceptListenToggle()) return;
    if (await toggleNativeListen(state.liveId)) return;
    const micOn = !!(state.liveMic && state.liveMic.recording);
    if (state.liveListening && !micOn) {
      await API.post("/api/privacy/command", { engine_id: state.liveId, command: "stop_listen" });
      setListenButtons(false);
      setStatus($("live-status"), "Transcribing…");
      hydrateLiveLog();
      return;
    }
    if (!state.liveListening) {
      await startLiveCaptureLoop();
      return;
    }
    await stopLiveListenAndAnswer();
  }

  async function endLive() {
    if (window.OverlayPrivacy) {
      try { await OverlayPrivacy.shutdown(); } catch (_) {}
    }
    if (state.liveAuto) await stopLiveAuto();
    if (state.liveListening) {
      await state.liveMic.cancel();
      state.liveListening = false;
    }
    stopBrowserCaptions();
    stopLiveStt();
    try { state.liveMic.stopTracksOnly(); } catch (_) {}
    if (state.liveId) {
      try {
        await API.post("/api/live/save", { engine_id: state.liveId });
      } catch (_) {}
    }
    if (state.sessionId) {
      try { await API.post(`/api/sessions/${state.sessionId}/end`); } catch (_) {}
    }
    state.liveId = null;
    state.sessionId = null;
    resetQuestionAssembly();
    stopLiveLogSync();
    stopTimer();
    if (window.SessionsUI) {
      SessionsUI.setLiveBadge(false);
      SessionsUI.refresh?.();
    }
    $("live-stage").classList.add("hidden");
    $("live-setup").classList.remove("hidden");
    showMode("sessions");
  }

  async function processLiveAudio(blob, force, autoAnswer) {
    if (!blob || blob.size < 400 || !state.liveId) return;
    setStatus($("live-status"), "Transcribing…");
    await ingestUtterance(blob, {
      force: !!force,
      autoAnswer: !!(force || autoAnswer || state.liveAuto),
    });
  }

  async function answerLastQuestion(opts = {}) {
    const text = (state.qText || state.lastQuestion || ($("live-input").value || "")).trim();
    if (!text || !state.liveId) {
      setStatus($("live-status"), "No question yet — wait for the interviewer, then press ` to stop and answer");
      return;
    }
    if (state.answering) return;
    const lastUser = [...state.messages].reverse().find((m) => m.role === "user");
    const lastAsst = [...state.messages].reverse().find((m) => m.role === "assistant");
    if (!opts.again && lastUser && lastAsst && messageText(lastUser).trim() === text) {
      setStatus($("live-status"), "Ready");
      renderLiveLog();
      return;
    }
    $("live-input").value = "";
    upsertInterviewer(text, { commit: true });
    const gen = state.answerGen + 1;
    state.answerGen = gen;
    state.answering = true;
    let acc = "";
    setLiveAnswer("", { restart: true });
    setStatus($("live-status"), "Writing answer…");
    await API.streamPost(
      "/api/chat/stream",
      { engine_id: state.liveId, text },
      {
        onEvent: (ev) => {
          if (state.answerGen !== gen) return;
          if (ev.type === "delta") {
            acc += ev.text || "";
            setLiveAnswer(acc);
          }
          if (ev.type === "done" && state.answerGen === gen) {
            if (ev.messages) state.messages = ev.messages;
            state.liveAnswer = acc || state.liveAnswer;
            state.answering = false;
            renderLiveLog();
            setStatus($("live-status"), "Ready");
            drainQueuedUtterance();
          }
          if (ev.type === "error") setStatus($("live-status"), ev.message || "Error");
        },
      }
    );
    if (state.answerGen === gen) {
      state.answering = false;
      drainQueuedUtterance();
    }
  }

  function drainQueuedUtterance() {
    const next = state.queuedUtterance;
    state.queuedUtterance = null;
    if (!next || !state.liveListening) return;
    processLiveAudio(next, false, autoAnswerLive()).catch(() => {});
  }

  async function startLiveAuto() {
    state.liveAuto = true;
    $("btn-live-auto").textContent = "Auto on";
    $("btn-live-auto").dataset.on = "1";
    setStatus($("live-status"), "Auto: listening for the next question…");
    if (window.OverlayPrivacy) OverlayPrivacy.syncLiveState({ auto: true, status: "Auto listening…" });
    if (!state.liveMic.live && !(window.OverlayPrivacy && OverlayPrivacy.isNative())) {
      try { await grantLiveAudio(); } catch (_) {}
    }
    if (!state.liveListening) await startLiveVadLoop();
  }

  async function stopLiveAuto() {
    state.liveAuto = false;
    clearTimeout(state.autoLoop);
    $("btn-live-auto").textContent = "Auto off";
    $("btn-live-auto").dataset.on = "0";
    setStatus($("live-status"), "Auto stopped — still listening");
    if (window.OverlayPrivacy) OverlayPrivacy.syncLiveState({ auto: false, status: "Auto stopped" });
  }

  async function sendLiveChat() {
    const text = $("live-input").value.trim();
    if (!text || !state.liveId) return;
    $("live-input").value = "";
    addBubble("interviewer", text);
    state.lastQuestion = text;
    state.qText = text;
    showLiveCaption(text, { live: false });
    const gen = state.answerGen + 1;
    state.answerGen = gen;
    state.answering = true;
    let acc = "";
    setLiveAnswer("", { restart: true });
    await API.streamPost(
      "/api/chat/stream",
      { engine_id: state.liveId, text },
      {
        onEvent: (ev) => {
          if (state.answerGen !== gen) return;
          if (ev.type === "delta") {
            acc += ev.text || "";
            setLiveAnswer(acc);
          }
          if (ev.type === "done") {
            if (ev.messages) state.messages = ev.messages;
            state.liveAnswer = acc || state.liveAnswer;
            state.answering = false;
            renderLiveLog();
          }
        },
      }
    );
    if (state.answerGen === gen) state.answering = false;
  }

  // ── Wiring ──────────────────────────────────────────────────────

  function wire() {
    document.querySelectorAll(".mode-tab, .nav-item[data-mode]").forEach((tab) => {
      tab.onclick = () => showMode(tab.dataset.mode);
    });
    $("btn-open-desktop")?.addEventListener("click", () => {
      if (state.liveId && window.OverlayPrivacy) {
        OverlayPrivacy.enableHideFromShare().catch((e) => alert(e.message));
      } else {
        alert("Join a session first, then open the floating overlay.");
      }
    });
    $("btn-logout-nav")?.addEventListener("click", () => $("btn-logout")?.click());

    $("btn-send").onclick = () => sendChat();
    $("input").addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendChat();
      }
    });
    $("input").addEventListener("paste", (e) => {
      const items = e.clipboardData && e.clipboardData.items;
      if (!items) return;
      for (const item of items) {
        if (item.type.startsWith("image/")) {
          e.preventDefault();
          const file = item.getAsFile();
          const reader = new FileReader();
          reader.onload = () => {
            state.pendingImages.push(reader.result);
            renderPending();
          };
          reader.readAsDataURL(file);
        }
      }
    });

    $("btn-listen").onclick = () => toggleListen();
    $("btn-stop").onclick = async () => {
      if (state.studioId) await API.post(`/api/engines/${state.studioId}/cancel`);
      if (state.listening) {
        await state.mic.cancel();
        state.listening = false;
        $("btn-listen").classList.remove("active-listen");
        $("btn-listen").textContent = "Listen";
      }
      setStatus($("status-line"), "Stopped");
    };
    $("btn-screen").onclick = () => analyzeScreen(state.studioId, $("messages"), $("status-line"));
    $("btn-attach").onclick = () => $("file-attach").click();
    $("file-attach").onchange = async (e) => {
      for (const file of e.target.files || []) {
        const fd = new FormData();
        fd.append("engine_id", state.studioId);
        fd.append("file", file);
        const res = await fetch("/api/documents/upload", { method: "POST", body: fd }).then((r) => r.json());
        setStatus($("status-line"), res.message || (res.ok ? "Attached" : "Attach failed"));
      }
      e.target.value = "";
    };

    $("btn-cycle-mode").onclick = async () => {
      const res = await API.post(`/api/engines/${state.studioId}/cycle-answer-mode`);
      $("btn-cycle-mode").textContent = `Mode: ${res.answer_mode}`;
    };
    $("btn-fast").onclick = async () => {
      const res = await API.post(`/api/engines/${state.studioId}/toggle-fast`);
      $("btn-fast").textContent = res.label;
    };
    $("select-model").onchange = async () => {
      await API.patch(`/api/engines/${state.studioId}/mode`, { model: $("select-model").value });
      $("model-pill").textContent = $("select-model").value;
    };
    $("btn-bookmark").onclick = async () => {
      const lastUser = [...state.messages].reverse().find((m) => m.role === "user");
      const preview = (lastUser && lastUser.content || "Bookmark").slice(0, 80);
      const res = await API.post("/api/bookmarks", {
        engine_id: state.studioId,
        line_index: state.messages.length,
        preview,
      });
      state.bookmarks = res.bookmarks || [];
      renderBookmarks();
    };
    $("btn-font-up").onclick = () => {
      state.fontSize = Math.min(24, state.fontSize + 1);
      $("messages").style.setProperty("--msg-font", state.fontSize + "px");
      $("messages").style.fontSize = state.fontSize + "px";
    };
    $("btn-font-down").onclick = () => {
      state.fontSize = Math.max(8, state.fontSize - 1);
      $("messages").style.fontSize = state.fontSize + "px";
    };
    $("btn-save-chat").onclick = async () => {
      const title = prompt("Chat title?", `Chat ${new Date().toLocaleString()}`);
      if (!title) return;
      await API.post("/api/chats/save-named", { engine_id: state.studioId, title });
      refreshChats();
    };
    $("btn-new-chat").onclick = async () => {
      await API.post(`/api/engines/${state.studioId}/clear`);
      state.messages = [];
      state.bookmarks = [];
      renderMessages($("messages"), []);
      renderBookmarks();
      refreshChats();
    };
    $("btn-add-tab").onclick = async () => {
      const name = prompt("Tab name?");
      if (!name) return;
      await API.post("/api/prompts/tabs", { name });
      refreshPrompts();
    };
    $("btn-default-interview").onclick = async () => {
      const data = await API.post("/api/default-interview/bodies", {});
      for (const item of data.items || []) {
        if (item.body) await sendChat(item.body);
      }
    };

    // Live
    $("btn-start-live").onclick = () => startLive().catch((e) => alert(e.message));
    const grantBtn = $("btn-grant-audio");
    if (grantBtn) grantBtn.onclick = () => grantLiveAudio().catch(() => {});
    API.get("/api/audio/status").then((info) => {
      const hint = $("audio-setup-hint");
      if (hint && info && info.setup) hint.textContent = info.setup;
      const st = $("audio-grant-status");
      if (st && info && info.loopback_device) st.textContent = `Loopback found: ${info.loopback_device}`;
    }).catch(() => {});
    $("btn-end-live").onclick = () => endLive();
    $("btn-live-disconnect")?.addEventListener("click", () => endLive());
    $("btn-live-listen").onclick = () => toggleLiveListen().catch((e) => setStatus($("live-status"), e.message));
    $("btn-room-listen")?.addEventListener("click", () => toggleLiveListen().catch((e) => setStatus($("live-status"), e.message)));
    $("btn-live-answer")?.addEventListener("click", () => answerLastQuestion({ again: true }).catch((e) => setStatus($("live-status"), e.message)));
    $("btn-live-prefs")?.addEventListener("click", () => {
      if (window.SessionsUI) SessionsUI.openPrefs(state.sessionId);
    });
    $("btn-mock-next")?.addEventListener("click", async () => {
      if (!state.sessionId) return;
      const q = await API.post(`/api/sessions/${state.sessionId}/mock-question`);
      addBubble("interviewer", q.question);
    });
    $("btn-live-fullscreen")?.addEventListener("click", () => {
      const el = $("live-room") || $("view-live");
      if (!document.fullscreenElement) el.requestFullscreen?.();
      else document.exitFullscreen?.();
    });
    $("live-room-lang")?.addEventListener("change", async () => {
      const lang = $("live-room-lang").value;
      if ($("live-lang")) $("live-lang").value = lang;
      if (state.liveId) await API.patch(`/api/engines/${state.liveId}/mode`, { language: lang });
      if (state.liveListening) startBrowserCaptions();
    });
    $("btn-live-auto").onclick = async () => {
      if (state.liveAuto) await stopLiveAuto();
      else await startLiveAuto();
    };
    $("btn-live-screen").onclick = () =>
      analyzeScreen(state.liveId, $("live-answer"), $("live-status"));
    $("btn-live-notes").onclick = async () => {
      const res = await API.post("/api/live/notes", { engine_id: state.liveId });
      $("notes-body").textContent = res.notes || "";
      $("notes-drawer").classList.remove("hidden");
    };
    $("btn-close-notes").onclick = () => $("notes-drawer").classList.add("hidden");
    $("btn-live-send").onclick = () => sendLiveChat();
    $("live-input").addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        sendLiveChat();
      }
    });
    $("btn-live-mode").onclick = async () => {
      const res = await API.post(`/api/engines/${state.liveId}/cycle-answer-mode`);
      $("btn-live-mode").textContent = res.answer_mode;
    };
    $("btn-live-fast").onclick = async () => {
      const res = await API.post(`/api/engines/${state.liveId}/toggle-fast`);
      $("btn-live-fast").textContent = res.label;
    };
    $("btn-overlay-opacity").onclick = () => {
      $("overlay-window").classList.toggle("dim");
    };

    if (window.OverlayPrivacy) {
      OverlayPrivacy.init({
        getEngineId: () => {
          const liveOpen = !$("view-live").classList.contains("hidden");
          const studioOpen = !$("view-studio").classList.contains("hidden");
          if (liveOpen && state.liveId) return state.liveId;
          if (studioOpen && state.studioId) return state.studioId;
          return state.liveId || state.studioId;
        },
        onStatus: (msg) => {
          const el = !$("view-live").classList.contains("hidden") ? $("live-status") : $("status-line");
          setStatus(el, msg);
        },
        onListening: (on) => {
          if (state.liveId) paintListenButtons(!!on || state.liveListening);
        },
        onCommand: (cmd) => {
          if (cmd === "listen" || cmd === "stop_listen" || cmd === "toggle_listen") {
            routeListenToggle(cmd);
          } else if (cmd === "auto_on") {
            if (state.liveId && !state.liveAuto) startLiveAuto();
          } else if (cmd === "auto_off") {
            if (state.liveId && state.liveAuto) stopLiveAuto();
          } else if (cmd === "screen") {
            if (state.liveId) analyzeScreen(state.liveId, $("live-answer"), $("live-status"));
            else if (state.studioId) analyzeScreen(state.studioId, $("messages"), $("status-line"));
          } else if (cmd === "end") {
            OverlayPrivacy.disableHideFromShare();
          }
        },
      });
    }

    // OS-global `` ` `` is handled by the Python server (works in other apps).
    // In-page handler is only a fallback when that listener is not armed.
    window.addEventListener("keydown", (e) => {
      if (e.target.matches("textarea, input")) return;
      if (e.key === "`") {
        e.preventDefault();
        if (state.status && state.status.global_hotkeys) return;
        const liveOpen = state.liveId && !$("view-live").classList.contains("hidden");
        if (liveOpen || (state.liveId && $("view-studio").classList.contains("hidden"))) {
          toggleLiveListen();
        } else {
          toggleListen();
        }
      }
      if (e.key === "!") {
        e.preventDefault();
        if (!$("view-studio").classList.contains("hidden")) {
          analyzeScreen(state.studioId, $("messages"), $("status-line"));
        } else if (state.liveId) {
          analyzeScreen(state.liveId, $("live-answer"), $("live-status"));
        }
      }
    });
  }

  async function bootAccount() {
    try {
      const r = await fetch("/api/auth/me", { credentials: "include" });
      const data = await r.json();
      if (data.required && !data.user) {
        location.replace("/login?next=/app");
        return;
      }
      if (data.user) {
        $("account-chip").classList.remove("hidden");
        $("account-email").textContent = data.user.email || data.user.name || "";
        const name = data.user.name || data.user.email || "User";
        if ($("user-name")) $("user-name").textContent = name;
        if ($("user-email")) $("user-email").textContent = data.user.email || "";
        if ($("user-avatar")) {
          const initials = name.split(/[\s@]+/).filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join("");
          $("user-avatar").textContent = initials || "IC";
        }
      }
    } catch (_) { /* guest mode */ }
    $("btn-logout")?.addEventListener("click", async () => {
      await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
      location.href = "/";
    });
  }

  async function boot() {
    wire();
    if (window.SessionsUI) {
      SessionsUI.init({
        onJoin: (id, connection, platform, opts) => startCallSession(id, connection, platform, opts || {}),
        showMode,
      });
    }
    await bootAccount();
    showMode("sessions");
    try {
      await refreshStatus();
      await initStudio();
    } catch (e) {
      setStatus($("status-line"), e.message || String(e));
      $("conn-status").textContent = "Backend error";
      $("conn-status").className = "pill pill-bad";
    }
  }

  boot();
})();
