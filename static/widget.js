/* Embed on any site:
   <link rel="stylesheet" href="https://YOUR-HOST/static/widget.css">
   <script src="https://YOUR-HOST/static/widget.js" data-api="https://YOUR-HOST"></script> */
(function () {
  var script = document.currentScript;
  var API = (script && script.getAttribute("data-api")) || "";
  var QUICK = ["Services", "Pricing", "Internships", "Contact"];

  var btn = document.createElement("button");
  btn.id = "ca-chat-btn"; btn.innerHTML = "&#128172;"; btn.setAttribute("aria-label", "Open chat");
  var box = document.createElement("div");
  box.id = "ca-chat-box";
  box.innerHTML =
    '<div class="ca-head"><span>CodeAlpha Assistant</span><button aria-label="Close">&times;</button></div>' +
    '<div class="ca-msgs"></div><div class="ca-chips"></div>' +
    '<div class="ca-input"><input type="text" maxlength="500" placeholder="Type your question..."><button>Send</button></div>';
  document.body.appendChild(btn); document.body.appendChild(box);

  var msgs = box.querySelector(".ca-msgs"), input = box.querySelector("input"), chips = box.querySelector(".ca-chips");

  function add(text, who) {
    var d = document.createElement("div");
    d.className = "ca-msg " + who; d.textContent = text;
    msgs.appendChild(d); msgs.scrollTop = msgs.scrollHeight; return d;
  }
  function send(text) {
    text = (text || input.value).trim();
    if (!text) return;
    add(text, "user"); input.value = "";
    var t = document.createElement("div");
    t.className = "ca-typing"; t.textContent = "typing...";
    msgs.appendChild(t); msgs.scrollTop = msgs.scrollHeight;
    fetch(API + "/api/chat", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({message: text})})
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) { t.remove(); add(d.reply, "bot"); })
      .catch(function () { t.remove(); add("Server unreachable. Please try again shortly.", "bot"); });
  }
  QUICK.forEach(function (q) {
    var b = document.createElement("button"); b.textContent = q;
    b.onclick = function () { send(q); }; chips.appendChild(b);
  });
  btn.onclick = function () {
    box.classList.toggle("open");
    if (box.classList.contains("open") && !msgs.children.length) add("Hi! I'm the CodeAlpha assistant. Ask me anything.", "bot");
    input.focus();
  };
  box.querySelector(".ca-head button").onclick = function () { box.classList.remove("open"); };
  box.querySelector(".ca-input button").onclick = function () { send(); };
  input.addEventListener("keydown", function (e) { if (e.key === "Enter") send(); });
})();
