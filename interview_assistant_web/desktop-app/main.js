/**
 * Interview Assistant - Electron Main Process
 * Manages the desktop application lifecycle
 */
const { app, BrowserWindow, Menu, Tray, shell, dialog, globalShortcut, ipcMain } = require('electron');
const path = require('path');
const { spawn, exec } = require('child_process');
const http = require('http');
const fs = require('fs');

// Environment
const isDev = !app.isPackaged;
const isMac = process.platform === 'darwin';
const isWin = process.platform === 'win32';

// Paths
const resourcesPath = isDev 
  ? path.join(__dirname, '..') 
  : path.join(process.resourcesPath);

const backendPath = isDev
  ? path.join(resourcesPath, 'backend')
  : path.join(resourcesPath, 'backend');

const frontendPath = isDev
  ? path.join(resourcesPath, 'frontend')
  : path.join(resourcesPath, 'frontend');

// Process references
let mainWindow = null;
let backendProcess = null;
let tray = null;

// Ports
const BACKEND_PORT = 8000;
const FRONTEND_PORT = isDev ? 3000 : 3000;

// App configuration
const APP_CONFIG = {
  width: 1400,
  height: 900,
  minWidth: 800,
  minHeight: 600,
};

/**
 * Create the main application window
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: APP_CONFIG.width,
    height: APP_CONFIG.height,
    minWidth: APP_CONFIG.minWidth,
    minHeight: APP_CONFIG.minHeight,
    title: 'Interview Assistant',
    icon: path.join(__dirname, 'resources', isMac ? 'icon.icns' : 'icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    titleBarStyle: isMac ? 'hiddenInset' : 'default',
    trafficLightPosition: { x: 15, y: 15 },
    backgroundColor: '#0a0a0f',
    show: false, // Don't show until ready
  });

  // Show when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  // Load the app
  const appUrl = `http://localhost:${FRONTEND_PORT}`;
  console.log(`Loading app from: ${appUrl}`);
  
  mainWindow.loadURL(appUrl).catch(err => {
    console.error('Failed to load app:', err);
    // Retry after delay
    setTimeout(() => {
      mainWindow.loadURL(appUrl);
    }, 2000);
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Cleanup on close
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/**
 * Start the Python backend server
 */
async function startBackend() {
  return new Promise((resolve, reject) => {
    console.log('Starting backend server...');
    
    const pythonCmd = isMac || !isWin ? 'python3' : 'python';
    const mainScript = path.join(backendPath, 'main.py');
    
    // Check if running bundled version
    const bundledBackend = path.join(backendPath, isMac ? 'backend' : 'backend.exe');
    
    let cmd, args;
    if (!isDev && fs.existsSync(bundledBackend)) {
      // Use bundled executable
      cmd = bundledBackend;
      args = [];
      console.log('Using bundled backend:', cmd);
    } else {
      // Use Python script
      cmd = pythonCmd;
      args = [mainScript];
      console.log('Using Python backend:', mainScript);
    }

    // Set environment variables
    const env = {
      ...process.env,
      PORT: BACKEND_PORT.toString(),
      HOST: '127.0.0.1',
    };

    backendProcess = spawn(cmd, args, {
      cwd: backendPath,
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    backendProcess.stdout.on('data', (data) => {
      console.log(`[Backend] ${data.toString().trim()}`);
    });

    backendProcess.stderr.on('data', (data) => {
      console.error(`[Backend] ${data.toString().trim()}`);
    });

    backendProcess.on('error', (err) => {
      console.error('Backend process error:', err);
      reject(err);
    });

    backendProcess.on('exit', (code) => {
      console.log(`Backend process exited with code ${code}`);
      backendProcess = null;
    });

    // Wait for backend to be ready
    waitForServer(`http://localhost:${BACKEND_PORT}/health`, 30000)
      .then(() => {
        console.log('Backend server is ready!');
        resolve();
      })
      .catch(reject);
  });
}

/**
 * Start the Next.js frontend (dev mode only)
 */
async function startFrontend() {
  if (!isDev) {
    // In production, serve static files or use next start
    return startProductionFrontend();
  }

  return new Promise((resolve, reject) => {
    console.log('Starting frontend dev server...');
    
    const npmCmd = isWin ? 'npm.cmd' : 'npm';
    
    const frontendProcess = spawn(npmCmd, ['run', 'dev'], {
      cwd: frontendPath,
      env: { ...process.env, PORT: FRONTEND_PORT.toString() },
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: true,
    });

    frontendProcess.stdout.on('data', (data) => {
      console.log(`[Frontend] ${data.toString().trim()}`);
    });

    frontendProcess.stderr.on('data', (data) => {
      console.error(`[Frontend] ${data.toString().trim()}`);
    });

    // Wait for frontend to be ready
    waitForServer(`http://localhost:${FRONTEND_PORT}`, 60000)
      .then(() => {
        console.log('Frontend server is ready!');
        resolve();
      })
      .catch(reject);
  });
}

/**
 * Start production frontend server
 */
async function startProductionFrontend() {
  return new Promise((resolve, reject) => {
    console.log('Starting production frontend...');
    
    const npmCmd = isWin ? 'npm.cmd' : 'npm';
    
    const frontendProcess = spawn(npmCmd, ['run', 'start'], {
      cwd: frontendPath,
      env: { ...process.env, PORT: FRONTEND_PORT.toString() },
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: true,
    });

    frontendProcess.stdout.on('data', (data) => {
      console.log(`[Frontend] ${data.toString().trim()}`);
    });

    frontendProcess.stderr.on('data', (data) => {
      console.error(`[Frontend] ${data.toString().trim()}`);
    });

    waitForServer(`http://localhost:${FRONTEND_PORT}`, 30000)
      .then(resolve)
      .catch(reject);
  });
}

/**
 * Wait for a server to be ready
 */
function waitForServer(url, timeout = 30000) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    const check = () => {
      http.get(url, (res) => {
        if (res.statusCode === 200) {
          resolve();
        } else {
          retry();
        }
      }).on('error', retry);
    };

    const retry = () => {
      if (Date.now() - startTime > timeout) {
        reject(new Error(`Server at ${url} did not start within ${timeout}ms`));
      } else {
        setTimeout(check, 500);
      }
    };

    check();
  });
}

