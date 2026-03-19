#!/usr/bin/env node
/**
 * Pre-install check for npm package.
 * Validates Node.js version before installation.
 */
const MIN_NODE = 18;

const version = process.version.slice(1).split('.').map(Number);
const major = version[0];

if (major < MIN_NODE) {
  console.error(`ERROR: Node.js ${MIN_NODE}+ required, but found ${major}.`);
  console.error('Use nvm to install a newer version: nvm install 18');
  process.exit(1);
}

console.log(`Node.js ${major} detected — OK`);
