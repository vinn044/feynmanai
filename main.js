const { app, BrowserWindow, ipcMain } = require("electron");
const { spawn } = require("child_process");
const path = require("path");

let py;

function createWindow() {
  const win = new BrowserWindow({
    width: 900,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
    },
  });

  win.loadFile("index.html");
}

app.whenReady().then(() => {
  py = spawn("python", ["engine.py"], {
  env: {
    ...process.env,
    PYTHONIOENCODING: "utf-8",
  },
});


  createWindow();
});

ipcMain.handle("chat", (_, message) => {
  return new Promise((resolve) => {
    py.stdin.write(message + "\n");
    py.stdout.once("data", (data) => {
  resolve(data.toString("utf8").trim());
});

  });
});
