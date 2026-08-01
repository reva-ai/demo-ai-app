import process from "node:process";

const input = await readStdin();

let payload;
try {
  payload = JSON.parse(input);
} catch {
  respond({
    permission: "deny",
    user_message: "Cursor shell guard could not parse the hook payload; command denied safely.",
    agent_message: "Do not retry through another shell form. Ask the user to validate the pinned Cursor hook contract."
  });
}

const command = extractString(payload, [
  ["command"],
  ["tool_input", "command"],
  ["args", "command"],
  ["input", "command"]
]);

if (!command) {
  respond({
    permission: "deny",
    user_message: "Cursor shell guard received no command; execution denied safely.",
    agent_message: "Inspect the pinned Cursor hook payload schema before retrying."
  });
}

const normalized = command.replace(/\s+/gu, " ").trim();

if (isCatastrophicRemoval(normalized)) {
  respond({
    permission: "deny",
    user_message: "Blocked a recursive deletion targeting a broad or unresolved path.",
    agent_message: "Resolve and validate a narrow explicit target. Prefer a recoverable operation."
  });
}

if (isProtectedForcePush(normalized)) {
  respond({
    permission: "deny",
    user_message: "Force-pushing a protected branch is blocked by the Reva Cursor baseline.",
    agent_message: "Use a feature branch and normal reviewed merge flow."
  });
}

if (referencesSensitivePath(normalized)) {
  respond({
    permission: "deny",
    user_message:
      "Blocked a shell command that references a credential, private key, state, dump, or " +
      "local secret path.",
    agent_message:
      "Do not retry with another reader, encoder, interpreter, or shell form. Use a reviewed " +
      "example/template file or ask the user for a redacted value."
  });
}

if (mustRunOutsideAgent(normalized)) {
  respond({
    permission: "deny",
    user_message:
      "This command can delete data, change Git state, publish code, expose credentials, or " +
      "affect infrastructure. Run it outside the Cursor agent only after human review.",
    agent_message:
      "Do not retry through another shell form. Report the resolved target, impact, " +
      "recovery/rollback, and the manual command for an authorized operator."
  });
}

respond({ permission: "allow" });

