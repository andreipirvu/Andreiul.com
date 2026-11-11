#!/usr/bin/env node
// PreToolUse guard: block Claude Code from reading or writing secret files (R-02).
// Written in Node because Claude Code always ships with it, so the hook works on
// Windows, macOS and Linux without jq. It fails closed: input it cannot parse is blocked.
// Exit 2 blocks the tool call; stderr is the reason Claude sees.

const SECRET = [
  /(^|[\\/])\.env(\.[^\\/]*)?$/i,           // .env, .env.local, .env.production
  /\.env$/i,                                // aws.env, creds.env
  /(^|[\\/])secrets?[\\/]/i,                // secrets/ or secret/ at any depth
  /\.(key|pem|p12|pfx|secret)$/i,           // private keys and certificates
  /(^|[\\/])id_(rsa|ed25519|ecdsa)[^\\/]*$/i,
  /(^|[\\/])\.git-credentials$/i,
  /(^|[\\/])\.ssh[\\/]/i,
];
// For shell commands: the same names anywhere in the command line.
const SECRET_IN_COMMAND =
  /(^|[\s"'=\/\\])(\.env(\.[\w.-]+)?|[\w.-]+\.env|secrets?\/|[\w.-]+\.(key|pem|p12|pfx)|id_(rsa|ed25519|ecdsa)|\.git-credentials|\.ssh\/)(?=$|[\s"';|&)<>])/i;
const ALLOWED = [/(^|[\\/])\.env\.example$/i];

function block(reason) {
  process.stderr.write(`Blocked by policy (R-02): ${reason}\n`);
  process.exit(2);
}

let raw = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (c) => (raw += c));
process.stdin.on('end', () => {
  let input;
  try {
    input = JSON.parse(raw);
  } catch {
    block('hook input was not valid JSON, failing closed');
  }
  const tool = input.tool_name || '';
  const ti = input.tool_input || {};

  if (tool === 'Bash') {
    const cmd = String(ti.command || '');
    if (SECRET_IN_COMMAND.test(cmd) && !/\.env\.example\b/i.test(cmd)) {
      block(`the command touches a secret path: ${cmd.slice(0, 200)}`);
    }
    process.exit(0);
  }

  const paths = [ti.file_path, ti.notebook_path, ti.path, ti.pattern, ti.glob]
    .filter((p) => typeof p === 'string' && p.length > 0);
  for (const p of paths) {
    if (ALLOWED.some((re) => re.test(p))) continue;
    if (SECRET.some((re) => re.test(p))) block(`${p} is a secret path`);
  }
  process.exit(0);
});
