const { app, BrowserWindow, ipcMain } = require("electron");
const { spawn } = require("child_process");
const path = require("path");

let py;
let voiceSessionActive = false;
let mainWindow;
let buffer = "";

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
    },
  });

  mainWindow.loadFile("index.html");
}

app.whenReady().then(() => {
  py = spawn("python", ["engine.py"], {
    env: {
      ...process.env,
      PYTHONIOENCODING: "utf-8",
    },
  });

  py.stdout.on("data", (data) => {
    buffer += data.toString("utf8");
    
    // Process complete lines
    const lines = buffer.split("\n");
    buffer = lines.pop(); // Keep incomplete line in buffer
    
    lines.forEach(line => {
      line = line.trim();
      if (!line) return;
      
      if (line.startsWith("AUDIO:")) {
        // Extract and send audio data
        try {
          const audioJson = line.substring(6); // Remove "AUDIO:" prefix
          const audioData = JSON.parse(audioJson);
          if (mainWindow && Array.isArray(audioData)) {
            mainWindow.webContents.send("audio-response", audioData);
          }
        } catch (e) {
          console.error("Failed to parse audio JSON:", e.message);
        }
      } else {
        // Regular JSON message
        try {
          const msg = JSON.parse(line);
          console.log("Message from Python:", msg);
        } catch (e) {
          // Not JSON, ignore
        }
      }
    });
  });

  py.stderr.on("data", (data) => {
    console.error("Python stderr:", data.toString());
  });

  createWindow();
});

ipcMain.handle("chat", (_, message) => {
  return new Promise((resolve) => {
    py.stdin.write(JSON.stringify({ type: "text", content: message }) + "\n");
    py.stdout.once("data", (data) => {
      const response = data.toString("utf8").trim();
      try {
        const parsed = JSON.parse(response);
        resolve(parsed.content || response);
      } catch {
        resolve(response);
      }
    });
  });
});

ipcMain.handle("startVoiceSession", async () => {
  voiceSessionActive = true;
  py.stdin.write(JSON.stringify({ type: "voice_start" }) + "\n");
  console.log("Voice session started");
  return true;
});

ipcMain.handle("stopVoiceSession", async () => {
  voiceSessionActive = false;
  py.stdin.write(JSON.stringify({ type: "voice_stop" }) + "\n");
  console.log("Voice session stopped");
  return true;
});

ipcMain.handle("sendAudioData", (_, audioData) => {
  if (voiceSessionActive && py && py.stdin) {
    py.stdin.write(JSON.stringify({ type: "audio", data: audioData }) + "\n");
  }
  return true;
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});