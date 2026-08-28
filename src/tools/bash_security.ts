// src/tools/bash_security.ts — Bash command safety classification
// Ported from cheetahclaws/tools/security.py and claude-code-source/BashTool patterns
// Classifies commands as read-only, search, list, write, or destructive

// ── Read-only commands (from cheetahclaws/tools/security.py) ─────────────────
const READ_ONLY_COMMANDS = new Set([
  // Filesystem inspection
  'ls', 'll', 'la', 'pwd', 'stat', 'file', 'tree', 'realpath', 'readlink',
  'basename', 'dirname', 'du', 'df', 'mountpoint',
  // File contents
  'cat', 'head', 'tail', 'nl', 'wc', 'od', 'xxd', 'strings', 'base64',
  'md5sum', 'sha1sum', 'sha256sum', 'sha512sum', 'cksum',
  'diff', 'cmp', 'comm',
  // Text processing
  'sort', 'uniq', 'cut', 'tr', 'rev', 'fold', 'paste', 'join', 'column',
  'jq', 'yq', 'sed', 'grep', 'egrep', 'fgrep', 'rg', 'ag', 'fd', 'find',
  // Environment/system introspection
  'echo', 'printf', 'date', 'cal', 'uptime', 'hostname', 'uname',
  'whoami', 'id', 'groups', 'which', 'type', 'command', 'env', 'printenv',
  'locale', 'nproc', 'arch', 'lscpu', 'lsblk', 'free', 'ps',
  'netstat', 'ss', 'lsof', 'ulimit', 'tty',
]);

// Read-only subcommands per tool (from cheetahclaws/tools/security.py)
const READ_ONLY_SUBCOMMANDS: Record<string, Set<string>> = {
  git: new Set([
    'log', 'status', 'diff', 'show', 'branch', 'remote', 'tag', 'blame',
    'describe', 'rev-parse', 'rev-list', 'ls-files', 'ls-tree', 'ls-remote',
    'cat-file', 'shortlog', 'whatchanged', 'reflog', 'count-objects',
    'grep', 'annotate', 'difftool', 'verify-commit', 'check-ignore',
    'config', 'stash', 'worktree', 'submodule',
  ]),
  docker: new Set(['ps', 'images', 'image', 'logs', 'inspect', 'version', 'info', 'top', 'stats', 'port', 'diff', 'history']),
  kubectl: new Set(['get', 'describe', 'logs', 'top', 'version', 'explain', 'api-resources', 'cluster-info']),
  npm: new Set(['ls', 'list', 'view', 'info', 'outdated', 'why', 'ping']),
  pip: new Set(['show', 'list', 'freeze', 'check']),
  pip3: new Set(['show', 'list', 'freeze', 'check']),
  cargo: new Set(['metadata', 'tree', 'search', 'verify-project']),
  go: new Set(['list', 'env', 'version', 'doc']),
  systemctl: new Set(['status', 'list-units', 'list-unit-files', 'show', 'is-active', 'is-enabled', 'cat']),
};

// Destructive commands — always require confirmation
const DESTRUCTIVE_COMMANDS = new Set([
  'rm', 'rmdir', 'shred', 'dd', 'mkfs', 'fdisk', 'parted',
  'chmod', 'chown', 'chattr', 'setfacl',
  'systemctl', 'service', 'reboot', 'shutdown', 'halt', 'poweroff',
  'kill', 'killall', 'pkill',
  'sudo', 'su', 'doas',
  'iptables', 'ip6tables', 'nft', 'ufw',
  'crontab', 'at', 'batch',
  'useradd', 'userdel', 'usermod', 'groupadd', 'groupdel', 'passwd',
  'mount', 'umount',
  'format', 'fdisk', 'mkswap', 'swapon', 'swapoff',
]);

// Search commands (from claude-code-source/BashTool patterns)
const SEARCH_COMMANDS = new Set(['find', 'grep', 'rg', 'ag', 'ack', 'locate', 'which', 'whereis', 'fzf']);

// List commands (directory listing)
const LIST_COMMANDS = new Set(['ls', 'tree', 'du', 'find', 'fd']);

// Read/view commands
const READ_COMMANDS = new Set(['cat', 'head', 'tail', 'less', 'more', 'wc', 'stat', 'file', 'strings', 'jq', 'awk', 'cut', 'sort', 'uniq', 'tr']);

// Semantically neutral (output-only, pipeline helpers)
const SEMANTIC_NEUTRAL = new Set(['echo', 'printf', 'true', 'false', 'tee', 'xargs']);

// ── Classification ────────────────────────────────────────────────────────────

