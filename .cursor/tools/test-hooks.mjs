import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const toolDirectory = path.dirname(fileURLToPath(import.meta.url));
const hooksDirectory = path.resolve(toolDirectory, "../hooks");
const failures = [];
const repositoryRoot = path.resolve(toolDirectory, "../..");
for (const relativePath of [
  ".cursor/tools/validate-cursor-config.mjs",
  ".cursor/tools/test-hooks.mjs"
]) {
  if (!fs.existsSync(path.join(repositoryRoot, relativePath))) {
    failures.push(`repository-local hook references missing tool: ${relativePath}`);
  }
}

const shellCases = [
  {
    name: "allows read-only git status",
    payload: { command: "git status --short" },
    permission: "allow"
  },
  {
    name: "denies broad recursive deletion",
    payload: { command: "rm -rf /" },
    permission: "deny"
  },
  {
    name: "denies ordinary file deletion",
    payload: { command: "rm important.txt" },
    permission: "deny"
  },
  {
    name: "denies absolute-path file deletion",
    payload: { command: "/bin/rm -f important.txt" },
    permission: "deny"
  },
  {
    name: "denies protected force push",
    payload: { command: "git push --force origin main" },
    permission: "deny"
  },
  {
    name: "denies ordinary agent push pending manual review",
    payload: { command: "git push origin feat/example" },
    permission: "deny"
  },
  {
    name: "denies terraform destroy",
    payload: { command: "terraform destroy -var-file dev.tfvars" },
    permission: "deny"
  },
  {
    name: "denies long-option broad deletion",
    payload: { command: "rm --force --recursive /" },
    permission: "deny"
  },
  {
    name: "denies git global-option force push",
    payload: { command: "git -C service push --force-with-lease origin feat/example" },
    permission: "deny"
  },
  {
    name: "denies kubectl global-option mutation",
    payload: { command: "kubectl --context prod delete namespace demo" },
    permission: "deny"
  },
  {
    name: "denies Helm global-option mutation",
    payload: { command: "helm --namespace prod upgrade demo chart" },
    permission: "deny"
  },
  {
    name: "denies Terraform global-option mutation",
    payload: { command: "terraform -chdir=infra destroy -auto-approve" },
    permission: "deny"
  },
  {
    name: "denies AWS global-option mutation",
    payload: {
      command: "aws --profile prod ec2 terminate-instances --instance-ids i-example"
    },
    permission: "deny"
  },
  {
    name: "denies AWS object transfer",
    payload: { command: "aws --profile prod s3 cp s3://customer-data/export.json -" },
    permission: "deny"
  },
  {
    name: "denies AWS secret reads",
    payload: { command: "aws secretsmanager get-secret-value --secret-id api" },
    permission: "deny"
  },
  {
    name: "denies AWS remote execution",
    payload: {
      command: "aws stepfunctions start-execution --state-machine-arn arn:example"
    },
    permission: "deny"
  },
  {
    name: "denies package publication",
    payload: { command: "npm publish --access public" },
    permission: "deny"
  },
  {
    name: "denies additional kubectl mutations",
    payload: { command: "kubectl --context prod set image deployment/api api=image:v2" },
    permission: "deny"
  },
  {
    name: "denies kubectl debug",
    payload: { command: "kubectl --context prod debug pod/api --image=busybox" },
    permission: "deny"
  },
  {
    name: "denies Kubernetes secret reads",
    payload: { command: "kubectl --context prod get secret api -o yaml" },
    permission: "deny"
  },
  {
    name: "denies raw Kubernetes configuration reads",
    payload: { command: "kubectl config view --raw" },
    permission: "deny"
  },
  {
    name: "denies Terraform force unlock",
    payload: { command: "terraform -chdir=infra force-unlock -force lock-id" },
    permission: "deny"
  },
  {
    name: "denies Terraform state pull",
    payload: { command: "terraform -chdir=infra state pull" },
    permission: "deny"
  },
  {
    name: "denies Terraform output exfiltration",
    payload: { command: "terraform -chdir=infra output -json" },
    permission: "deny"
  },
  {
    name: "denies Helm publication",
    payload: { command: "helm push chart.tgz oci://registry.example/reva" },
    permission: "deny"
  },
  {
    name: "denies Maven deployment",
    payload: { command: "./mvnw -B deploy" },
    permission: "deny"
  },
  {
    name: "denies Python package upload",
    payload: { command: "python -m twine upload dist/*" },
    permission: "deny"
  },
  {
    name: "denies uv publication",
    payload: { command: "uv publish" },
    permission: "deny"
  },
  {
    name: "denies Git commit",
    payload: { command: "git -C service commit -m 'example'" },
    permission: "deny"
  },
  {
    name: "denies Git tag",
    payload: { command: "git tag v1.2.3" },
    permission: "deny"
  },
  {
    name: "denies destructive Git branch deletion",
    payload: { command: "git branch -D feature-x" },
    permission: "deny"
  },
  {
    name: "denies destructive Git switch reset",
    payload: { command: "git switch -C main origin/main" },
    permission: "deny"
  },
  {
    name: "denies destructive Git checkout of worktree",
    payload: { command: "git checkout ." },
    permission: "deny"
  },
  {
    name: "denies destructive Git checkout from HEAD",
    payload: { command: "git checkout HEAD -- src/app.py" },
    permission: "deny"
  },
  {
    name: "denies forced Git checkout",
    payload: { command: "git checkout -f main" },
    permission: "deny"
  },
  {
    name: "denies Git stash deletion",
    payload: { command: "git stash clear" },
    permission: "deny"
  },
  {
    name: "denies Git worktree removal",
    payload: { command: "git worktree remove --force ../other" },
    permission: "deny"
  },
  {
    name: "denies Git reference deletion",
    payload: { command: "git update-ref -d refs/heads/main" },
    permission: "deny"
  },
  {
    name: "denies Git remote removal",
    payload: { command: "git remote remove origin" },
    permission: "deny"
  },
  {
    name: "denies find deletion",
    payload: { command: "find . -type f -delete" },
    permission: "deny"
  },
  {
    name: "denies unlink deletion",
    payload: { command: "unlink important.txt" },
    permission: "deny"
  },
  {
    name: "denies directory deletion",
    payload: { command: "rmdir empty-dir" },
    permission: "deny"
  },
  {
    name: "denies environment dump",
    payload: { command: "env" },
    permission: "deny"
  },
  {
    name: "denies proc environment disclosure",
    payload: { command: "cat /proc/self/environ" },
    permission: "deny"
  },
  {
    name: "denies common SSH private key disclosure",
    payload: { command: "cat ~/.ssh/id_rsa" },
    permission: "deny"
  },
  {
    name: "denies AWS shared credential disclosure",
    payload: { command: "sed -n '1,20p' $HOME/.aws/credentials" },
    permission: "deny"
  },
  {
    name: "denies Node environment disclosure",
    payload: { command: "node -e 'console.log(process.env)'" },
    permission: "deny"
  },
  {
    name: "denies Python environment disclosure",
    payload: { command: "python -c 'import os; print(os.environ)'" },
    permission: "deny"
  },
  {
    name: "denies unfiltered Go environment",
    payload: { command: "go env -json" },
    permission: "deny"
  },
  {
    name: "denies credential-bearing Go proxy output",
    payload: { command: "go env GOPROXY" },
    permission: "deny"
  },
  {
    name: "allows approved named Go environment keys",
    payload: { command: "go env GOVERSION GOMOD GOPRIVATE GONOSUMDB" },
    permission: "allow"
  },
  {
    name: "denies alternate-reader environment access",
    payload: { command: "base64 .env.production" },
    permission: "deny"
  },
  {
    name: "denies interpreter environment access",
    payload: { command: "python -c \"print(open('.env').read())\"" },
    permission: "deny"
  },
  {
    name: "denies npm credential access",
    payload: { command: "cat -- .npmrc" },
    permission: "deny"
  },
  {
    name: "denies Docker credential access",
    payload: { command: "node -e \"console.log(readFileSync('.docker/config.json'))\"" },
    permission: "deny"
  },
  {
    name: "denies npm credential backup access",
    payload: { command: "grep token .npmrc.backup" },
    permission: "deny"
  },
  {
    name: "denies Yarn credential backup access",
    payload: { command: "base64 .yarnrc.yml.bak" },
    permission: "deny"
  },
  {
    name: "allows reviewed environment template",
    payload: { command: "sed -n '1,20p' .env.development.example" },
    permission: "allow"
  },
  {
    name: "allows read-only global-option commands",
    payload: {
      command:
        "git -C service status --short && kubectl --context dev get pods && " +
        "terraform -chdir=infra plan && aws --profile dev sts get-caller-identity"
    },
    permission: "allow"
  }
];

