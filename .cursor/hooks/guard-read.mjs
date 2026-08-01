import path from "node:path";
import process from "node:process";

const input = await readStdin();

let payload;
try {
  payload = JSON.parse(input);
} catch {
  respond({
    permission: "deny",
    user_message: "Cursor read guard could not parse the hook payload; file access denied safely."
  });
}

const filePath = extractString(payload, [
  ["file_path"],
  ["path"],
  ["tool_input", "file_path"],
  ["tool_input", "path"],
  ["args", "file_path"],
  ["args", "path"]
]);

if (!filePath) {
  respond({
    permission: "deny",
    user_message: "Cursor read guard received no file path; file access denied safely."
  });
}

const normalized = filePath.replaceAll("\\", "/");
const base = path.posix.basename(normalized);

if (isSafeTemplate(normalized, base)) {
  respond({ permission: "allow" });
}

if (isSensitive(normalized, base)) {
  respond({
    permission: "deny",
    user_message: "Blocked Cursor access to a credential, private key, infrastructure state, or local secret file."
  });
}

respond({ permission: "allow" });

function isSafeTemplate(fullPath, baseName) {
  if (/^\.env(?:\.[a-z0-9_-]+)*\.(?:example|sample)$/iu.test(baseName)) {
    return true;
  }
  if (/^\.(?:npmrc|pnpmrc|yarnrc(?:\.yml)?)\.(?:example|sample)$/iu.test(baseName)) {
    return true;
  }
  return /(?:^|\/)\.docker\/config\.(?:example|sample)\.json$/iu.test(fullPath);
}

function isSensitive(fullPath, baseName) {
  const basePatterns = [
    /^\.env(?:\..+)?$/iu,
    /^creds\.env$/iu,
    /^credentials(?:\.[^.]+)?$/iu,
    /^(?:\.netrc|\.git-credentials)$/iu,
    /^(?:\.pypirc|pip\.(?:conf|ini)|\.npmrc(?:\..+)?|\.pnpmrc(?:\..+)?|\.yarnrc(?:\.yml)?(?:\..+)?)$/iu,
    /^(?:kubeconfig)(?:\..+)?$/iu,
    /\.(?:pem|key|p12|pfx|pkcs12|jks|keystore)$/iu,
    /\.tfstate(?:\..+)?$/iu,
    /\.(?:sql|mongo)\.dump$/iu,
    /\.(?:pgdump|bson|bson\.gz)$/iu,
    /\.rdb$/iu,
    /(?:^|-)secrets?\.local(?:\.|$)/iu,
    /^core(?:\.\d+)?$/iu,
    /\.hprof$/iu
  ];

  if (basePatterns.some((pattern) => pattern.test(baseName))) {
    return true;
  }

  return /(?:^|\/)(?:\.aws\/(?:credentials|config)|\.kube\/config|\.docker\/config\.json(?:\..+)?|\.terraform\/|credentials\.local\/|secrets?\.local(?:\.|\/)|secret-values\.local(?:\.|\/))/iu.test(
    fullPath
  );
}

function extractString(value, paths) {
  for (const candidatePath of paths) {
    let current = value;
    for (const segment of candidatePath) {
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
