#!/usr/bin/env node
/**
 * Post-install script for npm package.
 * Validates environment and prints setup instructions.
 */
const fs = require('fs');
const os = require('os');
const path = require('path');

const configDir = path.join(os.homedir(), '.config', 'grok-swarm');
const configFile = path.join(configDir, 'config.json');

console.log('Grok Swarm CLI installed successfully!');
console.log('');

// Check for existing API key
const hasConfig = fs.existsSync(configFile);
const hasEnvKey = process.env.OPENROUTER_API_KEY || process.env.XAI_API_KEY;

if (hasEnvKey) {
  console.log('✓ API key found in environment');
} else if (hasConfig) {
  console.log('✓ API key found in config file');
} else {
  console.log('⚠ No API key configured yet');
  console.log('');
  console.log('Set OPENROUTER_API_KEY=sk-or-v1-... or create ~/.config/grok-swarm/config.json');
  console.log('Get a key at: https://openrouter.ai/keys');
}

console.log('');
console.log('Usage: grok-swarm <mode> --prompt "your task"');
console.log('Try:   grok-swarm --help');