for (const testCase of shellCases) {
  const result = runHook("guard-shell.mjs", testCase.payload);
  if (result.permission !== testCase.permission) {
    failures.push(
      `${testCase.name}: expected ${testCase.permission}, got ${JSON.stringify(result)}`
    );
  }
}

const malformedShell = runHookRaw("guard-shell.mjs", "{not-json");
if (malformedShell.permission !== "deny") {
  failures.push(`malformed shell payload must deny, got ${JSON.stringify(malformedShell)}`);
}

const readCases = [
  { name: "allows source", file_path: "src/main.go", permission: "allow" },
  { name: "allows env example", file_path: ".env.example", permission: "allow" },
  {
    name: "allows named env example",
    file_path: "config/.env.development.example",
    permission: "allow"
  },
  { name: "denies environment", file_path: ".env.production", permission: "deny" },
  { name: "denies private key", file_path: "certs/client.key", permission: "deny" },
  {
    name: "denies example private key",
    file_path: "certs/client.example.key",
    permission: "deny"
  },
  { name: "denies netrc", file_path: "/Users/dev/.netrc", permission: "deny" },
  {
    name: "denies cloud profile",
    file_path: "/Users/dev/.aws/config",
    permission: "deny"
  },
  { name: "denies Python package credentials", file_path: ".pypirc", permission: "deny" },
  { name: "denies local npm credentials", file_path: ".npmrc.local", permission: "deny" },
  { name: "denies npm credentials", file_path: ".npmrc", permission: "deny" },
  { name: "denies Yarn credentials", file_path: ".yarnrc.yml", permission: "deny" },
  {
    name: "denies Docker credentials",
    file_path: "/Users/dev/.docker/config.json",
    permission: "deny"
  },
  { name: "denies npm credential backup", file_path: ".npmrc.backup", permission: "deny" },
  { name: "denies pnpm credential profile", file_path: ".pnpmrc.prod", permission: "deny" },
  { name: "denies Yarn credential backup", file_path: ".yarnrc.yml.bak", permission: "deny" },
  {
    name: "allows npm credential template",
    file_path: ".npmrc.example",
    permission: "allow"
  },
  {
    name: "allows Docker credential template",
    file_path: ".docker/config.example.json",
    permission: "allow"
  },
  { name: "allows legitimate core source", file_path: "src/domain/core.py", permission: "allow" },
  { name: "denies numeric core dump", file_path: "core.12345", permission: "deny" },
  { name: "denies terraform state", file_path: "infra/terraform.tfstate", permission: "deny" },
  { name: "denies kubeconfig", file_path: "/Users/dev/.kube/config", permission: "deny" },
  {
    name: "denies database dump",
    file_path: "fixtures/customer.bson.gz",
    permission: "deny"
  },
  {
    name: "denies local secret overlay",
    file_path: "config/foo-secrets.local.yaml",
    permission: "deny"
  },
  { name: "denies Redis dump", file_path: "fixtures/cache.rdb", permission: "deny" }
];

