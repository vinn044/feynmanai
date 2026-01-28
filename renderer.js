const chat = document.getElementById("chat");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");

function addMessage(text, role) {
  const div = document.createElement("div");
  div.classList.add("message", role);
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;

  addMessage(text, "user");
  input.value = "";
  input.focus();

  const typing = document.createElement("div");
  typing.classList.add("message", "ai");
  typing.textContent = "Thinking…";
  chat.appendChild(typing);
  chat.scrollTop = chat.scrollHeight;

  // Force UI to render before waiting on Python
  await new Promise(requestAnimationFrame);

  const response = await window.api.chat(text);

  typing.remove();
  addMessage(response, "ai");
}

sendBtn.addEventListener("click", sendMessage);

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    sendMessage();
  }
});

/* AI GREETS ON LAUNCH */
window.addEventListener("DOMContentLoaded", async () => {
  const opening = await window.api.chat("");
  addMessage(opening, "ai");
});
