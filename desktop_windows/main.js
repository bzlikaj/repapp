const { app, BrowserWindow } = require('electron');

function createWindow() {
  const url = process.env.REPAPP_URL;
  if (!url) {
    // Per sicurezza: obbliga a impostare l'URL della tua app online.
    throw new Error('Imposta REPAPP_URL (es. https://tua-app.onrender.com)');
  }

  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: __dirname + '/preload.js'
    }
  });

  win.loadURL(url);
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
