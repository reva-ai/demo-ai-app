#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const failures = [];
const skip = new Set([".git", "node_modules", "target", "build", "dist", ".next", ".terraform", ".venv", "venv", "vendor", "artifacts", "run"]);
const standardSnapshotHeaderMarker = "GENERATED REVA STANDARD SNAPSHOT";
const rootManagedManifest = ".cursor/managed-files.json";
const exactMcpConfig = { mcpServers: {} };
const exactHooksConfig = {
  version: 1,
  hooks: {
    beforeShellExecution: [
      { command: "node .cursor/hooks/guard-shell.mjs", timeout: 5 },
    ],
    beforeReadFile: [
      { command: "node .cursor/hooks/guard-read.mjs", timeout: 5, failClosed: true },
    ],
    stop: [
      { command: "node .cursor/hooks/review-context-change.mjs", timeout: 10 },
    ],
  },
};
const requiredRootManagedPaths = [
  "AGENTS.md",
  ".cursorignore",
  ".cursorindexingignore",
  ".cursor/README.md",
  ".cursor/reva-profile.json",
  ".cursor/module-index.json",
  ".cursor/mcp.json",
  ".cursor/hooks.json",
  ".cursor/hooks/guard-read.mjs",
  ".cursor/hooks/guard-shell.mjs",
  ".cursor/hooks/review-context-change.mjs",
  ".cursor/knowledge/agent-context-design.md",
  ".cursor/knowledge/cursor-exceptions.md",
  ".cursor/knowledge/module-index.md",
  ".cursor/knowledge/organization-standard.md",
  ".cursor/knowledge/quality-policy.md",
  ".cursor/knowledge/repository-profile.md",
  ".cursor/knowledge/standards/manifest.json",
  ".cursor/rules/00-reva-organization.mdc",
  ".cursor/rules/20-testing-quality.mdc",
  ".cursor/rules/30-security-observability.mdc",
  ".cursor/rules/90-context-improvement.mdc",
  ".cursor/tools/test-hooks.mjs",
  ".cursor/tools/validate-cursor-config.mjs",
];
const standardBaselines = [
  { always: true, profile: "reva-org", source: "baseline.md", target: "organization-baseline.md" },
  { always: true, profile: "reva-org", source: "cursor-baseline.md", target: "cursor-baseline.md" },
  { profile: "reva-java", source: "Java/baseline.md", target: "java-baseline.md" },
  { profile: "reva-springboot", source: "Java/SpringBoot/baseline.md", target: "springboot-baseline.md" },
  { profile: "reva-r2dbc", source: "Java/R2DBC/baseline.md", target: "r2dbc-baseline.md" },
  { profile: "reva-mongodb", source: "Java/MongoDB/baseline.md", target: "mongodb-baseline.md" },
  { profile: "reva-go", source: "Golang/baseline.md", target: "go-baseline.md" },
  { profile: "reva-gin", source: "Golang/GIN/baseline.md", target: "gin-baseline.md" },
  { profile: "reva-chi", source: "Golang/CHI/baseline.md", target: "chi-baseline.md" },
  { profile: "reva-gorillamux", source: "Golang/GorillaMux/baseline.md", target: "gorillamux-baseline.md" },
  { profile: "reva-python", source: "Python/baseline.md", target: "python-baseline.md" },
  { profile: "reva-fastapi", source: "Python/FastAPI/baseline.md", target: "fastapi-baseline.md" },
  { profile: "reva-node", source: "Node/baseline.md", target: "node-baseline.md" },
  { profile: "reva-fastify", source: "Node/Fastify/baseline.md", target: "fastify-baseline.md" },
  { profile: "reva-nextjs", source: "Node/NextJS/baseline.md", target: "nextjs-baseline.md" },
  { profile: "reva-opentofu", source: "OpenTofu/baseline.md", target: "opentofu-baseline.md" },
  { profile: "reva-helm", source: "Helm/baseline.md", target: "helm-baseline.md" },
  { profile: "reva-katalon", source: "Katalon/baseline.md", target: "katalon-baseline.md" },
  { profile: "reva-gitlab", source: "GitLab/baseline.md", target: "gitlab-baseline.md" },
];
const standardOrganizationKnowledge = [
  { source: ".cursor/knowledge/reva-architecture.md", target: "reva-architecture.md" },
  { source: ".cursor/knowledge/context-budget.md", target: "context-budget.md" },
  { source: ".cursor/knowledge/cursor-operating-model.md", target: "cursor-operating-model.md" },
  { source: ".cursor/knowledge/hard-enforcement.md", target: "hard-enforcement.md" },
];