export type CommandClass =
  | 'read_only'     // safe, no confirmation needed
  | 'search'        // safe, grep/find style
  | 'list'          // safe, directory listing
  | 'write'         // modifies files, needs confirmation in default mode
  | 'destructive'   // high risk, always needs confirmation
  | 'network'       // network access
  | 'privilege'     // sudo/su
  | 'unknown';

function extractProgram(cmd: string): string {
  const parts = cmd.trim().split(/\s+/);
  // Skip env var assignments at start
  let i = 0;
  while (i < parts.length && parts[i].includes('=')) i++;
  return parts[i] || '';
}

function extractSubcommand(cmd: string): string {
  const parts = cmd.trim().split(/\s+/).filter(p => !p.startsWith('-'));
  return parts[1] || '';
}

export function classifyCommand(cmd: string): CommandClass {
  if (!cmd.trim()) return 'unknown';

  // Split on pipes and semicolons, classify each segment
  const segments = cmd.split(/[|;&]/).map(s => s.trim()).filter(Boolean);
  let maxRisk: CommandClass = 'read_only';

  const riskOrder: Record<CommandClass, number> = {
    read_only: 0, list: 0, search: 0,
    network: 1, write: 2, privilege: 3, destructive: 4, unknown: 5,
  };

  for (const seg of segments) {
    const prog = extractProgram(seg);
    if (!prog) continue;

    let segClass: CommandClass = 'unknown';

    if (SEMANTIC_NEUTRAL.has(prog)) {
      segClass = 'read_only';
    } else if (READ_ONLY_COMMANDS.has(prog)) {
      if (SEARCH_COMMANDS.has(prog)) segClass = 'search';
      else if (LIST_COMMANDS.has(prog)) segClass = 'list';
      else segClass = 'read_only';
    } else if (prog in READ_ONLY_SUBCOMMANDS) {
      const sub = extractSubcommand(seg);
      segClass = READ_ONLY_SUBCOMMANDS[prog]?.has(sub) ? 'read_only' : 'write';
    } else if (DESTRUCTIVE_COMMANDS.has(prog)) {
      segClass = prog === 'sudo' || prog === 'su' || prog === 'doas' ? 'privilege' : 'destructive';
    } else if (['curl', 'wget', 'nc', 'ncat', 'netcat', 'ssh', 'scp', 'rsync', 'nmap'].includes(prog)) {
      segClass = 'network';
    } else if (['cp', 'mv', 'touch', 'mkdir', 'ln', 'truncate', 'tee', 'write'].includes(prog)) {
      segClass = 'write';
    } else if (['python', 'python3', 'node', 'ruby', 'perl', 'bash', 'sh', 'zsh'].includes(prog)) {
      segClass = 'unknown'; // interpreter — could do anything
    } else {
      segClass = 'unknown';
    }

    if (riskOrder[segClass] > riskOrder[maxRisk]) maxRisk = segClass;
  }

  return maxRisk;
}

export function isReadOnly(cmd: string): boolean {
  const cls = classifyCommand(cmd);
  return cls === 'read_only' || cls === 'search' || cls === 'list';
}

export function requiresConfirmation(cmd: string): boolean {
  const cls = classifyCommand(cmd);
  return cls === 'write' || cls === 'network' || cls === 'unknown' ||
    cls === 'destructive' || cls === 'privilege';
}

export function classifyCommandVerbose(cmd: string): {
  classification: CommandClass;
  readOnly: boolean;
  requiresConfirmation: boolean;
  summary: string;
} {
  const classification = classifyCommand(cmd);
  const readOnly = classification === 'read_only' || classification === 'search' || classification === 'list';
  const needs = requiresConfirmation(cmd);

  const summaryMap: Record<CommandClass, string> = {
    read_only: 'Read-only — safe to run without confirmation',
    search: 'Search command — safe',
    list: 'Directory listing — safe',
    write: 'Writes to filesystem — confirm in default mode',
    network: 'Network access — confirm in default mode',
    destructive: 'DESTRUCTIVE — always confirm',
    privilege: 'ELEVATED PRIVILEGE (sudo) — always confirm',
    unknown: 'Unknown — confirm to be safe',
  };

  return {
    classification,
    readOnly,
    requiresConfirmation: needs,
    summary: summaryMap[classification],
  };
}

// ── Path traversal guard (from cheetahclaws/tools/security.py) ───────────────

export function isPathTraversal(filePath: string, allowedRoot: string): boolean {
  const resolved = require('path').resolve(filePath);
  return !resolved.startsWith(allowedRoot);
}

export function sanitizePath(filePath: string): string {
  // Remove null bytes, normalize separators
  return filePath.replace(/\0/g, '').replace(/\/+/g, '/');
}
