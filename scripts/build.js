#!/usr/bin/env node
/**
 * Build script for npm package.
 * Copies source files to dist/ for publishing.
 */
const fs = require('fs');
const path = require('path');

const root = path.dirname(__dirname);
const dist = path.join(root, 'dist');

function copyRecursive(src, dest) {
  if (!fs.existsSync(src)) return;
  
  const stat = fs.statSync(src);
  if (stat.isDirectory()) {
    if (!fs.existsSync(dest)) {
      fs.mkdirSync(dest, { recursive: true });
    }
    fs.readdirSync(src).forEach(child => {
      copyRecursive(path.join(src, child), path.join(dest, child));
    });
  } else {
    fs.copyFileSync(src, dest);
  }
}

// Clean dist
if (fs.existsSync(dist)) {
  fs.rmSync(dist, { recursive: true });
}
fs.mkdirSync(dist, { recursive: true });

// Copy Node wrapper and bridge
copyRecursive(path.join(root, 'src/bridge/index.js'), path.join(dist, 'index.js'));
copyRecursive(path.join(root, 'src/bridge/grok_bridge.py'), path.join(dist, 'grok_bridge.py'));
copyRecursive(path.join(root, 'src/bridge/apply.py'), path.join(dist, 'apply.py'));
copyRecursive(path.join(root, 'src/bridge/cli.py'), path.join(dist, 'cli.py'));

// Copy package files
fs.copyFileSync(path.join(root, 'package.json'), path.join(dist, 'package.json'));
fs.copyFileSync(path.join(root, 'README.md'), path.join(dist, 'README.md'));
fs.copyFileSync(path.join(root, 'LICENSE'), path.join(dist, 'LICENSE'));
fs.copyFileSync(path.join(root, 'VERSION'), path.join(dist, 'VERSION'));

console.log('Build complete: dist/');
