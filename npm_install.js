const { existsSync } = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const root = __dirname;
const python = process.platform === "win32" ? "py" : "python3";
const launcherArgs = process.platform === "win32" ? ["-3"] : [];
const venvPython = process.platform === "win32"
  ? path.join(root, ".venv", "Scripts", "python.exe")
  : path.join(root, ".venv", "bin", "python");

function run(command, args) {
  const result = spawnSync(command, args, { cwd: root, stdio: "inherit" });
  if (result.error || result.status !== 0) {
    throw result.error || new Error(`${command} exited with status ${result.status}`);
  }
}

if (!existsSync(venvPython)) {
  run(python, [...launcherArgs, "-m", "venv", ".venv"]);
}
run(venvPython, ["-m", "pip", "install", "-r", path.join(root, "requirements.txt")]);
console.log("ImageStudio installed. Run `image-studio init` in a workspace.");