for (const relativePath of [
  "AGENTS.md",
  ".cursor/README.md",
  ".cursor/reva-profile.json",
  ".cursor/module-index.json",
  rootManagedManifest,
  ".cursor/mcp.json",
  ".cursor/hooks.json",
  ".cursor/knowledge/agent-context-design.md",
  ".cursor/knowledge/standards/manifest.json",
  ".cursor/tools/validate-cursor-config.mjs",
  ".cursor/tools/test-hooks.mjs",
  ".cursorignore",
  ".cursorindexingignore",
]) {
  if (!fs.existsSync(path.join(root, relativePath))) failures.push(`${relativePath} is missing`);
}

let index = { modules: [] };
try {
  index = readJson(path.join(root, ".cursor/module-index.json"));
  if (!Array.isArray(index.modules)) failures.push(".cursor/module-index.json must contain modules[]");
} catch (error) {
  failures.push(error.message);
}

let repositoryProfile = { selectedProfiles: [] };
try {
  repositoryProfile = readJson(path.join(root, ".cursor/reva-profile.json"));
  if (repositoryProfile.profileKind !== "repository-local" || !Array.isArray(repositoryProfile.selectedProfiles)) {
    failures.push(".cursor/reva-profile.json must declare a repository-local profile and selectedProfiles[]");
  }
} catch (error) {
  failures.push(error.message);
}
validateStandardSnapshots(repositoryProfile.selectedProfiles ?? [], repositoryProfile.standardsRevision);
validateManagedFilesManifest(repositoryProfile.repository);

try {
  const mcp = readJson(path.join(root, ".cursor/mcp.json"));
  if (!jsonEqual(mcp, exactMcpConfig)) failures.push(".cursor/mcp.json must be exactly {mcpServers:{}} with no configured servers or extra keys");
} catch (error) {
  failures.push(error.message);
}

for (const relativePath of [".cursor/tools/validate-cursor-config.mjs", ".cursor/tools/test-hooks.mjs"]) {
  if (!fs.existsSync(path.join(root, relativePath))) failures.push(`repository-local hook referenced tool is missing: ${relativePath}`);
}
try {
  const stopScript = fs.readFileSync(path.join(root, ".cursor/hooks/review-context-change.mjs"), "utf8");
  for (const reference of [".cursor/tools/validate-cursor-config.mjs", ".cursor/tools/test-hooks.mjs", "git diff --check"]) {
    if (!stopScript.includes(reference)) failures.push(`repository-local stop hook is missing validation reference: ${reference}`);
  }
  for (const forbidden of ["validate-cursor-packs.mjs", "validate-materialized-cursor-pack.mjs"]) {
    if (stopScript.includes(forbidden)) failures.push(`repository-local stop hook references a non-installed validator: ${forbidden}`);
  }
} catch (error) {
  failures.push(`repository-local stop hook is unreadable: ${error.message}`);
}

try {
  const hooks = readJson(path.join(root, ".cursor/hooks.json"));
  if (!jsonEqual(hooks, exactHooksConfig)) failures.push(".cursor/hooks.json does not match the exact Reva repository hook contract");
  for (const hook of Object.values(exactHooksConfig.hooks)) {
    const script = hook[0].command.split(/\s+/u).at(-1);
    if (!fs.existsSync(path.join(root, script))) failures.push(`hook script is missing: ${script}`);
  }
} catch (error) {
  failures.push(error.message);
}

const nestedCursorDirectories = findNestedCursorDirectories();
validateModuleIndexIntegrity(index, repositoryProfile, nestedCursorDirectories);

const rules = findFiles(root, (file) => file.endsWith(".mdc") && file.split(path.sep).includes(".cursor"));
const skills = findFiles(root, (file) => path.basename(file) === "SKILL.md" && file.split(path.sep).includes(".cursor"));
const skillNames = new Set();
let rootAlwaysRules = 0;

