// src/tools/file_tool.ts — File system tools
// Ported from claude-code-source GlobTool + cheetahclaws/tools/files.py
// Provides glob, grep, read, write, stat, directory listing

import * as fs from 'fs';
import * as path from 'path';
import * as cp from 'child_process';

const DEVIN_ROOT = path.join(__dirname, '../..');

// ── File reading ──────────────────────────────────────────────────────────────

export interface ReadFileResult {
  path: string;
  content: string;
  lines: number;
  size: number;
  encoding: string;
}

export function readFile(filePath: string, startLine = 1, endLine?: number): ReadFileResult {
  const resolved = path.isAbsolute(filePath) ? filePath : path.join(DEVIN_ROOT, filePath);
  const content = fs.readFileSync(resolved, 'utf8');
  const allLines = content.split('\n');
  const start = Math.max(0, startLine - 1);
  const end = endLine ? Math.min(endLine, allLines.length) : allLines.length;
  const selected = allLines.slice(start, end).join('\n');
  return {
    path: resolved,
    content: selected,
    lines: end - start,
    size: fs.statSync(resolved).size,
    encoding: 'utf8',
  };
}

export function readFileSafe(filePath: string): string | null {
  try {
    return fs.readFileSync(filePath, 'utf8');
  } catch {
    return null;
  }
}

// ── File writing ──────────────────────────────────────────────────────────────

export function writeFile(filePath: string, content: string, createDirs = true): void {
  const resolved = path.isAbsolute(filePath) ? filePath : path.join(DEVIN_ROOT, filePath);
  if (createDirs) fs.mkdirSync(path.dirname(resolved), { recursive: true });
  fs.writeFileSync(resolved, content, 'utf8');
}

export function appendFile(filePath: string, content: string): void {
  const resolved = path.isAbsolute(filePath) ? filePath : path.join(DEVIN_ROOT, filePath);
  fs.appendFileSync(resolved, content, 'utf8');
}

// ── String replacement in files (Edit tool pattern from claude-code-source) ────

export function editFile(filePath: string, oldStr: string, newStr: string, all = false): number {
  const resolved = path.isAbsolute(filePath) ? filePath : path.join(DEVIN_ROOT, filePath);
  const content = fs.readFileSync(resolved, 'utf8');
  let count = 0;
  let newContent: string;
  if (all) {
    newContent = content.split(oldStr).join(newStr);
    count = content.split(oldStr).length - 1;
  } else {
    const idx = content.indexOf(oldStr);
    if (idx === -1) throw new Error(`String not found in ${filePath}: ${oldStr.slice(0, 50)}`);
    newContent = content.slice(0, idx) + newStr + content.slice(idx + oldStr.length);
    count = 1;
  }
  fs.writeFileSync(resolved, newContent, 'utf8');
  return count;
}

// ── File stat ─────────────────────────────────────────────────────────────────

export interface FileStat {
  path: string;
  size: number;
  isFile: boolean;
  isDirectory: boolean;
  created: string;
  modified: string;
  permissions: string;
}

export function statFile(filePath: string): FileStat {
  const resolved = path.isAbsolute(filePath) ? filePath : path.join(DEVIN_ROOT, filePath);
  const stat = fs.statSync(resolved);
  return {
    path: resolved,
    size: stat.size,
    isFile: stat.isFile(),
    isDirectory: stat.isDirectory(),
    created: stat.birthtime.toISOString(),
    modified: stat.mtime.toISOString(),
    permissions: (stat.mode & 0o777).toString(8),
  };
}

// ── Directory listing ─────────────────────────────────────────────────────────

export interface DirEntry {
  name: string;
  path: string;
  type: 'file' | 'directory' | 'symlink';
  size: number;
  modified: string;
}

export function listDirectory(dirPath: string, recursive = false, maxDepth = 3): DirEntry[] {
  const resolved = path.isAbsolute(dirPath) ? dirPath : path.join(DEVIN_ROOT, dirPath);
  const entries: DirEntry[] = [];

  function readDir(dir: string, depth: number): void {
    if (depth > maxDepth) return;
    const items = fs.readdirSync(dir, { withFileTypes: true });
    for (const item of items) {
      if (item.name.startsWith('.') && item.name !== '.env') continue;
      const fullPath = path.join(dir, item.name);
      try {
        const stat = fs.statSync(fullPath);
        entries.push({
          name: item.name,
          path: fullPath,
          type: item.isSymbolicLink() ? 'symlink' : item.isDirectory() ? 'directory' : 'file',
          size: stat.size,
          modified: stat.mtime.toISOString(),
        });
        if (recursive && item.isDirectory() && !['node_modules', '.git', '__pycache__'].includes(item.name)) {
          readDir(fullPath, depth + 1);
        }
      } catch { /* permission error */ }
    }
  }

  readDir(resolved, 0);
  return entries;
}

// ── Glob pattern matching (from claude-code-source GlobTool) ──────────────────

export interface GlobResult {
  files: string[];
  count: number;
  truncated: boolean;
  durationMs: number;
}

