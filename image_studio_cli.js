#!/usr/bin/env node
const { existsSync } = require("fs");
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const packageRoot = __dirname;
const venvDir = process.platform === "win32"
  ? path.join(packageRoot, ".venv", "Scripts")
  : path.join(packageRoot, ".venv", "bin");
const venvPython = path.join(venvDir, process.platform === "win32" ? "python.exe" : "python");

function findCompatiblePython() {
  // Prefer Python 3.12-3.13 over 3.14 (pyautogui incompatibility).
  for (const name of ["python3.13", "python3.12", "python3.11"]) {
    const probe = spawnSync(name, ["--version"], { stdio: "pipe" });
    if (probe.status === 0) return name;
  }
  return "python3";
}

function getPythonVersion(cmd) {
  const probe = spawnSync(cmd, ["--version"], { stdio: "pipe" });
  return probe.status === 0 ? probe.stdout.toString().trim() : null;
}

const systemPython = findCompatiblePython();
const venvStamp = path.join(packageRoot, ".venv", ".python-version");

// Re-create venv if Python version changed or venv doesn't exist.
const currentVersion = getPythonVersion(systemPython);
let needVenv = !existsSync(venvPython);
if (!needVenv && existsSync(venvStamp)) {
  if (fs.readFileSync(venvStamp, "utf8").trim() !== currentVersion) {
    console.log(`Python changed (${currentVersion}); re-creating venv...`);
    fs.rmSync(path.join(packageRoot, ".venv"), { recursive: true, force: true });
    needVenv = true;
  }
}

if (needVenv) {
  console.log(`Setting up Python environment with ${currentVersion}...`);
  const result = spawnSync(systemPython, ["-m", "venv", path.join(packageRoot, ".venv")], { stdio: "inherit" });
  if (result.status === 0) {
    const pip = path.join(venvDir, process.platform === "win32" ? "pip.exe" : "pip");
    spawnSync(pip, ["install", "numpy", "opencv-python", "scipy", "pyautogui", "PyGetWindow", "pynput"], { stdio: "inherit" });
    fs.writeFileSync(venvStamp, currentVersion || "");
  }
}

let runner = existsSync(venvPython) ? venvPython : systemPython;
console.log(`Using Python: ${getPythonVersion(runner)}\n`);

const args = [path.join(packageRoot, "image_studio.py"), ...process.argv.slice(2)];

const result = spawnSync(runner, args, { stdio: "inherit", cwd: process.cwd() });
if (result.error) {
  console.error(`Could not start ${runner}: ${result.error.message}`);
  process.exit(1);
}
process.exit(result.status ?? 1);
