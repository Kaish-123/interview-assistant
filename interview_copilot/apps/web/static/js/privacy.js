/** Floating overlay + hide-from-share for the web companion. */
(() => {
  const state = {
    pipWindow: null,
    popup: null,
    privacyOn: false,
    floating: false,
    clickThrough: false,
    lastCmdSeq: 0,
    pollTimer: null,
    cmdTimer: null,
    native: false,
    getEngineId: () => null,
    onCommand: () => {},
    onListening: () => {},
    onStatus: () => {},
  };

  function $(id) {
    return document.getElementById(id);
  }

  function $ov(id) {
    const docs = [];
    if (state.pipWindow && !state.pipWindow.closed) docs.push(state.pipWindow.document);
    if (state.popup && !state.popup.closed) docs.push(state.popup.document);
    docs.push(document);
    for (const d of docs) {
      const el = d.getElementById(id);
      if (el) return el;
    }
    return null;
  }

  function overlayEl() {
    return $ov("overlay-window");
  }

  function home() {
    return $("overlay-dock") || $("live-stage") || document.body;
  }

  function copyStyles(destDoc) {
    destDoc.documentElement.className = document.documentElement.className;
    destDoc.body.className = "pip-overlay-body";
    for (const node of document.querySelectorAll('link[rel="stylesheet"], style')) {
      destDoc.head.appendChild(node.cloneNode(true));
    }
    const extra = destDoc.createElement("style");
    extra.textContent =
      "html,body.pip-overlay-body{margin:0;height:100%;background:#0b1016;}" +
      ".overlay-window{width:100%;max-width:none;min-height:100%;max-height:100%;border-radius:0;box-shadow:none;display:flex;flex-direction:column;}" +
      ".live-log,.live-answer{flex:1;min-height:0;max-height:none;overflow:auto;}" +
      ".live-hearing{flex-shrink:0;}";
    destDoc.head.appendChild(extra);
  }

  function moveOverlayTo(doc) {
    const el = overlayEl();
    if (!el) return;
    doc.body.appendChild(el);
  }

  function returnOverlay() {
    const el = overlayEl();
    const stage = home();
    if (el && stage && el.parentElement !== stage) {
      stage.insertBefore(el, stage.firstChild);
    }
    state.floating = false;
    const btn = $("btn-overlay-float");
    if (btn) btn.textContent = "Float";
  }

  function closePip() {
    try {
      if (state.pipWindow && !state.pipWindow.closed) state.pipWindow.close();
    } catch (_) {}
    state.pipWindow = null;
    try {
      if (state.popup && !state.popup.closed) state.popup.close();
    } catch (_) {}
    state.popup = null;
    returnOverlay();
  }

  async function openPip() {
    const el = overlayEl();
    if (!el) throw new Error("Overlay not ready");
    if (window.documentPictureInPicture && window.documentPictureInPicture.requestWindow) {
      const pip = await window.documentPictureInPicture.requestWindow({
        width: 420,
        height: 560,
        disallowReturnToOpener: true,
      });
      copyStyles(pip.document);
      moveOverlayTo(pip.document);
      pip.addEventListener("pagehide", () => {
        returnOverlay();
        state.pipWindow = null;
        if (state.privacyOn && !state.native) showCover(true);
      });
      state.pipWindow = pip;
      bindClickThroughKeys(pip.document);
      state.floating = true;
      const btn = $("btn-overlay-float");
      if (btn) btn.textContent = "Dock";
      return "pip";
    }
    const popup = window.open(
      "",
      "interview-copilot-overlay",
      "popup=yes,width=420,height=560,menubar=no,toolbar=no,location=no,status=no"
    );
    if (!popup) throw new Error("Popup blocked — allow popups for this site, then try Float again.");
    popup.document.title = "Live Assist";
    copyStyles(popup.document);
    moveOverlayTo(popup.document);
    popup.addEventListener("pagehide", () => {
      returnOverlay();
      state.popup = null;
    });
    state.popup = popup;
    bindClickThroughKeys(popup.document);
    state.floating = true;
    const btn = $("btn-overlay-float");
    if (btn) btn.textContent = "Dock";
    return "popup";
  }

  function showCover(on) {
    const cover = $("share-safe-cover");
    if (!cover) return;
    cover.classList.toggle("hidden", !on);
    document.body.classList.toggle("privacy-on", on);
  }

  function setPrivacyHint(native) {
    const hint = $("share-safe-hint");
    if (!hint) return;
    hint.textContent = native
      ? "The floating overlay is excluded from screen capture on this computer. You can share your full screen or a meeting window."
      : "Share your meeting window or tab — not this page. Entire-screen share can still show a browser floating window.";
  }

  async function postPrivacy(path, body) {
    return API.post(path, body);
  }

  async function enableHideFromShare() {
    const engineId = state.getEngineId();
    if (!engineId) throw new Error("Start a Live or Studio session first");
    state.privacyOn = true;
    state.floating = true;
    showCover(true);
    $("overlay-window") && $("overlay-window").classList.add("stealth");
    const btn = $("btn-overlay-privacy");
    if (btn) {
      btn.textContent = "Sharing hidden";
      btn.classList.add("privacy-active");
    }
    const floatBtn = $("btn-overlay-float");
    if (floatBtn) floatBtn.textContent = "Dock";
    const g = $("btn-privacy-global");
    if (g) {
      g.textContent = "Sharing hidden";
      g.classList.add("privacy-active");
    }

    let native = false;
    state._fallbackAttempted = false;
    try {
      const res = await postPrivacy("/api/privacy/overlay", { engine_id: engineId });
      native = !!(res && res.native && res.ok !== false && res.alive !== false);
      state.native = native;
      setPrivacyHint(native);
      if (!native && res && res.reason) state.onStatus(res.reason);
    } catch (e) {
      state.native = false;
      setPrivacyHint(false);
      state.onStatus(e.message || String(e));
    }

    if (native) {
      closePip();
      if (overlayEl()) overlayEl().classList.add("hidden-from-tab");
    } else {
      if (overlayEl()) overlayEl().classList.remove("hidden-from-tab");
      try {
        await openPip();
        showCover(true);
      } catch (e) {
        state.onStatus(e.message || String(e));
      }
    }
    startPoll();
    return { native: state.native, floating: state.floating };
  }

  async function disableHideFromShare() {
    const engineId = state.getEngineId();
    state.privacyOn = false;
    state.native = false;
    state.floating = false;
    stopPoll();
    showCover(false);
    if (overlayEl()) {
      overlayEl().classList.remove("stealth", "hidden-from-tab");
    }
    const btn = $("btn-overlay-privacy");
    if (btn) {
      btn.textContent = "Hide from share";
      btn.classList.remove("privacy-active");
    }
    const g = $("btn-privacy-global");
    if (g) {
      g.textContent = "Hide from share";
      g.classList.remove("privacy-active");
    }
    if (engineId) {
      try {
        await postPrivacy("/api/privacy/overlay/stop", { engine_id: engineId });
      } catch (_) {}
    }
    closePip();
  }

  async function toggleFloat() {
    if (state.floating || state.privacyOn) {
      await disableHideFromShare();
      return { floating: false };
    }
    return enableHideFromShare();
  }

  function ingestOverlayCommand(ov) {
    const seq = Number(ov.seq || 0);
    if (seq && seq !== state.lastCmdSeq) {
      state.lastCmdSeq = seq;
      if (ov.command) state.onCommand(ov.command);
    }
    if (typeof ov.listening === "boolean") state.onListening(ov.listening);
  }

  function startCommandPoll() {
    if (state.cmdTimer) return;
    const tick = async () => {
      const id = state.getEngineId();
      if (!id) return;
      try {
        const snap = await API.get(`/api/engines/${id}?focus=1`);
        const ov = (snap.meta && snap.meta.overlay) || {};
        ingestOverlayCommand(ov);
        if (state.privacyOn && state.native && ov.alive === false && !state._fallbackAttempted) {
          state._fallbackAttempted = true;
          state.native = false;
          state.onStatus("Overlay closed — opening a floating window");
          if (overlayEl()) overlayEl().classList.remove("hidden-from-tab");
          openPip().catch((e) => state.onStatus(e.message || String(e)));
        }
      } catch (_) {}
    };
    state.cmdTimer = setInterval(tick, 280);
    tick();
  }

  function startPoll() {
    stopPoll();
    const tick = async () => {
      if (!state.privacyOn) return;
      const id = state.getEngineId();
      if (!id) return;
      try {
        const snap = await API.get(`/api/engines/${id}`);
        const ov = (snap.meta && snap.meta.overlay) || {};
        ingestOverlayCommand(ov);
        if (state.native && ov.alive === false && !state._fallbackAttempted) {
          state._fallbackAttempted = true;
          state.native = false;
          state.onStatus("Overlay closed — opening a floating window");
          if (overlayEl()) overlayEl().classList.remove("hidden-from-tab");
          openPip().catch((e) => state.onStatus(e.message || String(e)));
        }
      } catch (_) {}
    };
    state.pollTimer = setInterval(tick, 400);
    tick();
  }

  function stopPoll() {
    if (state.pollTimer) clearInterval(state.pollTimer);
    state.pollTimer = null;
  }

  function applyOpacity(pct) {
    const el = overlayEl();
    if (!el) return;
    const n = Math.max(20, Math.min(100, Number(pct) || 85));
    el.style.opacity = String(n / 100);
  }

  const isMac = /mac/i.test(navigator.platform || navigator.userAgent || "");
  const ctShortcut = isMac ? "Esc / ⌘⇧O" : "Esc / Ctrl+Shift+O";

  function setClickThrough(on) {
    state.clickThrough = !!on;
    const el = overlayEl();
    if (el) el.classList.toggle("click-through", state.clickThrough);
    const btn = $ov("btn-overlay-clickthrough");
    if (btn) {
      btn.textContent = state.clickThrough ? "Click-through ON" : "Click-through off";
      btn.dataset.on = state.clickThrough ? "1" : "0";
      btn.title = state.clickThrough
        ? `Click-through is on. Click this button, or press ${ctShortcut}, to turn it off.`
        : "Clicks pass through the overlay";
    }
    if (state.clickThrough) state.onStatus("Click-through on — click the button or press Esc to turn off");
    else state.onStatus("Click-through off");
  }

  function bindClickThroughKeys(target) {
    if (!target || target._ctKeys) return;
    target._ctKeys = true;
    target.addEventListener("keydown", (e) => {
      const key = (e.key || "").toLowerCase();
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && key === "o") {
        e.preventDefault();
        setClickThrough(!state.clickThrough);
      }
      if (key === "escape" && state.clickThrough) {
        e.preventDefault();
        setClickThrough(false);
      }
    });
  }

  async function syncLiveState(patch) {
    const id = state.getEngineId();
    if (!id) return;
    try {
      await API.post("/api/privacy/state", { engine_id: id, ...patch });
    } catch (_) {}
  }

  async function shutdown() {
    await disableHideFromShare();
  }

  function init(opts) {
    Object.assign(state, opts || {});
    startCommandPoll();
    const floatBtn = $("btn-overlay-float");
    if (floatBtn) floatBtn.onclick = () => toggleFloat().catch((e) => state.onStatus(e.message));
    const privBtn = $("btn-overlay-privacy");
    if (privBtn) {
      privBtn.onclick = () => {
        if (state.privacyOn) disableHideFromShare();
        else enableHideFromShare().catch((e) => state.onStatus(e.message));
      };
    }
    const globalBtn = $("btn-privacy-global");
    if (globalBtn) {
      globalBtn.onclick = () => {
        if (state.privacyOn) disableHideFromShare();
        else enableHideFromShare().catch((e) => state.onStatus(e.message));
      };
    }
    const showBtn = $("btn-privacy-show");
    if (showBtn) showBtn.onclick = () => disableHideFromShare();
    const opacity = $("overlay-opacity");
    if (opacity) {
      opacity.oninput = () => applyOpacity(opacity.value);
      applyOpacity(opacity.value);
    }
    const ct = $ov("btn-overlay-clickthrough") || $("btn-overlay-clickthrough");
    if (ct) ct.onclick = () => setClickThrough(!state.clickThrough);
    bindClickThroughKeys(window);
    const dim = $("btn-overlay-opacity");
    if (dim) {
      dim.onclick = () => {
        const el = overlayEl();
        if (!el) return;
        el.classList.toggle("dim");
      };
    }
  }

  window.OverlayPrivacy = {
    init,
    toggleFloat,
    enableHideFromShare,
    disableHideFromShare,
    shutdown,
    syncLiveState,
    isHidden: () => state.privacyOn,
    isFloating: () => state.floating,
    isNative: () => state.native,
  };
})();
