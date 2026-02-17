const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("api", {
  chat: (message) => ipcRenderer.invoke("chat", message),
  startVoiceSession: () => ipcRenderer.invoke("startVoiceSession"),
  stopVoiceSession: () => ipcRenderer.invoke("stopVoiceSession"),
  sendAudioData: (audioData) => ipcRenderer.invoke("sendAudioData", audioData),
  onAudioResponse: (callback) => {
    ipcRenderer.on("audio-response", (_, data) => callback(data));
  },
});