for (const file of rules) {
  const relativePath = posix(path.relative(root, file));
  const text = fs.readFileSync(file, "utf8");
  const frontmatter = text.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n/u);
  if (!frontmatter) {
    failures.push(`${relativePath} has no YAML frontmatter`);
    continue;
  }
  const keys = [...frontmatter[1].matchAll(/^([A-Za-z][A-Za-z0-9]*):/gmu)].map((match) => match[1]);
  if (keys.some((key) => !["description", "globs", "alwaysApply"].includes(key))) failures.push(`${relativePath} has unsupported frontmatter`);
  if (!keys.includes("description") || !keys.includes("alwaysApply")) failures.push(`${relativePath} needs description and alwaysApply`);
  const alwaysApply = /^alwaysApply:\s*true\s*$/mu.test(frontmatter[1]);
  if (relativePath.startsWith(".cursor/rules/") && alwaysApply) rootAlwaysRules += 1;
  if (!relativePath.startsWith(".cursor/rules/") && alwaysApply) failures.push(`${relativePath} must not be always-applied`);
  if (text.split(/\r?\n/u).length > 500) failures.push(`${relativePath} exceeds 500 lines`);
}
if (rootAlwaysRules > 2) failures.push(`root pack has ${rootAlwaysRules} always rules; maximum is 2`);

for (const file of skills) {
  const relativePath = posix(path.relative(root, file));
  const text = fs.readFileSync(file, "utf8");
  const match = text.match(/^---\r?\nname:\s*([a-z0-9-]+)\r?\ndescription:/mu);
  const expected = path.basename(path.dirname(file));
  if (!match || match[1] !== expected) failures.push(`${relativePath} must name its containing directory`);
  if (match && skillNames.has(match[1])) failures.push(`duplicate skill name: ${match[1]}`);
  if (match) skillNames.add(match[1]);
}

for (const directory of nestedCursorDirectories) {
  const moduleRoot = path.dirname(directory);
  const modulePath = posix(path.relative(root, moduleRoot));
  for (const forbidden of ["AGENTS.md", "agents.md", ".cursorignore", ".cursorindexingignore"]) {
    if (fs.existsSync(path.join(moduleRoot, forbidden))) failures.push(`${modulePath}/${forbidden} is forbidden; root owns agent and ignore policy`);
  }
  for (const forbidden of ["hooks.json", "mcp.json", "commands", "agents", "hooks", "tools"]) {
    if (fs.existsSync(path.join(directory, forbidden))) failures.push(`${modulePath}/.cursor/${forbidden} is root-owned and forbidden`);
  }
}

for (const file of findFiles(root, (candidate) => path.basename(candidate).toLowerCase() === "agents.md")) {
  if (path.dirname(file) !== root) failures.push(`nested agent instruction is forbidden: ${posix(path.relative(root, file))}`);
}
for (const file of findFiles(root, (candidate) => /^agent-start[^/]*\.md$/u.test(path.basename(candidate).toLowerCase()))) {
  failures.push(`legacy agent-start instruction is forbidden: ${posix(path.relative(root, file))}`);
}
if (findFiles(root, (file) => path.basename(file) === ".cursorrules").length > 0) failures.push("legacy .cursorrules is forbidden");

if (failures.length > 0) {
  process.stderr.write(failures.map((failure) => `cursor_context_validation=fail ${failure}`).join("\n") + "\n");
  process.exit(1);
}

process.stdout.write(`cursor_context_validation=pass rules=${rules.length} skills=${skills.length} modules=${nestedCursorDirectories.length}\n`);

