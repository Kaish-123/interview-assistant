/**
 * Preload script for Interview Assistant
 * Provides secure bridge between renderer and main process
 */
const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to renderer
contextBridge.exposeInMainWorld('electronAPI', {
  // App info
  getVersion: () => ipcRenderer.invoke('get-version'),
  getPlatform: () => process.platform,
  
  // Menu actions
  onMenuAction: (callback) => {
    ipcRenderer.on('menu-action', (event, action) => callback(action));
  },
  
  // Window controls
  minimize: () => ipcRenderer.send('window-minimize'),
  maximize: () => ipcRenderer.send('window-maximize'),
  close: () => ipcRenderer.send('window-close'),
  
  // File operations
  openFile: () => ipcRenderer.invoke('open-file'),
  saveFile: (content, filename) => ipcRenderer.invoke('save-file', content, filename),
  
  // Notifications
  showNotification: (title, body) => ipcRenderer.send('show-notification', title, body),
  
  // Global hotkeys (these work even when app not focused)
  registerGlobalHotkey: (accelerator, callback) => {
    ipcRenderer.send('register-global-hotkey', accelerator);
    ipcRenderer.on(`global-hotkey-${accelerator}`, callback);
  },
  unregisterGlobalHotkey: (accelerator) => {
    ipcRenderer.send('unregister-global-hotkey', accelerator);
  },
});

// Log when preload is complete
console.log('Preload script loaded');