export function globFiles(pattern: string, searchDir?: string, maxResults = 100): GlobResult {
  const start = Date.now();
  const dir = searchDir
    ? (path.isAbsolute(searchDir) ? searchDir : path.join(DEVIN_ROOT, searchDir))
    : DEVIN_ROOT;

  try {
    // Use ripgrep --files if available, else find
    let output: string;
    try {
      output = cp.execSync(`cd "${dir}" && rg --files --glob "${pattern}" 2>/dev/null | head -${maxResults + 1}`,
        { encoding: 'utf8', timeout: 15000 });
    } catch {
      // Convert glob pattern to find -name pattern (simplified)
      const findPattern = pattern.replace('**/', '').replace(/\*/g, '*');
      output = cp.execSync(
        `find "${dir}" -type f -name "${findPattern}" -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null | head -${maxResults + 1}`,
        { encoding: 'utf8', timeout: 15000 }
      );
    }
    const allFiles = output.trim().split('\n').filter(Boolean);
    const truncated = allFiles.length > maxResults;
    const files = allFiles.slice(0, maxResults).map(f =>
      path.isAbsolute(f) ? f : path.join(dir, f)
    );
    return { files, count: files.length, truncated, durationMs: Date.now() - start };
  } catch {
    return { files: [], count: 0, truncated: false, durationMs: Date.now() - start };
  }
}

// ── Grep (from claude-code-source GrepTool / cheetahclaws/tools/shell.py) ─────

export interface GrepMatch {
  file: string;
  line: number;
  content: string;
}

export interface GrepResult {
  matches: GrepMatch[];
  fileCount: number;
  matchCount: number;
  truncated: boolean;
  durationMs: number;
}

export function grepFiles(
  pattern: string,
  searchPath?: string,
  opts: {
    glob?: string;
    caseInsensitive?: boolean;
    maxResults?: number;
    contextLines?: number;
  } = {}
): GrepResult {
  const start = Date.now();
  const { glob, caseInsensitive, maxResults = 250, contextLines = 0 } = opts;
  const searchDir = searchPath
    ? (path.isAbsolute(searchPath) ? searchPath : path.join(DEVIN_ROOT, searchPath))
    : DEVIN_ROOT;

  const args: string[] = ['--hidden', '--line-number'];
  if (caseInsensitive) args.push('-i');
  if (contextLines) args.push('-C', String(contextLines));
  if (glob) args.push('--glob', glob);
  args.push('--glob', '!.git');
  args.push('--glob', '!node_modules');
  args.push('--max-columns', '500');
  args.push(pattern, searchDir);

  try {
    const output = cp.execSync(`rg ${args.map(a => JSON.stringify(a)).join(' ')} 2>/dev/null`,
      { encoding: 'utf8', timeout: 30000, maxBuffer: 10 * 1024 * 1024 });

    const lines = output.trim().split('\n').filter(Boolean);
    const truncated = lines.length > maxResults;
    const matches = lines.slice(0, maxResults).map(line => {
      const m = line.match(/^([^:]+):(\d+):(.*)$/);
      if (!m) return null;
      return { file: m[1], line: parseInt(m[2]), content: m[3] };
    }).filter(Boolean) as GrepMatch[];

    const files = new Set(matches.map(m => m.file));
    return { matches, fileCount: files.size, matchCount: matches.length, truncated, durationMs: Date.now() - start };
  } catch {
    return { matches: [], fileCount: 0, matchCount: 0, truncated: false, durationMs: Date.now() - start };
  }
}

// ── Delete file/directory ─────────────────────────────────────────────────────

export function deleteFile(filePath: string): void {
  const resolved = path.isAbsolute(filePath) ? filePath : path.join(DEVIN_ROOT, filePath);
  fs.unlinkSync(resolved);
}

export function deleteDirectory(dirPath: string): void {
  const resolved = path.isAbsolute(dirPath) ? dirPath : path.join(DEVIN_ROOT, dirPath);
  fs.rmSync(resolved, { recursive: true, force: true });
}

// ── Copy / move ───────────────────────────────────────────────────────────────

export function copyFile(src: string, dest: string): void {
  const srcR = path.isAbsolute(src) ? src : path.join(DEVIN_ROOT, src);
  const destR = path.isAbsolute(dest) ? dest : path.join(DEVIN_ROOT, dest);
  fs.mkdirSync(path.dirname(destR), { recursive: true });
  fs.copyFileSync(srcR, destR);
}

export function moveFile(src: string, dest: string): void {
  const srcR = path.isAbsolute(src) ? src : path.join(DEVIN_ROOT, src);
  const destR = path.isAbsolute(dest) ? dest : path.join(DEVIN_ROOT, dest);
  fs.mkdirSync(path.dirname(destR), { recursive: true });
  fs.renameSync(srcR, destR);
}

// ── File diff ─────────────────────────────────────────────────────────────────

export function diffFiles(fileA: string, fileB: string): string {
  try {
    return cp.execSync(`diff "${fileA}" "${fileB}"`, { encoding: 'utf8' });
  } catch (e: unknown) {
    const err = e as { stdout?: string };
    return err.stdout || '';
  }
}

// ── Find in tree (cheetahclaws/tools/files.py find_in_tree) ──────────────────

export function findFiles(
  searchDir: string,
  opts: { name?: string; extension?: string; minSize?: number; maxSize?: number; maxDepth?: number }
): string[] {
  const dir = path.isAbsolute(searchDir) ? searchDir : path.join(DEVIN_ROOT, searchDir);
  const parts = [`find "${dir}"`];
  if (opts.maxDepth) parts.push(`-maxdepth ${opts.maxDepth}`);
  parts.push('-type f');
  if (opts.name) parts.push(`-name "${opts.name}"`);
  if (opts.extension) parts.push(`-name "*.${opts.extension.replace(/^\./, '')}"`);
  if (opts.minSize) parts.push(`-size +${opts.minSize}c`);
  if (opts.maxSize) parts.push(`-size -${opts.maxSize}c`);
  parts.push('-not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/__pycache__/*"');
  try {
    return cp.execSync(parts.join(' ') + ' 2>/dev/null | head -500',
      { encoding: 'utf8', timeout: 30000 }).trim().split('\n').filter(Boolean);
  } catch {
    return [];
  }
}