function validateStandardSnapshots(selectedProfiles, standardsRevision) {
  const selected = new Set(selectedProfiles);
  const expected = [
    ...standardBaselines
      .filter((definition) => definition.always || selected.has(definition.profile))
      .map((definition) => ({ ...definition, kind: "baseline" })),
    ...standardOrganizationKnowledge.map((definition) => ({
      ...definition,
      kind: "organization-knowledge",
      profile: "reva-org",
    })),
  ];
  let manifest = { snapshots: [] };
  try {
    manifest = readJson(path.join(root, ".cursor/knowledge/standards/manifest.json"));
    if (!Array.isArray(manifest.snapshots)) failures.push(".cursor/knowledge/standards/manifest.json must contain snapshots[]");
    if (manifest.standardsRevision !== standardsRevision) failures.push("standard snapshot manifest revision does not match the repository profile");
  } catch (error) {
    failures.push(error.message);
    return;
  }

  const expectedByTarget = new Map(expected.map((definition) => [`knowledge/standards/${definition.target}`, definition]));
  const actualByTarget = new Map((manifest.snapshots ?? []).map((snapshot) => [snapshot.target, snapshot]));
  for (const [target, definition] of expectedByTarget) {
    const snapshot = actualByTarget.get(target);
    if (!snapshot) {
      failures.push(`standard snapshot is missing from manifest: ${target}`);
      continue;
    }
    if (snapshot.profile !== definition.profile || snapshot.source !== definition.source || snapshot.kind !== definition.kind) {
      failures.push(`standard snapshot metadata does not match selected profile: ${target}`);
    }
  }
  for (const target of actualByTarget.keys()) {
    if (!expectedByTarget.has(target)) failures.push(`standard snapshot is not selected by this repository profile: ${target}`);
  }

  for (const snapshot of manifest.snapshots ?? []) {
    if (typeof snapshot.target !== "string" || !snapshot.target.startsWith("knowledge/standards/") || snapshot.target.includes("..")) {
      failures.push(`standard snapshot has unsafe target: ${String(snapshot.target)}`);
      continue;
    }
    const file = path.join(root, ".cursor", snapshot.target);
    if (!fs.existsSync(file)) {
      failures.push(`standard snapshot file is missing: ${snapshot.target}`);
      continue;
    }
    const content = fs.readFileSync(file, "utf8");
    if (!content.includes(standardSnapshotHeaderMarker)) failures.push(`standard snapshot header is missing: ${snapshot.target}`);
    const digest = crypto.createHash("sha256").update(content).digest("hex");
    if (snapshot.materializedSha256 !== digest) failures.push(`standard snapshot digest does not match: ${snapshot.target}`);
  }
}

function validateManagedFilesManifest(expectedRepository) {
  let manifest;
  try {
    manifest = readJson(path.join(root, rootManagedManifest));
  } catch (error) {
    failures.push(error.message);
    return;
  }
  if (manifest.schemaVersion !== 1) failures.push(`${rootManagedManifest} must use schemaVersion 1`);
  if (manifest.manifestKind !== "reva-generated-root-pack") {
    failures.push(`${rootManagedManifest} must declare manifestKind reva-generated-root-pack`);
  }
  if (manifest.repository !== expectedRepository) failures.push(`${rootManagedManifest} repository does not match the repository profile`);
  if (manifest.hashAlgorithm !== "sha256") failures.push(`${rootManagedManifest} must declare sha256`);
  if (!Array.isArray(manifest.files)) {
    failures.push(`${rootManagedManifest} must contain files[]`);
    return;
  }

  const declaredPaths = new Set();
  let previousPath = null;
  for (const entry of manifest.files) {
    if (!entry || typeof entry !== "object" || Array.isArray(entry)) {
      failures.push(`${rootManagedManifest} contains a non-object file entry`);
      continue;
    }
    const relativePath = entry.path;
    if (!isSafeManagedRootPath(relativePath)) {
      failures.push(`${rootManagedManifest} contains an unsafe path: ${String(relativePath)}`);
      continue;
    }
    if (previousPath !== null && previousPath.localeCompare(relativePath) >= 0) {
      failures.push(`${rootManagedManifest} file entries must be in deterministic path order`);
    }
    previousPath = relativePath;
    if (declaredPaths.has(relativePath)) {
      failures.push(`${rootManagedManifest} contains a duplicate path: ${relativePath}`);
      continue;
    }
    declaredPaths.add(relativePath);
    if (!/^[a-f0-9]{64}$/u.test(entry.sha256 ?? "")) {
      failures.push(`${rootManagedManifest} has an invalid sha256 for ${relativePath}`);
      continue;
    }
    const resolved = path.resolve(root, relativePath);
    let stat;
    try {
      stat = fs.lstatSync(resolved);
    } catch {
      failures.push(`managed root file is missing: ${relativePath}`);
      continue;
    }
    if (!stat.isFile() || stat.isSymbolicLink()) {
      failures.push(`managed root path must be a regular file: ${relativePath}`);
      continue;
    }
    const digest = crypto.createHash("sha256").update(fs.readFileSync(resolved)).digest("hex");
    if (entry.sha256 !== digest) failures.push(`managed root digest does not match: ${relativePath}`);
  }

  const actualPaths = new Set(collectRootManagedPaths());
  for (const relativePath of declaredPaths) {
    if (!actualPaths.has(relativePath)) failures.push(`managed root manifest declares a non-root artifact: ${relativePath}`);
  }
  for (const relativePath of actualPaths) {
    if (!declaredPaths.has(relativePath)) failures.push(`root Cursor artifact is not declared in ${rootManagedManifest}: ${relativePath}`);
  }
  for (const requiredPath of requiredRootManagedPaths) {
    if (!declaredPaths.has(requiredPath)) failures.push(`required root file is not declared in ${rootManagedManifest}: ${requiredPath}`);
  }
}