/**
 * Create application menu
 */
function createMenu() {
  const template = [
    ...(isMac ? [{
      label: app.name,
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    }] : []),
    {
      label: 'File',
      submenu: [
        {
          label: 'New Chat',
          accelerator: 'CmdOrCtrl+N',
          click: () => {
            mainWindow?.webContents.send('menu-action', 'new-chat');
          }
        },
        { type: 'separator' },
        isMac ? { role: 'close' } : { role: 'quit' }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'zoom' },
        ...(isMac ? [
          { type: 'separator' },
          { role: 'front' }
        ] : [
          { role: 'close' }
        ])
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Documentation',
          click: () => {
            shell.openExternal('https://techyera.co/docs');
          }
        },
        {
          label: 'Report Issue',
          click: () => {
            shell.openExternal('https://github.com/techyera/interview-assistant/issues');
          }
        },
        { type: 'separator' },
        {
          label: 'About Interview Assistant',
          click: () => {
            dialog.showMessageBox({
              type: 'info',
              title: 'About Interview Assistant',
              message: 'Interview Assistant',
              detail: `Version: ${app.getVersion()}\n\nAI-powered interview preparation tool with real-time transcription.\n\n© 2024 TechYera`
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

/**
 * Register global shortcuts
 */
function registerGlobalShortcuts() {
  // These are handled by the web app, but we can add Electron-level shortcuts here
  globalShortcut.register('CommandOrControl+Shift+I', () => {
    mainWindow?.webContents.toggleDevTools();
  });
}

/**
 * Cleanup and shutdown
 */
function cleanup() {
  console.log('Cleaning up...');
  
  // Unregister shortcuts
  globalShortcut.unregisterAll();
  
  // Kill backend process
  if (backendProcess) {
    console.log('Stopping backend server...');
    if (isWin) {
      exec(`taskkill /pid ${backendProcess.pid} /T /F`);
    } else {
      backendProcess.kill('SIGTERM');
    }
    backendProcess = null;
  }
}

// App lifecycle events
app.whenReady().then(async () => {
  console.log('Interview Assistant starting...');
  console.log('Platform:', process.platform);
  console.log('Dev mode:', isDev);
  
  try {
    // Start backend first
    await startBackend();
    
    // Start frontend (in dev) or wait for it to be available
    if (isDev) {
      await startFrontend();
    }
    
    // Create window
    createWindow();
    createMenu();
    registerGlobalShortcuts();
    
    // macOS: Re-create window when dock icon clicked
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
      }
    });
    
  } catch (error) {
    console.error('Failed to start application:', error);
    dialog.showErrorBox('Startup Error', `Failed to start Interview Assistant:\n${error.message}`);
    app.quit();
  }
});

// Quit when all windows closed (except on macOS)
app.on('window-all-closed', () => {
  if (!isMac) {
    app.quit();
  }
});

// Cleanup before quit
app.on('before-quit', cleanup);
app.on('will-quit', cleanup);

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  cleanup();
});


