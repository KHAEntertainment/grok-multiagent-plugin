#!/usr/bin/env node
/**
 * Test script for npm package.
 */
const { spawn } = require('child_process');
const path = require('path');

const grokBin = path.join(__dirname, '..', 'dist', 'index.js');

console.log('Running Grok Swarm CLI tests...\n');

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
