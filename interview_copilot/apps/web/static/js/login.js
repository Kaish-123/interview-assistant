(() => {
  const params = new URLSearchParams(location.search);
  const next = params.get("next") || "/app";
  const pageError = document.getElementById("page-error");
  const errors = { google: "Google sign-in failed. Check GOOGLE_CLIENT_ID / SECRET and the callback URL.", state: "Sign-in expired. Try Google again.", email: "Google did not return an email." };
  if (params.get("error")) pageError.textContent = errors[params.get("error")] || "Sign-in failed.";

  const views = {
    start: document.getElementById("view-start"),
    email: document.getElementById("view-email"),
    code: document.getElementById("view-code"),
  };
  let pendingEmail = "";

  function show(name) {
    Object.values(views).forEach((el) => el.classList.add("hidden"));
    views[name].classList.remove("hidden");
  }

  async function me() {
    const r = await fetch("/api/auth/me", { credentials: "include" });
    return r.json();
  }

  me().then((data) => {
    if (data.user) location.replace(next);
    const g = document.getElementById("btn-google");
    if (!data.google) {
      g.textContent = "Continue with Google (configure env)";
    }
  }).catch(() => {});

  document.getElementById("btn-google").addEventListener("click", () => {
    location.href = `/api/auth/google/start?next=${encodeURIComponent(next)}`;
  });
  document.getElementById("btn-email").addEventListener("click", () => show("email"));
  ["back-start", "back-login-1", "back-login-2"].forEach((id) => {
    document.getElementById(id).addEventListener("click", (e) => {
      e.preventDefault();
      show("start");
    });
  });
  document.getElementById("back-email").addEventListener("click", (e) => {
    e.preventDefault();
    show("email");
  });

  async function sendCode() {
    const email = document.getElementById("email").value.trim();
    const err = document.getElementById("email-error");
    err.textContent = "";
    const r = await fetch("/api/auth/email/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email }),
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) {
      err.textContent = data.detail || "Could not send a code.";
      return;
    }
    pendingEmail = data.email;
    document.getElementById("code-copy").innerHTML =
      `We sent a login code to <b>${pendingEmail}</b>. Open it on this device, or type the code below.`;
    const hint = document.getElementById("dev-code");
    hint.textContent = data.dev_code ? `Dev code (AUTH_DEV_SHOW_CODE): ${data.dev_code}` : "";
    show("code");
    document.querySelector("#otp input").focus();
  }

  document.getElementById("btn-send-code").addEventListener("click", sendCode);
  document.getElementById("resend").addEventListener("click", (e) => {
    e.preventDefault();
    sendCode();
  });

  const boxes = [...document.querySelectorAll("#otp input")];
  boxes.forEach((box, i) => {
    box.addEventListener("input", () => {
      box.value = box.value.replace(/\D/g, "").slice(-1);
      if (box.value && i < boxes.length - 1) boxes[i + 1].focus();
      if (boxes.every((b) => b.value)) verify();
    });
    box.addEventListener("keydown", (e) => {
      if (e.key === "Backspace" && !box.value && i > 0) boxes[i - 1].focus();
    });
    box.addEventListener("paste", (e) => {
      const text = (e.clipboardData.getData("text") || "").replace(/\D/g, "").slice(0, 6);
      if (!text) return;
      e.preventDefault();
      text.split("").forEach((ch, idx) => { if (boxes[idx]) boxes[idx].value = ch; });
      if (text.length === 6) verify();
    });
  });

  async function verify() {
    const err = document.getElementById("code-error");
    err.textContent = "";
    const code = boxes.map((b) => b.value).join("");
    const r = await fetch("/api/auth/email/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email: pendingEmail || document.getElementById("email").value, code }),
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) {
      err.textContent = data.detail || "That code is invalid or expired.";
      boxes.forEach((b) => { b.value = ""; });
      boxes[0].focus();
      return;
    }
    location.replace(next);
  }
})();
