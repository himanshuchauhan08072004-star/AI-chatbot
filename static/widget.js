/* Embed on any site:
   <link rel="stylesheet" href="https://YOUR-HOST/static/widget.css">
   <script src="https://YOUR-HOST/static/widget.js" data-api="https://YOUR-HOST"></script>
   (set ALLOWED_ORIGINS on the server for cross-site embedding) */
(function () {
  var script = document.currentScript;
  var API = (script && script.getAttribute("data-api")) || "";
  var QUICK = ["Services", "Pricing", "Internships", "Contact"];
  var KEY = "ca_chat_session";

  function newId() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID().replace(/-/g, "");
    return (Date.now().toString(36) + Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2)).padEnd(24, "0");
  }
  function getSession() {
    var id = null;
    try { id = localStorage.getItem(KEY); } catch (e) {}
    if (!id) { id = newId(); try { localStorage.setItem(KEY, id); } catch (e) {} }
    return id;
  }
  var session = getSession();

  var btn = document.createElement("button");
  btn.id = "ca-chat-btn"; btn.innerHTML = "&#128172;"; btn.setAttribute("aria-label", "Open chat");
  var box = document.createElement("div");
  box.id = "ca-chat-box"; box.setAttribute("role", "dialog"); box.setAttribute("aria-label", "Chat assistant");
  box.innerHTML =
    '<div class="ca-head"><span>CodeAlpha Assistant</span><span><button class="ca-clear" title="Clear chat history" aria-label="Clear chat">&#128465;</button><button class="ca-close" aria-label="Close">&times;</button></span></div>' +
    '<div class="ca-msgs" aria-live="polite"></div><div class="ca-chips"></div>' +
    '<div class="ca-input"><input type="text" maxlength="500" placeholder="Type your question..." aria-label="Message"><button class="ca-send">Send</button></div>';
  document.body.appendChild(btn); document.body.appendChild(box);

  var msgs = box.querySelector(".ca-msgs"), input = box.querySelector("input"),
      chips = box.querySelector(".ca-chips"), sendBtn = box.querySelector(".ca-send");
  var pending = false, loaded = false;

  var BADGES = { ai: "AI answer", retrieval: "From site documents (no AI)", rules: "Auto-reply (no AI)", fallback: "Auto-reply (no AI)" };

  function add(text, who, mode) {
    var d = document.createElement("div");
    d.className = "ca-msg " + who; d.textContent = text;
    if (who === "bot" && mode && BADGES[mode]) {
      var b = document.createElement("div"); b.className = "ca-badge"; b.textContent = BADGES[mode]; d.appendChild(b);
    }
    msgs.appendChild(d); msgs.scrollTop = msgs.scrollHeight; return d;
  }
  function welcome() { add("Hi! I'm the CodeAlpha assistant. Ask me anything.", "bot"); }
  function setPending(v) { pending = v; sendBtn.disabled = v; input.disabled = v; }

  function loadHistory() {
    if (loaded) return; loaded = true;
    fetch(API + "/api/history/" + session)
      .then(function (r) { return r.ok ? r.json() : { messages: [] }; })
      .then(function (d) {
        if (!d.messages.length) return welcome();
        d.messages.forEach(function (m) { add(m.content, m.role === "user" ? "user" : "bot", m.mode); });
      })
      .catch(welcome);
  }

  function send(text) {
    text = (text || input.value).trim();
    if (!text || pending) return;
    add(text, "user"); input.value = ""; setPending(true);
    var t = document.createElement("div");
    t.className = "ca-typing"; t.textContent = "typing...";
    msgs.appendChild(t); msgs.scrollTop = msgs.scrollHeight;
    fetch(API + "/api/chat", { method: "POST", headers: { "Content-Type": "application/json" },
                               body: JSON.stringify({ message: text, session_id: session }) })
      .then(function (r) {
        if (r.status === 429) throw new Error("Too many messages. Please wait a minute and try again.");
        if (r.status === 422) throw new Error("Message not accepted. Please check it and try again.");
        if (!r.ok) throw new Error("Server error. Please try again shortly.");
        return r.json();
      })
      .then(function (d) {
        t.remove(); add(d.reply, "bot", d.mode);
        if (d.ai_unavailable) add("AI service is currently unavailable; this is an automatic fallback reply.", "note");
      })
      .catch(function (e) {
        t.remove();
        add(e instanceof TypeError ? "Server unreachable. Please check your connection and try again." : e.message, "note");
      })
      .then(function () { setPending(false); input.focus(); });
  }

  QUICK.forEach(function (q) {
    var b = document.createElement("button"); b.textContent = q;
    b.onclick = function () { send(q); }; chips.appendChild(b);
  });
  btn.onclick = function () {
    box.classList.toggle("open");
    if (box.classList.contains("open")) { loadHistory(); input.focus(); }
  };
  box.querySelector(".ca-close").onclick = function () { box.classList.remove("open"); };
  box.querySelector(".ca-clear").onclick = function () {
    if (!confirm("Delete this conversation?")) return;
    fetch(API + "/api/history/" + session, { method: "DELETE" }).finally(function () {
      msgs.innerHTML = ""; welcome();
    });
  };
  sendBtn.onclick = function () { send(); };
  input.addEventListener("keydown", function (e) { if (e.key === "Enter") send(); });
})();
