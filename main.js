const { app, BrowserWindow, Tray, Menu } = require('electron');
const path = require('path');
const sudo = require('sudo-prompt');  // Import sudo-prompt
const os = require('os');

let mainWindow;
let tray;

// Paths setup using user's Program Files directory
const programFilesDir = 'C:\\Program Files\\DLP';
const flaskPath = path.join(programFilesDir, 'attempt', 'flaskEnd', 'dist', 'flask_app.exe');
const reactPath = path.join(programFilesDir, 'attempt', 'pg1');
const reactBuildPath = path.join(reactPath, 'build');

function createWindow() {
    if (mainWindow) {
        mainWindow.focus();
        return;
    }

    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
        }
    });

    // Load the React build (production) index.html file
    mainWindow.loadFile(path.join(reactBuildPath, 'index.html')).catch(() => {
        console.error("Failed to load the React build index.html");
    });

    mainWindow.on('closed', () => mainWindow = null);
}

// Start Flask server with sudo-prompt for elevated privileges
const flaskCommand = `"${flaskPath}"`;  // Full path to the executable
sudo.exec(flaskCommand, { name: 'DLP Admin' }, (error, stdout, stderr) => {
    if (error) {
        console.error(`Error starting Flask server: ${error}`);
        return;
    }
    console.log(`Flask server output: ${stdout}`);
});

// Start React server with sudo-prompt
const reactCommand = `npm start --prefix "${reactPath}"`;
sudo.exec(reactCommand, { name: 'DLP Admin' }, (error, stdout, stderr) => {
    if (error) {
        console.error(`Error starting React server: ${error}`);
        return;
    }
    console.log(`React server output: ${stdout}`);
});

app.on('ready', () => {
    // Create the tray icon
    tray = new Tray(path.join(__dirname, 'icon.jpeg'));

    // Define toggle function
    function toggleWindow() {
        if (mainWindow && mainWindow.isVisible()) {
            mainWindow.hide();
        } else {
            createWindow();
        }
    }

    // Set up the tray context menu with Show, Hide, and Quit options
    const contextMenu = Menu.buildFromTemplate([
        { label: 'Show App', click: () => mainWindow ? mainWindow.show() : createWindow() },
        { label: 'Hide App', click: () => mainWindow && mainWindow.hide() },
        { label: 'Quit', click: () => {
            app.quit();
        }},
    ]);

    // Assign the menu to the tray icon
    tray.setContextMenu(contextMenu);
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (!mainWindow) createWindow();
});