function collectRootManagedPaths() {
  const results = [];
  for (const relativePath of ["AGENTS.md", ".cursorignore", ".cursorindexingignore"]) {
    if (fs.existsSync(path.join(root, relativePath))) results.push(relativePath);
  }
  const cursorRoot = path.join(root, ".cursor");
  const visit = (directory) => {
    let entries = [];
    try {
      entries = fs.readdirSync(directory, { withFileTypes: true });
    } catch (error) {
      failures.push(`root Cursor directory is unreadable: ${posix(path.relative(root, directory))}: ${error.message}`);
      return;
    }
    for (const entry of entries.sort((left, right) => left.name.localeCompare(right.name))) {
      const candidate = path.join(directory, entry.name);
      const relativePath = posix(path.relative(root, candidate));
      if (entry.isDirectory()) {
        visit(candidate);
      } else if (relativePath !== rootManagedManifest) {
        results.push(relativePath);
        if (!entry.isFile()) failures.push(`root Cursor artifact must be a regular file: ${relativePath}`);
      }
    }
  };
  if (fs.existsSync(cursorRoot)) visit(cursorRoot);
  return [...new Set(results)].sort((left, right) => left.localeCompare(right));
}

function isSafeManagedRootPath(value) {
  if (typeof value !== "string" || value.length === 0 || value !== value.trim()) return false;
  if (value.includes("\\") || value.includes("\0") || path.posix.isAbsolute(value)) return false;
  if (path.posix.normalize(value) !== value || value.split("/").some((part) => part === "" || part === "." || part === "..")) return false;
  if (value === rootManagedManifest) return false;
  return value === "AGENTS.md" || value === ".cursorignore" || value === ".cursorindexingignore" || value.startsWith(".cursor/");
}

function validateModuleIndexIntegrity(index, repositoryProfile, nestedCursorDirectories) {
  if (index.schemaVersion !== 1) failures.push(".cursor/module-index.json must use schemaVersion 1");
  if (index.repository !== repositoryProfile.repository) failures.push("module index repository does not match the repository profile");
  const entries = Array.isArray(index.modules) ? index.modules : [];
  const entriesByPath = new Map();
  const indexIds = new Set();
  for (const entry of entries) {
    if (!entry || typeof entry !== "object" || Array.isArray(entry)) {
      failures.push("module index contains a non-object entry");
      continue;
    }
    if (typeof entry.moduleId !== "string" || entry.moduleId.length === 0) failures.push("module index entry has an invalid moduleId");
    else if (indexIds.has(entry.moduleId)) failures.push(`duplicate module id in index: ${entry.moduleId}`);
    else indexIds.add(entry.moduleId);
    if (!isSafeModulePath(entry.path)) {
      failures.push(`module index entry has an unsafe path: ${String(entry.path)}`);
    } else if (entriesByPath.has(entry.path)) {
      failures.push(`duplicate module path in index: ${entry.path}`);
    } else {
      entriesByPath.set(entry.path, entry);
    }
    validateStringArray(entry.selectedProfiles, `module index ${String(entry.path)} selectedProfiles`);
    validateStringArray(entry.manifests, `module index ${String(entry.path)} manifests`);
    if (!/^[a-f0-9]{64}$/u.test(entry.generatedFilesDigest ?? "")) {
      failures.push(`module index ${String(entry.path)} has an invalid generatedFilesDigest`);
    }
  }

  const actualPaths = new Set(nestedCursorDirectories.map((directory) => posix(path.relative(root, path.dirname(directory)))));
  for (const modulePath of entriesByPath.keys()) {
    if (!actualPaths.has(modulePath)) failures.push(`module index references missing overlay: ${modulePath}`);
  }
  for (const modulePath of actualPaths) {
    if (!entriesByPath.has(modulePath)) failures.push(`nested .cursor is not indexed: ${modulePath}`);
  }

  const profileIds = new Set();
  for (const directory of nestedCursorDirectories) {
    const modulePath = posix(path.relative(root, path.dirname(directory)));
    const entry = entriesByPath.get(modulePath);
    let profile;
    try {
      profile = readJson(path.join(directory, "reva-module-profile.json"));
    } catch (error) {
      failures.push(error.message);
      continue;
    }
    if (profile.schemaVersion !== 1) failures.push(`${modulePath} profile must use schemaVersion 1`);
    if (typeof profile.moduleId !== "string" || profile.moduleId.length === 0) {
      failures.push(`${modulePath} profile has an invalid moduleId`);
    } else if (profileIds.has(profile.moduleId)) {
      failures.push(`duplicate module id in profiles: ${profile.moduleId}`);
    } else {
      profileIds.add(profile.moduleId);
    }
    if (profile.path !== modulePath) failures.push(`${modulePath} profile path does not match its location`);
    if (profile.parentRepository !== repositoryProfile.repository) failures.push(`${modulePath} profile parentRepository does not match the root profile`);
    validateStringArray(profile.selectedProfiles, `${modulePath} profile selectedProfiles`);
    validateStringArray(profile.manifests, `${modulePath} profile manifests`);
    const digest = digestModuleDirectory(directory);
    if (profile.generatedFilesDigest !== digest) failures.push(`${modulePath} generated digest does not match`);
    if (!entry) continue;
    if (entry.moduleId !== profile.moduleId) failures.push(`${modulePath} index moduleId does not match its profile`);
    if (!arraysEqual(entry.selectedProfiles, profile.selectedProfiles)) failures.push(`${modulePath} index selectedProfiles do not match its profile`);
    if (!arraysEqual(entry.manifests, profile.manifests)) failures.push(`${modulePath} index manifests do not match its profile`);
    if (entry.generatedFilesDigest !== profile.generatedFilesDigest) failures.push(`${modulePath} index digest does not match its profile`);
    if (entry.generatedFilesDigest !== digest) failures.push(`${modulePath} index digest does not match generated module files`);
  }
}

