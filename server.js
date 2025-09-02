// server.js
const express = require('express');
const { exec } = require('child_process');
const path = require('path');
const app = express();
const port = 3000;

// Serve static files (HTML, CSS, JS) from the 'public' directory
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// --- Configuration ---
// Replace/add more servers as needed. Ensure your SSH key is set up.
const serverLocations = [
  { name: 'Server 1 (Primary)', ssh: 'almalinux@148.113.171.172' }
  // Add more servers if you have them:
  // { name: 'Server 2 (Secondary)', ssh: 'username@server_ip' },
  // { name: 'Server 3 (Tertiary)', ssh: 'username@server_ip' },
];

// --- API Endpoint ---
app.post('/run', async (req, res) => {
    const { host, tools } = req.body;
    if (!host || !tools || !Array.isArray(tools) || tools.length === 0) {
        return res.status(400).json({ error: 'Host and at least one tool are required.' });
    }

    // Function to run a command on a remote server via SSH
    const runRemoteCommand = (ssh, cmd) =>
        new Promise(resolve => {
            const command = `ssh -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=10 ${ssh} "${cmd}"`;
            exec(command, { timeout: 45000 }, (error, stdout, stderr) => {
                if (error) {
                    console.error(`Exec error for "${cmd}" on ${ssh}:`, error);
                    resolve(stderr || `Error: ${error.message}`);
                } else {
                    resolve(stdout);
                }
            });
        });

    // Map tools to shell commands
    const toolCommands = {
        ping:       (h) => `ping -c 4 ${h}`,
        traceroute: (h) => `traceroute ${h}`,
        // Updated MTR command to work on AlmaLinux
        mtr:        (h) => `mtr --report --report-cycles 4 ${h}`,
        // DNS Lookup (install 'bind-utils' on server for dig)
        dns:        (h) => `dig ${h}`,
    };

    try {
        const results = await Promise.all(serverLocations.map(async loc => {
            const locationResults = {};
            for (const tool of tools) {
                if (toolCommands[tool]) {
                    const command = toolCommands[tool](host);
                    locationResults[tool] = await runRemoteCommand(loc.ssh, command);
                }
            }
            return { name: loc.name, results: locationResults };
        }));
        res.json(results);
    } catch (error) {
        console.error('Failed to execute remote commands:', error);
        res.status(500).json({ error: 'A critical error occurred on the server.' });
    }
});

// Start server
app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
