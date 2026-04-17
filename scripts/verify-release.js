#!/usr/bin/env node
/**
 * Release verification for Grok Swarm.
 * Ensures the Claude marketplace bundle is self-contained and the npm tarball ships MCP assets.
 */
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const root = path.dirname(__dirname);

function assertExists(relativePath) {
  const fullPath = path.join(root, relativePath);
  if (!fs.existsSync(fullPath)) {
    throw new Error(`Missing required file: ${relativePath}`);
  }
}

function assertPortableClaudeMcpConfig() {
  const mcpPath = path.join(root, 'platforms/claude/.mcp.json');
  const raw = fs.readFileSync(mcpPath, 'utf8');
  const parsed = JSON.parse(raw);

  if (!parsed.mcpServers || !parsed.mcpServers['grok-swarm']) {
    throw new Error('Claude MCP config must use standard mcpServers.grok-swarm shape');
  }

  if (raw.includes('${PLUGIN_ROOT}')) {
    throw new Error('Claude MCP config must use ${CLAUDE_PLUGIN_ROOT}, not ${PLUGIN_ROOT}');
  }

  if (/\/Users\/|\/home\/|[A-Za-z]:\\/.test(raw)) {
    throw new Error('Claude MCP config contains a machine-local absolute path');
  }

  if (!raw.includes('${CLAUDE_PLUGIN_ROOT}/scripts/mcp-server.sh')) {
    throw new Error('Claude MCP config must launch the plugin-local MCP wrapper');
  }
}

function main() {
  const requiredClaudeFiles = [
    'platforms/claude/.claude-plugin/plugin.json',
    'platforms/claude/.claude-plugin/setup.sh',
    'platforms/claude/.mcp.json',
    'platforms/claude/commands/analyze.md',
    'platforms/claude/commands/code.md',
    'platforms/claude/commands/grok-swarm.md',
    'platforms/claude/commands/grok-swarm-analyze.md',
    'platforms/claude/commands/grok-swarm-code.md',
    'platforms/claude/commands/grok-swarm-reason.md',
    'platforms/claude/commands/grok-swarm-refactor.md',
    'platforms/claude/commands/grok-swarm-set-key.md',
    'platforms/claude/commands/grok-swarm-setup.md',
    'platforms/claude/commands/grok-swarm-stats.md',
    'platforms/claude/commands/reason.md',
    'platforms/claude/commands/refactor.md',
    'platforms/claude/commands/set-key.md',
    'platforms/claude/commands/setup.md',
    'platforms/claude/commands/setup.sh',
    'platforms/claude/commands/stats.md',
    'platforms/claude/scripts/bootstrap-runtime.sh',
    'platforms/claude/scripts/mcp-server.sh',
    'platforms/claude/src/requirements.txt',
    'platforms/claude/src/agent/grok_agent.py',
    'platforms/claude/src/bridge/cli.py',
    'platforms/claude/src/bridge/oauth_setup.py',
    'platforms/claude/src/mcp/grok_server.py',
    'platforms/claude/src/shared/patterns.py',
  ];

  requiredClaudeFiles.forEach(assertExists);
  assertPortableClaudeMcpConfig();

  const packJson = execFileSync('npm', ['pack', '--dry-run', '--json'], {
    cwd: root,
    encoding: 'utf8',
  });
  const packInfo = JSON.parse(packJson)[0];
  const tarballFiles = new Set((packInfo.files || []).map((entry) => entry.path));

  const requiredTarballFiles = [
    'bin/grok-swarm-mcp.js',
    'dist/index.js',
    'src/agent/grok_agent.py',
    'src/bridge/cli.py',
    'src/bridge/oauth_setup.py',
    'src/mcp/grok_server.py',
    'src/mcp/session.py',
  ];

  requiredTarballFiles.forEach((relativePath) => {
    if (!tarballFiles.has(relativePath)) {
      throw new Error(`npm tarball is missing required file: ${relativePath}`);
    }
  });

  console.log('Release verification passed.');
  console.log(`Verified Claude bundle files: ${requiredClaudeFiles.length}`);
  console.log(`Verified npm tarball files: ${requiredTarballFiles.length}`);
}

try {
  main();
} catch (error) {
  console.error(`Release verification failed: ${error.message}`);
  process.exit(1);
}
