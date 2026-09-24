/** Dashboard, create-session, and preference modals. */
(() => {
  const $ = (id) => document.getElementById(id);

  const state = {
    filter: "all",
    query: "",
    listView: false,
    sessions: [],
    pendingId: null,
    pendingConnection: "real",
    answerPrefs: {
      format: "script_bullets",
      length: "balanced",
      tone: "simple",
      question_type: "behavioral",
      star: false,
      filler_words: false,
    },
    resumeFile: null,
    docFiles: [],
    libraryKind: "resume",
    onJoin: null,
    showMode: null,
  };

  function openModal(id) {
    const el = $(id);
    if (el) el.classList.remove("hidden");
  }

  function closeModal(id) {
    const el = $(id);
    if (el) el.classList.add("hidden");
  }

  function fmtDate(iso) {
    if (!iso) return "";
    try {
      return new Date(iso).toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" }).toUpperCase();
    } catch (_) {
      return iso;
    }
  }

  function fmtDuration(seconds) {
    const s = Math.max(0, Number(seconds) || 0);
    const m = Math.floor(s / 60);
    const r = s % 60;
    if (!m && !r) return "";
    return r ? `${m}m ${r}s` : `${m}m`;
  }

  function readPrefsFromForm() {
    const format = (document.querySelector("input[name='pref-format']:checked") || {}).value || "script_bullets";
    return {
      format,
      length: $("pref-length").value,
      tone: $("pref-tone").value,
      question_type: $("pref-qtype").value,
      star: $("pref-star").checked,
      filler_words: $("pref-filler").checked,
    };
  }

  function writePrefsToForm(prefs) {
    const p = prefs || state.answerPrefs;
    document.querySelectorAll("input[name='pref-format']").forEach((el) => {
      el.checked = el.value === p.format;
    });
    $("pref-length").value = p.length || "balanced";
    $("pref-tone").value = p.tone || "simple";
    $("pref-qtype").value = p.question_type || "behavioral";
    $("pref-star").checked = !!p.star;
    $("pref-filler").checked = !!p.filler_words;
  }

  async function refreshPreview() {
    const prefs = readPrefsFromForm();
    try {
      const data = await API.post("/api/answer-prefs/preview", prefs);
      $("pref-preview").innerHTML =
        `<strong>Question:</strong> ${esc(data.question)}<br/><br/>${esc(data.answer)}`;
    } catch (e) {
      $("pref-preview").textContent = e.message || "Preview unavailable";
    }
  }

  function esc(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\n/g, "<br/>");
  }

  async function refresh() {
    const data = await API.get(`/api/sessions?state=${encodeURIComponent(state.filter)}`);
    state.sessions = data.sessions || [];
    const live = !!data.live;
    $("nav-live-pill")?.classList.toggle("hidden", !live);
    render();
  }

  function render() {
    const q = state.query.trim().toLowerCase();
    const items = state.sessions.filter((s) => {
      if (!q) return true;
      const blob = `${s.title || ""} ${s.company || ""} ${s.description || ""}`.toLowerCase();
      return blob.includes(q);
    });
    $("session-count").textContent = `${items.length} Session${items.length === 1 ? "" : "s"}`;
    $("session-empty").classList.toggle("hidden", items.length > 0);
    const grid = $("session-grid");
    grid.classList.toggle("list", state.listView);
    grid.innerHTML = items
      .map((s) => {
        const tags = [
          s.kind === "regular" ? "Call" : "Interview",
          s.connection === "mock" ? "Mock" : s.connection === "real" ? "Real" : "",
          s.save_transcript ? "Transcript" : "",
        ].filter(Boolean);
        const live = s.state === "live";
        const dur = fmtDuration(s.duration_seconds);
        return `<article class="session-card" data-id="${s.id}">
          <div class="meta"><span>${fmtDate(s.created_at)}</span><span>${s.state}</span></div>
          <h3>${esc(s.title || "Untitled")}</h3>
          <p class="role">${esc(s.description || s.company || "")}</p>
          <div class="tag-row">${tags.map((t) => `<span class="tag">${esc(t)}</span>`).join("")}</div>
          ${live ? `<div class="session-live"><span class="live-dot"></span> Live ${dur || ""}</div>` : (dur ? `<div class="muted">${dur}</div>` : "")}
          <button type="button" class="btn ${live || s.state === "ready" ? "primary" : ""} full btn-join">${s.state === "ended" ? "Review" : "Join Session"}</button>
        </article>`;
      })
      .join("");
    grid.querySelectorAll(".btn-join").forEach((btn) => {
      btn.onclick = () => onJoinCard(btn.closest(".session-card").dataset.id);
    });
  }

  async function onJoinCard(id) {
    const session = state.sessions.find((s) => s.id === id) || (await API.get(`/api/sessions/${id}`));
    state.pendingId = id;
    if (session.state === "ended") {
      if (state.showMode) state.showMode("live");
      if (state.onJoin) await state.onJoin(id, session.connection || "real", session.platform || "browser", { review: true });
      return;
    }
    if (session.connection) {
      if (state.onJoin) await state.onJoin(id, session.connection, session.platform || "browser");
      return;
    }
    openModal("modal-kind");
  }

  function kindFromSeg() {
    const active = document.querySelector("#create-kind .seg-btn.active");
    return (active && active.dataset.kind) || "interview";
  }

  async function submitCreate() {
    const kind = kindFromSeg();
    const company = $("create-company").value.trim();
    const title = kind === "regular" ? $("create-title-input").value.trim() : company;
    const description = kind === "regular" ? $("create-regular-desc").value.trim() : $("create-desc").value.trim();
    const body = {
      kind,
      title,
      company,
      description,
      posting_url: $("create-url").value.trim(),
      language: $("create-lang").value,
      model: $("create-model").value,
      auto_answer: $("create-auto").checked,
      save_transcript: $("create-save").checked,
      instructions: $("create-instructions").value.trim(),
      answer_prefs: state.answerPrefs,
    };
    const session = await API.post("/api/sessions", body);
    state.pendingId = session.id;
    const status = $("create-context-status");
    if (state.resumeFile) {
      const fd = new FormData();
      fd.append("kind", "resume");
      fd.append("file", state.resumeFile);
      await fetch(`/api/sessions/${session.id}/document`, { method: "POST", body: fd });
      if (status) status.textContent = "Resume attached";
    }
    for (const file of state.docFiles) {
      const fd = new FormData();
      fd.append("kind", "document");
      fd.append("file", file);
      await fetch(`/api/sessions/${session.id}/document`, { method: "POST", body: fd });
    }
    closeModal("modal-create");
    openModal("modal-kind");
    await refresh();
  }

  async function continueJoin(connection) {
    state.pendingConnection = connection;
    closeModal("modal-kind");
    openModal("modal-platform");
  }

  async function pickPlatform(platform) {
    closeModal("modal-platform");
    if (!state.pendingId) return;
    if (state.onJoin) await state.onJoin(state.pendingId, state.pendingConnection, platform);
    await refresh();
  }

  async function refreshLibrary() {
    const kind = state.libraryKind === "resumes" ? "resume" : "document";
    $("library-title").textContent = state.libraryKind === "resumes" ? "CVs & Resumes" : "Documents";
    const data = await API.get(`/api/library?kind=${kind}`);
    const items = data.items || [];
    $("library-list").innerHTML = items.length
      ? items
          .map(
            (it) => `<div class="library-item"><div><strong>${esc(it.name)}</strong><div class="muted">${it.chars} chars</div></div>
              <button type="button" class="btn ghost" data-del="${it.id}">Delete</button></div>`
          )
          .join("")
      : `<p class="muted">Nothing saved yet. Upload a PDF or text file.</p>`;
    $("library-list").querySelectorAll("[data-del]").forEach((btn) => {
      btn.onclick = async () => {
        await API.del(`/api/library/${btn.dataset.del}`);
        refreshLibrary();
      };
    });
  }

  function showLibrary(mode) {
    state.libraryKind = mode;
    refreshLibrary().catch(() => {});
  }

  function wire() {
    document.querySelectorAll("[data-close]").forEach((btn) => {
      btn.onclick = () => closeModal(btn.dataset.close);
    });
    $("btn-create-session").onclick = () => {
      state.resumeFile = null;
      state.docFiles = [];
      $("create-context-status").textContent = "";
      $("create-instructions").classList.add("hidden");
      openModal("modal-create");
    };
    document.querySelectorAll("#create-kind .seg-btn").forEach((btn) => {
      btn.onclick = () => {
        document.querySelectorAll("#create-kind .seg-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        const interview = btn.dataset.kind === "interview";
        $("create-interview-fields").classList.toggle("hidden", !interview);
        $("create-regular-fields").classList.toggle("hidden", interview);
      };
    });
    $("btn-add-resume").onclick = () => $("create-resume-file").click();
    $("btn-add-docs").onclick = () => $("create-docs-file").click();
    $("btn-add-instructions").onclick = () => $("create-instructions").classList.toggle("hidden");
    $("create-resume-file").onchange = (e) => {
      state.resumeFile = (e.target.files || [])[0] || null;
      $("btn-add-resume").classList.toggle("filled", !!state.resumeFile);
      $("create-context-status").textContent = state.resumeFile ? `Resume: ${state.resumeFile.name}` : "";
    };
    $("create-docs-file").onchange = (e) => {
      state.docFiles = [...(e.target.files || [])];
      $("btn-add-docs").classList.toggle("filled", state.docFiles.length > 0);
    };
    $("btn-open-prefs").onclick = () => openPrefs();
    $("btn-submit-create").onclick = () => submitCreate().catch((e) => alert(e.message));
    $("btn-select-real").onclick = () => continueJoin("real");
    $("btn-select-mock").onclick = () => continueJoin("mock");
    $("btn-platform-desktop").onclick = () => pickPlatform("desktop").catch((e) => alert(e.message));
    $("btn-platform-browser").onclick = () => pickPlatform("browser").catch((e) => alert(e.message));
    $("btn-platform-diff").onclick = () => openModal("modal-diff");
    $("btn-save-prefs").onclick = async () => {
      state.answerPrefs = readPrefsFromForm();
      if (state.pendingId) {
        try {
          await API.patch(`/api/sessions/${state.pendingId}/answer-prefs`, state.answerPrefs);
        } catch (_) {}
      }
      closeModal("modal-prefs");
    };
    ["pref-length", "pref-tone", "pref-qtype", "pref-star", "pref-filler"].forEach((id) => {
      $(id)?.addEventListener("change", refreshPreview);
    });
    document.querySelectorAll("input[name='pref-format']").forEach((el) => {
      el.addEventListener("change", refreshPreview);
    });
    document.querySelectorAll(".filter-tab").forEach((tab) => {
      tab.onclick = () => {
        document.querySelectorAll(".filter-tab").forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");
        state.filter = tab.dataset.filter;
        refresh().catch(() => {});
      };
    });
    $("session-search").oninput = () => {
      state.query = $("session-search").value;
      render();
    };
    $("btn-view-grid").onclick = () => {
      state.listView = false;
      $("btn-view-grid").classList.add("active");
      $("btn-view-list").classList.remove("active");
      render();
    };
    $("btn-view-list").onclick = () => {
      state.listView = true;
      $("btn-view-list").classList.add("active");
      $("btn-view-grid").classList.remove("active");
      render();
    };
    $("library-file").onchange = async (e) => {
      const file = (e.target.files || [])[0];
      if (!file) return;
      const fd = new FormData();
      fd.append("kind", state.libraryKind === "resumes" ? "resume" : "document");
      fd.append("file", file);
      await fetch("/api/library/upload", { method: "POST", body: fd });
      e.target.value = "";
      refreshLibrary();
    };
  }

  function openPrefs(sessionId) {
    if (sessionId) state.pendingId = sessionId;
    writePrefsToForm(state.answerPrefs);
    openModal("modal-prefs");
    refreshPreview();
  }

  function init(opts) {
    Object.assign(state, opts || {});
    wire();
    refresh().catch(() => {});
  }

  window.SessionsUI = {
    init,
    refresh,
    openPrefs,
    showLibrary,
    setLiveBadge(on) {
      $("nav-live-pill")?.classList.toggle("hidden", !on);
    },
  };
})();
