(() => {
  const demos = {
    share: {
      title: "Hide from share",
      body: "The Live overlay can be excluded from screen capture on macOS and Windows so your interviewer sees the call — not the copilot chrome.",
    },
    dock: {
      title: "Dock / taskbar hidden",
      body: "On Mac the native overlay stays out of the Dock. On Windows it uses a tool window so it does not sit on the taskbar.",
    },
    click: {
      title: "Click-through overlay",
      body: "Clicks pass through the answer pane to the app below. A separate control strip stays clickable so you can always turn it off or close.",
    },
  };

  document.querySelectorAll("#privacy-tabs li").forEach((item) => {
    item.addEventListener("click", () => {
      document.querySelectorAll("#privacy-tabs li").forEach((n) => n.classList.remove("active"));
      item.classList.add("active");
      const demo = demos[item.dataset.tab] || demos.share;
      document.getElementById("privacy-demo").innerHTML =
        `<p><b>${demo.title}</b></p><p class="muted">${demo.body}</p>`;
    });
  });

  const faqs = {
    features: [
      ["What languages does Interview Copilot support?", "Set the session language when you start Live or Studio. Transcription follows that language; switch it if the call changes."],
      ["Does it support coding calls?", "Yes. Studio and Live can take a screenshot of the problem, attach documents, and stream an approach while the call is going."],
      ["Can I give it instructions during the call?", "Upload a resume or docs, fill Live session notes, and send mid-call chat. Prompt tabs from your local tabs.json still apply in Studio."],
      ["Can I use headphones?", "Yes. The web companion uses the browser microphone you pick. Desktop BlackHole remains the desktop-app path for system audio."],
    ],
    privacy: [
      ["Will it hide from Activity Monitor / Task Manager?", "No. We do not disguise the process, spoof the cursor, or fake tab switches. Those are out of scope."],
      ["What does Hide from share actually do?", "On macOS the native overlay requests capture-exclusion. On Windows it uses SetWindowDisplayAffinity so sharing tools omit that window. The control strip stays clickable."],
      ["Is this for secretly cheating in interviews?", "No. Use it where AI assistance is permitted. Check the rules first."],
    ],
    account: [
      ["How do I sign in?", "Google OAuth if you set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET, or email with a one-time code. Local accounts live in data/users.json."],
      ["Do I need a credit card?", "No. This companion uses your OPENAI_API_KEY. There is no copilot subscription in this build."],
      ["Can I use desktop and web at once?", "Yes. They share the same local JSON stores under interview_copilot/data/."],
    ],
  };

  const list = document.getElementById("faq-list");
  function renderFaq(cat) {
    list.innerHTML = faqs[cat].map(([q, a]) =>
      `<div class="faq-item"><button type="button">${q}<span>+</span></button><p>${a}</p></div>`
    ).join("");
    list.querySelectorAll(".faq-item button").forEach((btn) => {
      btn.addEventListener("click", () => btn.parentElement.classList.toggle("open"));
    });
  }
  renderFaq("features");
  document.querySelectorAll("#faq-cats button").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#faq-cats button").forEach((b) => b.classList.remove("on"));
      btn.classList.add("on");
      renderFaq(btn.dataset.cat);
    });
  });

  document.querySelectorAll("#price-seg button").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#price-seg button").forEach((b) => b.classList.remove("on"));
      btn.classList.add("on");
    });
  });
})();
