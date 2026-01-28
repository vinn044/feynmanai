const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("api", {
  chat: (message) => ipcRenderer.invoke("chat", message),
});