for (const testCase of readCases) {
  const result = runHook("guard-read.mjs", { file_path: testCase.file_path });
  if (result.permission !== testCase.permission) {
    failures.push(
      `${testCase.name}: expected ${testCase.permission}, got ${JSON.stringify(result)}`
    );
  }
}

const contextReview = runHook(
  "review-context-change.mjs",
  {
    loop_count: 0,
    workspace_roots: [
      path.join(os.tmpdir(), "not-the-hook-owner"),
      path.resolve(toolDirectory, "../..")
    ]
  },
  { REVA_HOOK_CHANGED_FILES: "src/main.ts\n.cursor/rules/example/RULE.md" }
);
if (typeof contextReview.followup_message !== "string") {
  failures.push("context-file change must request follow-up validation");
} else if (
  !contextReview.followup_message.includes("validate-cursor-config.mjs") ||
  !contextReview.followup_message.includes("test-hooks.mjs") ||
  !contextReview.followup_message.includes("git diff --check") ||
  contextReview.followup_message.includes("validate-cursor-packs.mjs") ||
  contextReview.followup_message.includes("validate-materialized-cursor-pack.mjs")
) {
  failures.push("repository-local stop hook must reference only its installed validation tools");
}

const nonContextReview = runHook(
  "review-context-change.mjs",
  { loop_count: 0, workspace_roots: [path.resolve(toolDirectory, "../..")] },
  { REVA_HOOK_CHANGED_FILES: "src/main.ts\ntest/main.test.ts" }
);
if (Object.keys(nonContextReview).length !== 0) {
  failures.push(`ordinary source changes must not loop, got ${JSON.stringify(nonContextReview)}`);
}