function validateStringArray(value, label) {
  if (!Array.isArray(value)) {
    failures.push(`${label} must be an array`);
    return;
  }
  const seen = new Set();
  for (const item of value) {
    if (typeof item !== "string" || item.length === 0) failures.push(`${label} must contain non-empty strings`);
    else if (seen.has(item)) failures.push(`${label} contains a duplicate value: ${item}`);
    else seen.add(item);
  }
}

function arraysEqual(left, right) {
  return Array.isArray(left) && Array.isArray(right) && left.length === right.length && left.every((value, index) => value === right[index]);
}

function isSafeModulePath(value) {
  return typeof value === "string" && value.length > 0 && value === value.trim() && !value.includes("\\") && !value.includes("\0") &&
    !path.posix.isAbsolute(value) && path.posix.normalize(value) === value &&
    !value.split("/").some((part) => part === "" || part === "." || part === ".." || part === ".cursor");
}

function jsonEqual(left, right) {
  return canonicalJson(left) === canonicalJson(right);
}

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function findNestedCursorDirectories() {
  const results = [];
  const visit = (directory) => {
    let entries = [];
    try { entries = fs.readdirSync(directory, { withFileTypes: true }); } catch { return; }
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const child = path.join(directory, entry.name);
      if (entry.name === ".cursor") {
        if (child !== path.join(root, ".cursor")) results.push(child);
        continue;
      }
      if (skip.has(entry.name)) continue;
      visit(child);
    }
  };
  visit(root);
  return results.sort();
}

function findFiles(directory, predicate) {
  const results = [];
  const visit = (current) => {
    let entries = [];
    try { entries = fs.readdirSync(current, { withFileTypes: true }); } catch { return; }
    for (const entry of entries) {
      const file = path.join(current, entry.name);
      if (entry.isDirectory()) {
        if (skip.has(entry.name) && entry.name !== ".cursor") continue;
        visit(file);
      } else if (entry.isFile() && predicate(file)) {
        results.push(file);
      }
    }
  };
  visit(directory);
  return results;
}

function digestModuleDirectory(directory) {
  const hash = crypto.createHash("sha256");
  const files = findFiles(directory, (file) => path.basename(file) !== "reva-module-profile.json")
    .sort((left, right) => left.localeCompare(right));
  for (const file of files) {
    hash.update(posix(path.relative(directory, file))).update("\0").update(fs.readFileSync(file)).update("\0");
  }
  return hash.digest("hex");
}

function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (error) {
    throw new Error(`${posix(path.relative(root, file))} is not valid JSON: ${error.message}`);
  }
}

function posix(value) {
  return value.split(path.sep).join("/");
}
