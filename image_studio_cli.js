const { existsSync } = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const packageRoot = __dirname;
const systemPython = process.platform === "win32" ? "py" : "python3";
const launcherArgs = process.platform === "win32" ? ["-3"] : [];
const venvDir = process.platform === "win32"
  ? path.join(packageRoot, ".venv", "Scripts")
  : path.join(packageRoot, ".venv", "bin");
const venvPython = path.join(venvDir, process.platform === "win32" ? "python.exe" : "python");

// Auto-create venv on first run if it doesn't exist.
if (!existsSync(venvPython)) {
  console.log("Setting up Python environment (one-time)...");
  const result = spawnSync(systemPython, [...launcherArgs, "-m", "venv", path.join(packageRoot, ".venv")], { stdio: "inherit" });
  if (result.status === 0) {
    const pip = path.join(venvDir, process.platform === "win32" ? "pip.exe" : "pip");
    spawnSync(pip, ["install", "numpy", "opencv-python", "scipy", "pyautogui", "PyGetWindow", "pynput"], { stdio: "inherit" });
  }
}

const runner = existsSync(venvPython) ? venvPython : systemPython;
const args = runner === systemPython && process.platform === "win32"
  ? [...launcherArgs, path.join(packageRoot, "image_studio.py"), ...process.argv.slice(2)]
  : [path.join(packageRoot, "image_studio.py"), ...process.argv.slice(2)];

const result = spawnSync(runner, args, { stdio: "inherit", cwd: process.cwd() });
if (result.error) {
  console.error(`Could not start ${runner}: ${result.error.message}`);
  process.exit(1);
}
process.exit(result.status ?? 1);
