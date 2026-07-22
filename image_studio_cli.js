const { spawnSync } = require("child_process");

const python = process.platform === "win32" ? "py" : "python3";
const args = process.platform === "win32"
  ? ["-3", "image_studio.py", ...process.argv.slice(2)]
  : ["image_studio.py", ...process.argv.slice(2)];

const result = spawnSync(python, args, { stdio: "inherit" });
if (result.error) {
  console.error(`Could not start ${python}: ${result.error.message}`);
  process.exit(1);
}
process.exit(result.status ?? 1);