const repeatedReview = runHook(
  "review-context-change.mjs",
  { loop_count: 1, workspace_roots: [path.resolve(toolDirectory, "../..")] },
  { REVA_HOOK_CHANGED_FILES: ".cursor/rules/example/RULE.md" }
);
if (Object.keys(repeatedReview).length !== 0) {
  failures.push(`stop hook must not repeat after loop 0, got ${JSON.stringify(repeatedReview)}`);
}

if (failures.length) {
  process.stderr.write(`${failures.join("\n")}\n`);
  process.exit(1);
}

process.stdout.write(
  `cursor_hook_tests=pass shell=${shellCases.length + 1} read=${readCases.length} stop=3\n`
);

function runHook(fileName, payload, extraEnvironment = {}) {
  return runHookRaw(fileName, JSON.stringify(payload), extraEnvironment);
}

function runHookRaw(fileName, input, extraEnvironment = {}) {
  return runHookAt(
    path.join(hooksDirectory, fileName),
    input,
    extraEnvironment,
    path.resolve(toolDirectory, "../..")
  );
}

function runHookAt(scriptPath, inputOrPayload, extraEnvironment = {}, cwd = process.cwd()) {
  const input =
    typeof inputOrPayload === "string" ? inputOrPayload : JSON.stringify(inputOrPayload);
  const result = spawnSync(process.execPath, [scriptPath], {
    input,
    encoding: "utf8",
    env: { ...process.env, ...extraEnvironment },
    cwd,
    timeout: 5000
  });
  if (result.error) {
    failures.push(`${path.basename(scriptPath)}: execution error ${result.error.message}`);
    return {};
  }
  if (result.status !== 0) {
    failures.push(
      `${path.basename(scriptPath)}: exit ${result.status}; stderr=${result.stderr.trim()}`
    );
    return {};
  }
  const output = result.stdout.trim();
  try {
    return JSON.parse(output);
  } catch (error) {
    failures.push(
      `${path.basename(scriptPath)}: invalid JSON output '${output}': ${error.message}`
    );
    return {};
  }
}
