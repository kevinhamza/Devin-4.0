// src/security/web_scanner.ts — Web application security scanner
// Ported from external/hackability/ + airgorah (WiFi) + cheetahclaws security patterns
// REQUIRES AUTHORIZATION: Only use on systems you own or have explicit permission

import * as cp from 'child_process';
import * as path from 'path';
import { httpFetch, extractTextFromHTML } from '../tools/web_tool.js';

const DEVIN_ROOT = path.join(__dirname, '../..');

// ── Directory/path discovery ──────────────────────────────────────────────────

const COMMON_PATHS = [
  '/admin', '/login', '/wp-admin', '/phpmyadmin', '/cpanel', '/manager',
  '/api', '/api/v1', '/api/v2', '/graphql', '/swagger', '/openapi.json',
  '/robots.txt', '/sitemap.xml', '/.env', '/.git/HEAD', '/config.php',
  '/wp-config.php', '/web.config', '/backup', '/admin.php', '/console',
  '/actuator', '/actuator/health', '/server-status', '/.htaccess',
];

export interface PathScanResult {
  url: string;
  status: number;
  found: boolean;
  title?: string;
  size: number;
}

export async function scanPaths(
  baseUrl: string,
  authorized: boolean,
  customPaths?: string[]
): Promise<PathScanResult[]> {
  if (!authorized) throw new Error('Authorization required for path scanning.');
  const paths = customPaths || COMMON_PATHS;
  const results: PathScanResult[] = [];
  const base = baseUrl.replace(/\/$/, '');

  for (const p of paths) {
    const url = base + p;
    try {
      const res = await httpFetch(url, { timeoutMs: 5000 });
      if (res.status < 400) {
        const title = res.text.match(/<title>(.*?)<\/title>/i)?.[1]?.trim();
        results.push({
          url,
          status: res.status,
          found: true,
          title,
          size: res.text.length,
        });
      }
    } catch { /* unreachable */ }
  }
  return results;
}

// ── XSS probe (from hackability patterns) ─────────────────────────────────────

const XSS_PAYLOADS = [
  '<script>alert(1)</script>',
  '"><script>alert(1)</script>',
  "'><img src=x onerror=alert(1)>",
  '{{7*7}}',
  '${7*7}',
];

export async function testXSS(
  url: string,
  paramName: string,
  authorized: boolean
): Promise<{ vulnerable: boolean; payload?: string; evidence?: string }> {
  if (!authorized) throw new Error('Authorization required.');
  for (const payload of XSS_PAYLOADS) {
    try {
      const testUrl = url.includes('?')
        ? `${url}&${paramName}=${encodeURIComponent(payload)}`
        : `${url}?${paramName}=${encodeURIComponent(payload)}`;
      const res = await httpFetch(testUrl, { timeoutMs: 8000 });
      // Check if payload is reflected unescaped
      if (res.text.includes(payload)) {
        return { vulnerable: true, payload, evidence: `Reflected in response body` };
      }
      // Check for SSTI indicator
      if (payload.includes('7*7') && res.text.includes('49')) {
        return { vulnerable: true, payload, evidence: `Template injection: 7*7=49 computed` };
      }
    } catch { /* skip */ }
  }
  return { vulnerable: false };
}

// ── SQL injection probe ────────────────────────────────────────────────────────

const SQLI_PAYLOADS = [
  { payload: "'", errorPatterns: ['sql syntax', 'mysql_fetch', 'ora-0', 'sqlite_'] },
  { payload: '" OR "1"="1', errorPatterns: ['you have an error', 'warning: mysql'] },
  { payload: "' OR '1'='1' --", errorPatterns: ['sql syntax', 'mysql_fetch'] },
  { payload: '1 AND 1=2', errorPatterns: [] }, // boolean-based
];

export async function testSQLi(
  url: string,
  paramName: string,
  authorized: boolean
): Promise<{ vulnerable: boolean; type?: string; evidence?: string }> {
  if (!authorized) throw new Error('Authorization required.');
  // Baseline response
  let baseline = '';
  try {
    const baseRes = await httpFetch(`${url}?${paramName}=1`, { timeoutMs: 8000 });
    baseline = baseRes.text;
  } catch {
    return { vulnerable: false };
  }

  for (const { payload, errorPatterns } of SQLI_PAYLOADS) {
    try {
      const testUrl = `${url}?${paramName}=${encodeURIComponent(payload)}`;
      const res = await httpFetch(testUrl, { timeoutMs: 8000 });
      const body = res.text.toLowerCase();

      for (const pattern of errorPatterns) {
        if (body.includes(pattern)) {
          return { vulnerable: true, type: 'error-based', evidence: `Error pattern: ${pattern}` };
        }
      }
      // Check significant response difference (boolean-based)
      if (Math.abs(res.text.length - baseline.length) > baseline.length * 0.3) {
        return { vulnerable: true, type: 'boolean-based', evidence: `Response length changed significantly: ${baseline.length} → ${res.text.length}` };
      }
    } catch { /* skip */ }
  }
  return { vulnerable: false };
}

// ── HTTP method testing ────────────────────────────────────────────────────────

export async function testHTTPMethods(url: string, authorized: boolean): Promise<Record<string, number>> {
  if (!authorized) throw new Error('Authorization required.');
  const methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'TRACE', 'HEAD'];
  const results: Record<string, number> = {};
  for (const method of methods) {
    try {
      const res = await httpFetch(url, { method: method as 'GET' | 'POST', timeoutMs: 5000 });
      results[method] = res.status;
    } catch {
      results[method] = 0;
    }
  }
  return results;
}

