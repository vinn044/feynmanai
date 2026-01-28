const chat = document.getElementById("chat");
const input = document.getElementById("input");
const send = document.getElementById("send");

function addMessage(text, sender) {
  const msg = document.createElement("div");
  msg.className = sender;
  msg.textContent = text;
  chat.appendChild(msg);
  chat.scrollTop = chat.scrollHeight;
}

send.onclick = async () => {
  const message = input.value.trim();
  if (!message) return;

  addMessage(message, "user");
  input.value = "";

  const reply = await window.api.chat(message);
  addMessage(reply, "ai");
};

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") send.click();
});
