#!/usr/bin/env node
/**
 * Cross-platform wrapper for the Grok Swarm MCP server.
 * Spawns python3 (or python on Windows) to run grok_server.py,
 * forwarding stdin/stdout for the MCP stdio transport.
 */
const { spawn } = require('child_process');
const path = require('path');

const serverScript = path.join(__dirname, '..', 'src', 'mcp', 'grok_server.py');

// Try python3 first, fall back to python (common on Windows)
const pythonCandidates = process.platform === 'win32'
  ? ['python3', 'python']
  : ['python3'];

function trySpawn(candidates) {
  const cmd = candidates[0];
  if (!cmd) {
    process.stderr.write(
      'ERROR: Python 3 not found. Install Python 3.8+ and ensure python3 (or python) is on PATH.\n'
    );
    process.exit(1);
  }

  const child = spawn(cmd, [serverScript], {
    stdio: ['inherit', 'inherit', 'inherit'],
  });

  child.on('error', (err) => {
    if (err.code === 'ENOENT' && candidates.length > 1) {
      // python3 not found, try next candidate
      trySpawn(candidates.slice(1));
    } else {
      process.stderr.write(`ERROR: Failed to start MCP server: ${err.message}\n`);
      process.exit(1);
    }
  });

  child.on('exit', (code) => {
    process.exit(code || 0);
  });
}

trySpawn(pythonCandidates);
