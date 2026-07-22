const { existsSync } = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const packageRoot = __dirname;
const systemPython = process.platform === "win32" ? "py" : "python3";
const venvPython = process.platform === "win32"
  ? path.join(packageRoot, ".venv", "Scripts", "python.exe")
  : path.join(packageRoot, ".venv", "bin", "python");
const runner = existsSync(venvPython) ? venvPython : systemPython;
const args = runner === systemPython && process.platform === "win32"
  ? ["-3", path.join(packageRoot, "image_studio.py"), ...process.argv.slice(2)]
  : [path.join(packageRoot, "image_studio.py"), ...process.argv.slice(2)];

const result = spawnSync(runner, args, { stdio: "inherit", cwd: process.cwd() });
if (result.error) {
  console.error(`Could not start ${runner}: ${result.error.message}`);
  process.exit(1);
}
process.exit(result.status ?? 1);