function referencesSensitivePath(commandText) {
  const withoutSafeTemplates = commandText
    .replace(
      /\.env(?:\.[a-z0-9_-]+)*\.(?:example|sample)(?=$|[\s'"`;,|)&\]])/giu,
      ""
    )
    .replace(
      /\.(?:npmrc|pnpmrc|yarnrc(?:\.yml)?)\.(?:example|sample)(?=$|[\s'"`;,|)&\]])/giu,
      ""
    )
    .replace(
      /\.docker\/config\.(?:example|sample)\.json(?=$|[\s'"`;,|)&\]])/giu,
      ""
    );

  const sensitivePatterns = [
    /\/proc\/(?:self|[0-9]+)\/environ(?=$|[\s'"`;,|)&\]])/iu,
    /(?:^|[\/\s'"`=(,])(?:~|\$HOME|\$\{HOME\}|\/Users\/[^/\s]+|\/home\/[^/\s]+|\/root)\/\.ssh\/id_[A-Za-z0-9._-]+(?=$|[\s'"`;,|)&\]])/u,
    /(?:^|[\/\s'"`=(,])(?:~|\$HOME|\$\{HOME\}|\/Users\/[^/\s]+|\/home\/[^/\s]+|\/root)\/\.aws\/credentials(?=$|[\s'"`;,|)&\]])/u,
    /(?:^|[\/\s'"`=(,])(?:~|\$HOME|\$\{HOME\}|\/Users\/[^/\s]+|\/home\/[^/\s]+|\/root)\/\.kube\/config(?=$|[\s'"`;,|)&\]])/u,
    /(?:^|[\/\s'"`=(,])(?:~|\$HOME|\$\{HOME\}|\/Users\/[^/\s]+|\/home\/[^/\s]+|\/root)\/\.config\/(?:gh\/hosts\.yml|glab-cli\/config\.yml|gcloud\/application_default_credentials\.json)(?=$|[\s'"`;,|)&\]])/u,
    /(?:^|[\/\s'"`=(,])\.env(?:\.[a-z0-9_-]+)*(?=$|[\/\s'"`;,|)&\]])/iu,
    /(?:^|[\/\s'"`=(,])(?:\.npmrc(?:\.[a-z0-9_-]+)*|\.pnpmrc(?:\.[a-z0-9_-]+)*|\.yarnrc(?:\.yml)?(?:\.[a-z0-9_-]+)*)(?=$|[\/\s'"`;,|)&\]])/iu,
    /(?:^|[\/\s'"`=(,])\.docker\/config\.json(?:\.[a-z0-9_-]+)*(?=$|[\s'"`;,|)&\]])/iu,
    /(?:^|[\/\s'"`=(,])(?:\.netrc|\.git-credentials|\.pypirc)(?=$|[\/\s'"`;,|)&\]])/iu,
    /(?:^|[\/\s'"`=(,])(?:credentials|kubeconfig)(?:\.[a-z0-9_-]+)?(?=$|[\/\s'"`;,|)&\]])/iu,
    /\.(?:pem|key|p12|pfx|pkcs12|jks|keystore|tfstate|pgdump|bson|rdb)(?=$|[\s'"`;,|)&\]])/iu,
    /(?:^|[\/\s'"`=(,])(?:secrets?\.local|secret-values\.local)(?:[./][^\s'"`;|)&\]]*)?/iu
  ];

  return sensitivePatterns.some((pattern) => pattern.test(withoutSafeTemplates));
}

function isCatastrophicRemoval(commandText) {
  const hasRm = /(?:^|[\s;&|])(?:sudo\s+)?(?:\/[^\s;&|]+\/)?rm(?:\s|$)/iu.test(commandText);
  const hasRecursive = /(?:^|\s)(?:--recursive(?:=true)?|-[a-z]*r[a-z]*)\b/iu.test(commandText);
  const hasForce = /(?:^|\s)(?:--force(?:=true)?|-[a-z]*f[a-z]*)\b/iu.test(commandText);
  if (!hasRm || !hasRecursive || !hasForce) {
    return false;
  }

  return /(?:^|\s)(?:\/|~(?:\/|\s|$)|\$HOME(?:\/|\s|$)|\$\{HOME\}(?:\/|\s|$)|\.(?:\/|\s|$)|\.\.(?:\/|\s|$))/u.test(
    commandText
  );
}

function isProtectedForcePush(commandText) {
  const gitPush = /\bgit\b(?:(?![;&|]).){0,300}\bpush\b/iu.test(commandText);
  if (!gitPush || !/(?:--force(?:-with-lease)?(?:=[^\s]+)?|-f)\b/iu.test(commandText)) {
    return false;
  }

  // The hook cannot reliably resolve the current/upstream branch. Deny every agent force-push;
  // an authorized operator may perform a reviewed feature-branch lease push outside Agent.
  return true;
}

function mustRunOutsideAgent(commandText) {
  if (containsUnapprovedAwsCommand(commandText)) {
    return true;
  }

  const patterns = [
    /(?:^|[\s;&|])(?:sudo\s+)?(?:\/[^\s;&|]+\/)?rm(?:\s|$)/iu,
    /\bgit\b(?:(?![;&|]).){0,300}\b(?:push|commit|tag|merge|rebase|cherry-pick|revert|reset\s+--hard|clean\b(?:(?![;&|]).){0,80}(?:--force|-f)\b|checkout\s+(?:\.|HEAD\b(?:(?![;&|]).){0,80}--|-{1,2}(?:force|f|B)\b|--\b)|switch\s+-C\b|branch\b(?:(?![;&|]).){0,80}(?:-[dD]\b|--delete\b)|stash\s+(?:clear|drop|pop)\b|worktree\s+(?:remove|move|prune)\b|update-ref\b|remote\s+(?:add|remove|rename|set-head|set-url|prune|update)\b|restore\b)/iu,
    /\bfind\b(?:(?![;&|]).){0,400}(?:-delete\b|-exec(?:dir)?\s+(?:\/[^\s;&|]+\/)?rm\b)/iu,
    /\b(?:shred|truncate|unlink|rmdir)\b/iu,
    /\bkubectl\b(?:(?![;&|]).){0,300}\b(?:create|delete|apply|replace|patch|edit|set|label|annotate|taint|scale|rollout|cordon|uncordon|drain|expose|run|exec|attach|cp|debug|port-forward|proxy)\b/iu,
    /\bkubectl\b(?:(?![;&|]).){0,300}\bauth\s+reconcile\b/iu,
    /\bkubectl\b(?:(?![;&|]).){0,300}\bconfig\s+(?:delete|rename|set|unset|use-context)\b/iu,
    /\bkubectl\b(?:(?![;&|]).){0,300}\bconfig\s+view\b(?:(?![;&|]).){0,100}--raw(?:\s|$)/iu,
    /\bkubectl\b(?:(?![;&|]).){0,300}\b(?:get|describe)\s+(?:secret|secrets)\b/iu,
    /\bhelm\b(?:(?![;&|]).){0,300}\b(?:install|upgrade|uninstall|rollback|push|registry\s+login|repo\s+(?:add|remove))\b/iu,
    /\bterraform\b(?:(?![;&|]).){0,300}\b(?:apply|destroy|import|force-unlock|taint|untaint|output|show|workspace\s+(?:new|delete)|state\s+(?:rm|mv|push|pull))\b/iu,
    /\b(?:npm|pnpm|yarn)\b(?:(?![;&|]).){0,100}\bpublish\b/iu,
    /(?:^|[\s;&|])(?:\.\/)?mvnw?\b(?:(?![;&|]).){0,200}\bdeploy\b/iu,
    /(?:^|[\s;&|])(?:\.\/)?gradlew?\b(?:(?![;&|]).){0,200}\bpublish\w*\b/iu,
    /\b(?:twine\b(?:(?![;&|]).){0,100}\bupload|uv\s+publish|poetry\s+publish|cargo\s+publish)\b/iu,
    /\bdocker\b(?:(?![;&|]).){0,100}\bpush\b/iu,
    /(?:^|[;&|]\s*)(?:sudo\s+)?(?:\/usr\/bin\/)?env\s*(?:$|[;&|])/iu,
    /\bprintenv\b/iu,
    /(?:^|[;&|]\s*)(?:set|export|declare\s+-x)\s*(?:$|[;&|])/iu,
    /\b(?:process\.env|os\.environ|System\.getenv|Deno\.env)\b/u,
    /\bgo\s+env\s+(?:-json\s*(?:$|[;&|])|GOPROXY\b|GONOPROXY\b|GOAUTH\b)/iu,
    /\b(?:cat|sed|awk|head|tail|less|more)\b[^\\n]*(?:\.env|credentials|\.pem|\.key|tfstate)/iu
  ];

  return patterns.some((pattern) => pattern.test(commandText));
}

function containsUnapprovedAwsCommand(commandText) {
  const segments = commandText.split(/\s*(?:&&|\|\||[;|])\s*/u);
  for (const segment of segments) {
    const match = segment.match(/(?:^|\s)(?:(?:\/[^\s]+\/)?aws)\b(?<arguments>.*)$/iu);
    if (!match) {
      continue;
    }
    const invocation = `aws${match.groups.arguments}`.trim();
    const versionOnly = /^aws\s+--version$/iu.test(invocation);
    const callerIdentity =
      /^aws(?:(?:\s+--(?:profile|region|endpoint-url|output)(?:=\S+|\s+\S+))|(?:\s+--no-cli-pager))*\s+sts\s+get-caller-identity(?:(?:\s+--(?:output|query)(?:=\S+|\s+\S+))|(?:\s+--no-cli-pager))*$/iu.test(
        invocation
      );
    if (!versionOnly && !callerIdentity) {
      return true;
    }
  }
  return false;
}

function extractString(value, paths) {
  for (const path of paths) {
    let current = value;
    for (const segment of path) {
      current = current?.[segment];
    }
    if (typeof current === "string" && current.trim()) {
      return current;
    }
  }
  return "";
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
