const { app, BrowserWindow } = require('electron');
const path = require('path');
const url = require('url');
const config = require('./config.js');
const childProcess = require('child_process');
const psTree = require('ps-tree');

let mainWindow;
let pythonProcess;

function createWindow () {
  startUrl = "";
  if (process.env.ENVIRONMENT == config.PROD) {
    pythonProcess=childProcess.execFile(config.PROD_ENTRY)
    startUrl = url.format({
      pathname: config.REACT_ENTRY,
      protocol: 'file:',
      slashes: true,
    });
  }
  // This part doesn't really work for some reason ...
  else if (process.env.ENVIRONMENT == config.DEV) {
    startUrl = process.env.ELECTRON_START_URL;
    pythonProcess=childProcess.exec(config.RUN_METHOD,[config.PYTHON_ENTRY]);
  }
  else {  // Production
    startUrl = process.env.ELECTRON_START_URL;
  }
  mainWindow = new BrowserWindow({
    width: config.WIN_WIDTH,
    height: config.WIN_HEIGHT,
    icon:path.join(__dirname,'..','public','icon.png'),
    webPreferences: {
      nodeIntegration: true,
      // devTools: false // for production
    }
  });
  mainWindow.loadURL(startUrl);
  mainWindow.on('closed', function () {
    mainWindow = null;
  });

  if (process.env.ENVIRONMENT == config.DEBUG) {
    mainWindow.webContents.openDevTools()
  }

}
app.on('ready', () => {
  createWindow()
});
const deleteChildren = (rootPid) => {
  let cleanup_completed = false;

  psTree(rootPid, (err, children) => {
    children.map((p) => {
      process.kill(p.PID);
    });

    cleanup_completed = true;
  });
  return new Promise((resolve, reject) => {
    (function waitForSubProcessCleanup() {
      if (cleanup_completed) return resolve();
      setTimeout(waitForSubProcessCleanup, 30);
    })();
  });
};

// Quit when all windows are closed.
app.on('window-all-closed', async () => {
  if (pythonProcess != null) {
    deleteChildren(pythonProcess.pid).then(() => {
      //deleteChildren seems to also kill pythonProcess on Windows
      //but not on Mac
      if (pythonProcess != null) {
        pythonProcess.kill();
      }
      app.quit();
    });
  }
});

app.on('activate', function () {
  if (mainWindow === null) {
    createWindow();
  }
});