// ── WiFi scanning (from airgorah Rust patterns via system tools) ───────────────

export interface WiFiNetwork {
  ssid: string;
  bssid: string;
  channel: number;
  signal: number;
  encryption: string;
}

export function scanWiFiNetworks(authorized: boolean): WiFiNetwork[] {
  if (!authorized) throw new Error('Authorization required for WiFi scanning.');
  try {
    const output = cp.execSync('nmcli -t -f SSID,BSSID,CHAN,SIGNAL,SECURITY dev wifi list 2>/dev/null',
      { encoding: 'utf8', timeout: 15000 });
    return output.trim().split('\n').filter(Boolean).map(line => {
      const parts = line.split(':');
      return {
        ssid: parts[0] || '',
        bssid: parts.slice(1, 7).join(':') || '',
        channel: parseInt(parts[7] || '0') || 0,
        signal: parseInt(parts[8] || '0') || 0,
        encryption: parts[9] || 'Unknown',
      };
    }).filter(n => n.ssid);
  } catch {
    try {
      const output = cp.execSync('iwlist scan 2>/dev/null | grep -E "ESSID|Address|Frequency|Quality|Encryption"',
        { encoding: 'utf8', timeout: 15000 });
      const networks: WiFiNetwork[] = [];
      const lines = output.split('\n');
      let current: Partial<WiFiNetwork> = {};
      for (const line of lines) {
        if (line.includes('Address:')) {
          if (current.ssid) networks.push(current as WiFiNetwork);
          current = { bssid: line.split('Address:')[1]?.trim() || '' };
        } else if (line.includes('ESSID:')) {
          current.ssid = line.split('ESSID:"')[1]?.replace('"', '').trim() || '';
        } else if (line.includes('Frequency:')) {
          const ch = line.match(/Channel (\d+)/)?.[1];
          current.channel = parseInt(ch || '0') || 0;
        } else if (line.includes('Quality=')) {
          const q = line.match(/Quality=(\d+)/)?.[1];
          current.signal = parseInt(q || '0') || 0;
        } else if (line.includes('Encryption key:')) {
          current.encryption = line.includes('on') ? 'WPA' : 'Open';
        }
      }
      if (current.ssid) networks.push(current as WiFiNetwork);
      return networks;
    } catch {
      return [];
    }
  }
}

// ── SSL/TLS certificate analysis ──────────────────────────────────────────────

export interface SSLInfo {
  host: string;
  valid: boolean;
  subject: string;
  issuer: string;
  validFrom: string;
  validTo: string;
  daysRemaining: number;
  protocol: string;
  warnings: string[];
}

export function checkSSL(host: string, port = 443): SSLInfo {
  const warnings: string[] = [];
  try {
    const output = cp.execSync(
      `echo | openssl s_client -connect ${host}:${port} -servername ${host} 2>/dev/null | openssl x509 -noout -dates -subject -issuer`,
      { encoding: 'utf8', timeout: 15000 }
    );
    const notBefore = output.match(/notBefore=(.*)/)?.[1]?.trim() || '';
    const notAfter = output.match(/notAfter=(.*)/)?.[1]?.trim() || '';
    const subject = output.match(/subject=(.*)/)?.[1]?.trim() || '';
    const issuer = output.match(/issuer=(.*)/)?.[1]?.trim() || '';

    const expiry = new Date(notAfter);
    const now = new Date();
    const daysRemaining = Math.floor((expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    if (daysRemaining < 0) warnings.push('Certificate has EXPIRED');
    else if (daysRemaining < 30) warnings.push(`Certificate expires in ${daysRemaining} days`);

    return { host, valid: daysRemaining > 0, subject, issuer, validFrom: notBefore, validTo: notAfter, daysRemaining, protocol: 'TLS', warnings };
  } catch {
    return { host, valid: false, subject: '', issuer: '', validFrom: '', validTo: '', daysRemaining: -1, protocol: 'Unknown', warnings: ['Could not connect or retrieve certificate'] };
  }
}

// ── Subdomain enumeration ─────────────────────────────────────────────────────

export async function enumerateSubdomains(
  domain: string,
  authorized: boolean,
  wordlist?: string[]
): Promise<string[]> {
  if (!authorized) throw new Error('Authorization required.');
  const subs = wordlist || ['www', 'api', 'mail', 'admin', 'dev', 'staging', 'test',
    'app', 'portal', 'dashboard', 'cdn', 'static', 'images', 'blog', 'shop'];
  const found: string[] = [];
  for (const sub of subs) {
    const host = `${sub}.${domain}`;
    try {
      cp.execSync(`host ${host} 2>/dev/null`, { timeout: 3000 });
      found.push(host);
    } catch { /* not found */ }
  }
  return found;
}

// ── Responder-style credential capture (for authorized lab setups) ──────────────

export function generateResponderConfig(interface_: string, authorized: boolean): string {
  if (!authorized) throw new Error('Authorization required for Responder configuration.');
  const responderDir = path.join(DEVIN_ROOT, 'external/Responder');
  return `# Responder Configuration (for authorized penetration testing only)
# Run: python3 ${responderDir}/Responder.py -I ${interface_} -rdwv
# This will capture NTLMv2 hashes on the local network segment.
# ONLY use this on networks you own or have explicit written authorization to test.
Interface: ${interface_}
Responder Path: ${responderDir}
Capture File: ${responderDir}/logs/`;
}
