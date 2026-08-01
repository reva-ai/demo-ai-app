import { execFileSync } from "node:child_process";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const hookDirectory = path.dirname(fileURLToPath(import.meta.url));
const repositoryRoot = path.resolve(hookDirectory, "../..");

const input = await readStdin();

let payload;
try {
  payload = JSON.parse(input);
} catch {
  respond({});
}

const loopCount = Number.isInteger(payload.loop_count) ? payload.loop_count : null;
if (loopCount !== 0) {
  respond({});
}

const changedFiles = process.env.REVA_HOOK_CHANGED_FILES
  ? process.env.REVA_HOOK_CHANGED_FILES.split("\n")
  : gitChangedFiles(repositoryRoot);

if (changedFiles.some(isCursorContextFile)) {
  respond({
    followup_message:
      "Cursor context files changed. Run `node .cursor/tools/validate-cursor-config.mjs`, " +
      "`node .cursor/tools/test-hooks.mjs`, and `git diff --check` from this repository root; " +
      "inspect the final diff and record the standards revision, task-authorized exceptions, " +
      "and rollback evidence when generated behavior changed."
  });
}

respond({});

function gitChangedFiles(cwd) {
  try {
    const output = execFileSync(
      "git",
      ["status", "--porcelain=v1", "--untracked-files=all"],
      { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"], timeout: 3000 }
    );
    return output
      .split("\n")
      .filter(Boolean)
      .map((line) => line.slice(3).trim())
      .map((file) => file.includes(" -> ") ? file.split(" -> ").at(-1) : file);
  } catch {
    return [];
  }
}

function isCursorContextFile(file) {
  const normalized = file.replaceAll("\\", "/");
  return (
    normalized === "AGENTS.md" ||
    normalized.endsWith("/AGENTS.md") ||
    normalized === ".cursorignore" ||
    normalized.endsWith("/.cursorignore") ||
    normalized === ".cursorindexingignore" ||
    normalized.endsWith("/.cursorindexingignore") ||
    normalized.startsWith(".cursor/") ||
    normalized.includes("/.cursor/")
  );
}

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
}

function respond(value) {
  process.stdout.write(`${JSON.stringify(value)}\n`);
  process.exit(0);
}
