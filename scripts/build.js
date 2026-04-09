#!/usr/bin/env node
/**
 * Build script for Grok Swarm.
 * Prepares the npm dist/ bundle and syncs the self-contained Claude plugin runtime.
 */
const fs = require('fs');
const path = require('path');

const root = path.dirname(__dirname);
const dist = path.join(root, 'dist');
const claudeRuntime = path.join(root, 'platforms', 'claude', 'src');

const claudeSourceDirs = ['agent', 'bridge', 'mcp', 'shared'];

function copyRecursive(src, dest) {
  if (!fs.existsSync(src)) return;

  const baseName = path.basename(src);
  if (baseName === '__pycache__' || baseName.endsWith('.pyc') || baseName.endsWith('.pyo')) {
    return;
  }

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

function removeRecursive(target) {
  if (fs.existsSync(target)) {
    fs.rmSync(target, { recursive: true, force: true });
  }
}

// Clean generated outputs
removeRecursive(dist);
removeRecursive(claudeRuntime);

fs.mkdirSync(dist, { recursive: true });
fs.mkdirSync(claudeRuntime, { recursive: true });

// Copy npm CLI runtime
copyRecursive(path.join(root, 'src', 'bridge', 'index.js'), path.join(dist, 'index.js'));
copyRecursive(path.join(root, 'src', 'bridge', 'grok_bridge.py'), path.join(dist, 'grok_bridge.py'));
copyRecursive(path.join(root, 'src', 'bridge', 'apply.py'), path.join(dist, 'apply.py'));
copyRecursive(path.join(root, 'src', 'bridge', 'cli.py'), path.join(dist, 'cli.py'));
copyRecursive(path.join(root, 'src', 'bridge', 'oauth_setup.py'), path.join(dist, 'oauth_setup.py'));
copyRecursive(path.join(root, 'src', 'bridge', 'usage_tracker.py'), path.join(dist, 'usage_tracker.py'));

// Copy package files
fs.copyFileSync(path.join(root, 'package.json'), path.join(dist, 'package.json'));
fs.copyFileSync(path.join(root, 'README.md'), path.join(dist, 'README.md'));
fs.copyFileSync(path.join(root, 'LICENSE'), path.join(dist, 'LICENSE'));
fs.copyFileSync(path.join(root, 'VERSION'), path.join(dist, 'VERSION'));

// Sync the Claude marketplace runtime from canonical root src/
claudeSourceDirs.forEach((dirName) => {
  copyRecursive(path.join(root, 'src', dirName), path.join(claudeRuntime, dirName));
});
copyRecursive(path.join(root, 'src', 'requirements.txt'), path.join(claudeRuntime, 'requirements.txt'));

console.log('Build complete: dist/ and platforms/claude/src/');
