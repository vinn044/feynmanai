const chat = document.getElementById("chat");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");

let isVoiceCall = false;
let voiceCallBtn;

class AudioHandler {
  constructor() {
    this.audioContext = null;
    this.audioQueue = [];
    this.isPlaying = false;
  }

  async startRecording() {
    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const source = this.audioContext.createMediaStreamSource(this.mediaStream);
      const processor = this.audioContext.createScriptProcessor(4096, 1, 1);

      source.connect(processor);
      processor.connect(this.audioContext.destination);

      let bufferSize = 0;
      processor.onaudioprocess = (e) => {
        const audioData = e.inputBuffer.getChannelData(0);
        bufferSize++;
        
        // Send every 10 chunks (about once per 0.1 seconds)
        if (bufferSize % 10 === 0) {
          window.api.sendAudioData(Array.from(audioData));
        }
      };

      this.processor = processor;
      return true;
    } catch (error) {
      console.error("Microphone access denied:", error);
      addMessage("❌ Microphone access denied", "system");
      return false;
    }
  }

  stopRecording() {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
    }
    if (this.processor) {
      this.processor.disconnect();
    }
  }

  async queueAudio(audioData) {
    if (!this.audioContext) {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }

    this.audioQueue.push(audioData);
    
    if (!this.isPlaying) {
      this.processQueue();
    }
  }

  async processQueue() {
    if (this.audioQueue.length === 0) {
      this.isPlaying = false;
      return;
    }

    this.isPlaying = true;
    const audioData = this.audioQueue.shift();

    try {
      const audioBuffer = this.audioContext.createBuffer(1, audioData.length, 24000);
      const channelData = audioBuffer.getChannelData(0);
      channelData.set(audioData);

      const source = this.audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(this.audioContext.destination);

      // Wait for this audio to finish before playing next
      source.onended = () => {
        this.processQueue();
      };

      source.start(0);
    } catch (error) {
      console.error("Error playing audio:", error);
      this.processQueue(); // Continue with next audio if error
    }
  }
}

const audioHandler = new AudioHandler();

function setupVoiceButton() {
  voiceCallBtn = document.createElement("button");
  voiceCallBtn.id = "voice-call";
  voiceCallBtn.textContent = "🎤 Voice Call";
  
  const inputBar = document.getElementById("input-bar");
  inputBar.appendChild(voiceCallBtn);

  voiceCallBtn.addEventListener("click", toggleVoiceCall);
}

async function toggleVoiceCall() {
  if (!isVoiceCall) {
    const success = await audioHandler.startRecording();
    if (success) {
      isVoiceCall = true;
      voiceCallBtn.textContent = "🔴 Stop Call";
      voiceCallBtn.classList.add("active");
      await window.api.startVoiceSession();
      addMessage("🎤 Voice call started. Speak naturally!", "system");
    }
  } else {
    voiceCallBtn.textContent = "🎤 Voice Call";
    voiceCallBtn.classList.remove("active");
    audioHandler.stopRecording();
    await window.api.stopVoiceSession();
    isVoiceCall = false;
    addMessage("📞 Voice call ended.", "system");
  }
}

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

// Listen for audio responses from the AI
window.api.onAudioResponse((audioData) => {
  audioHandler.queueAudio(audioData);
});

window.addEventListener("DOMContentLoaded", async () => {
  setupVoiceButton();
  const opening = await window.api.chat("");
  addMessage(opening, "ai");
});