// src/os/control.ts — OS-level control utilities (TypeScript native)

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import * as cp from 'child_process';

export interface ProcessInfo {
  pid: number;
  name: string;
  cpu: number;
  memory: number;
  status: string;
}

export interface SystemInfo {
  platform: string;
  arch: string;
  hostname: string;
  uptime: number;
  cpuCount: number;
  cpuModel: string;
  totalMemMb: number;
  freeMemMb: number;
  cwd: string;
  user: string;
}

export function getSystemInfo(): SystemInfo {
  const cpus = os.cpus();
  return {
    platform: os.platform(),
    arch: os.arch(),
    hostname: os.hostname(),
    uptime: os.uptime(),
    cpuCount: cpus.length,
    cpuModel: cpus[0]?.model || 'Unknown',
    totalMemMb: Math.round(os.totalmem() / 1024 / 1024),
    freeMemMb: Math.round(os.freemem() / 1024 / 1024),
    cwd: process.cwd(),
    user: os.userInfo().username,
  };
}

export function listProcesses(filter?: string): ProcessInfo[] {
  try {
    const output = cp.execSync(
      `ps aux --no-headers ${filter ? `| grep -i "${filter}"` : ''} | head -30`,
      { encoding: 'utf8' }
    );
    return output.trim().split('\n').map(line => {
      const parts = line.trim().split(/\s+/);
      return {
        pid: parseInt(parts[1] || '0', 10),
        name: parts[10] || 'unknown',
        cpu: parseFloat(parts[2] || '0'),
        memory: parseFloat(parts[3] || '0'),
        status: parts[7] || 'unknown',
      };
    }).filter(p => p.pid > 0);
  } catch {
    return [];
  }
}

export function readFile(filePath: string, offset?: number, limit?: number): string {
  const p = path.resolve(filePath);
  const content = fs.readFileSync(p, 'utf8');
  if (offset === undefined && limit === undefined) return content;
  const lines = content.split('\n');
  const start = offset ? offset - 1 : 0;
  const end = limit ? start + limit : lines.length;
  return lines.slice(start, end).map((l, i) => `${start + i + 1}\t${l}`).join('\n');
}

export function writeFile(filePath: string, content: string): void {
  const p = path.resolve(filePath);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, content, 'utf8');
}

export function runCommand(cmd: string, cwd?: string, timeout = 30000): {
  stdout: string; stderr: string; exitCode: number;
} {
  try {
    const stdout = cp.execSync(cmd, {
      cwd: cwd || process.cwd(),
      timeout,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return { stdout, stderr: '', exitCode: 0 };
  } catch (e: unknown) {
    const err = e as { stdout?: string; stderr?: string; status?: number };
    return {
      stdout: err.stdout || '',
      stderr: err.stderr || String(e),
      exitCode: err.status || 1,
    };
  }
}

export function getDiskUsage(dirPath = '/'): { total: number; used: number; free: number; percent: number } {
  try {
    const output = cp.execSync(`df -k "${dirPath}" | tail -1`, { encoding: 'utf8' });
    const parts = output.trim().split(/\s+/);
    const total = parseInt(parts[1] || '0', 10) * 1024;
    const used = parseInt(parts[2] || '0', 10) * 1024;
    const free = parseInt(parts[3] || '0', 10) * 1024;
    const percent = total > 0 ? Math.round((used / total) * 100) : 0;
    return { total, used, free, percent };
  } catch {
    return { total: 0, used: 0, free: 0, percent: 0 };
  }
}

export function getNetworkInterfaces(): Record<string, string[]> {
  const ifaces = os.networkInterfaces();
  const result: Record<string, string[]> = {};
  for (const [name, addrs] of Object.entries(ifaces)) {
    result[name] = (addrs || []).map(a => `${a.address}/${a.cidr || '?'} (${a.family})`);
  }
  return result;
}
