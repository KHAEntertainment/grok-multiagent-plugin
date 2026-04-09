#!/usr/bin/env node
/**
 * Test script for npm package and Claude bundle sanity.
 */
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const grokBin = path.join(root, 'dist', 'index.js');
const requiredClaudeCommands = [
  'platforms/claude/commands/grok-swarm.md',
  'platforms/claude/commands/grok-swarm-setup.md',
  'platforms/claude/commands/grok-swarm-analyze.md',
  'platforms/claude/commands/grok-swarm-refactor.md',
  'platforms/claude/commands/grok-swarm-code.md',
  'platforms/claude/commands/grok-swarm-reason.md',
  'platforms/claude/commands/grok-swarm-stats.md',
  'platforms/claude/commands/grok-swarm-set-key.md',
  'platforms/claude/commands/setup.sh',
];

console.log('Running Grok Swarm CLI tests...\n');

const missingFiles = requiredClaudeCommands.filter((relativePath) => {
  return !fs.existsSync(path.join(root, relativePath));
});

if (missingFiles.length > 0) {
  console.log('✗ Claude bundle command files missing');
  missingFiles.forEach((relativePath) => console.log(`  - ${relativePath}`));
  process.exit(1);
}

console.log(`✓ Claude bundle command files present (${requiredClaudeCommands.length})`);

// Test: grok-swarm --help
const help = spawn('node', [grokBin, '--help'], { stdio: 'pipe' });

let helpOutput = '';
help.stdout.on('data', d => helpOutput += d);
help.stderr.on('data', d => helpOutput += d);

help.on('close', code => {
  if (code === 0 && helpOutput.includes('grok-swarm')) {
    console.log('✓ CLI --help works');
  } else {
    console.log('✗ CLI --help failed');
    console.log(helpOutput);
    process.exit(1);
  }
});
