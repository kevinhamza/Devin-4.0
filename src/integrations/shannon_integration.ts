// src/integrations/shannon_integration.ts — Shannon AI security assistant integration
// Shannon is a security-focused AI tool for network analysis and threat intelligence
// Provides threat analysis, network monitoring, and security event processing

import * as cp from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import { httpFetch } from '../tools/web_tool.js';

const DEVIN_ROOT = path.join(__dirname, '../..');

// ── Threat intelligence (Shannon security pattern) ────────────────────────────

export interface ThreatIndicator {
  type: 'ip' | 'domain' | 'hash' | 'url' | 'email';
  value: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'unknown';
  confidence: number;
  tags: string[];
  lastSeen?: string;
  source: string;
}

export interface ThreatAnalysisResult {
  indicator: string;
  isMalicious: boolean;
  reputation: number;
  findings: string[];
  recommendations: string[];
  sources: string[];
}

// ── IP reputation check ────────────────────────────────────────────────────────

export async function checkIPReputation(ip: string): Promise<ThreatAnalysisResult> {
  const findings: string[] = [];
  const sources: string[] = [];

  // Basic validation
  const ipv4 = /^(?:\d{1,3}\.){3}\d{1,3}$/.test(ip);
  const ipv6 = /^[0-9a-fA-F:]+$/.test(ip);
  if (!ipv4 && !ipv6) {
    return { indicator: ip, isMalicious: false, reputation: 0, findings: ['Invalid IP format'], recommendations: [], sources: [] };
  }

  // Check AbuseIPDB
  try {
    const res = await httpFetch(
      `https://api.abuseipdb.com/api/v2/check?ipAddress=${ip}&maxAgeInDays=90`,
      {
        timeoutMs: 8000,
        headers: { 'Key': process.env.ABUSEIPDB_API_KEY || '', 'Accept': 'application/json' }
      }
    );
    const data = JSON.parse(res.text);
    if (res.status === 200 && data?.data) {
      const abuseScore = data.data.abuseConfidenceScore || 0;
      findings.push(`AbuseIPDB confidence score: ${abuseScore}/100`);
      if (data.data.totalReports) findings.push(`Total reports: ${data.data.totalReports}`);
      if (data.data.countryCode) findings.push(`Country: ${data.data.countryCode}`);
      sources.push('AbuseIPDB');
      if (abuseScore > 50) {
        return {
          indicator: ip, isMalicious: true, reputation: abuseScore,
          findings, recommendations: ['Block this IP', 'Check firewall rules'], sources
        };
      }
    }
  } catch { /* API key not configured */ }

  // Reverse DNS lookup
  try {
    const rdns = cp.execSync(`host ${ip} 2>/dev/null`, { encoding: 'utf8', timeout: 5000 }).trim();
    if (rdns && !rdns.includes('not found')) {
      findings.push(`Reverse DNS: ${rdns.split('\n')[0]}`);
    }
  } catch { /* no reverse DNS */ }

  // Check if IP is in known TOR exit nodes (via local check)
  const isTor = await checkTorExit(ip);
  if (isTor) {
    findings.push('IP is a known TOR exit node');
    return {
      indicator: ip, isMalicious: true, reputation: 60,
      findings, recommendations: ['Consider blocking TOR exit nodes', 'Investigate traffic from this IP'],
      sources: [...sources, 'TOR Exit List']
    };
  }

  return {
    indicator: ip, isMalicious: false, reputation: 0,
    findings: findings.length ? findings : ['No threat indicators found'],
    recommendations: ['Continue monitoring'], sources
  };
}

async function checkTorExit(ip: string): Promise<boolean> {
  try {
    const res = await httpFetch(
      `https://check.torproject.org/torbulkexitlist`,
      { timeoutMs: 10000 }
    );
    return res.text.split('\n').includes(ip);
  } catch {
    return false;
  }
}

// ── Domain analysis ───────────────────────────────────────────────────────────

export async function analyzeDomain(domain: string): Promise<ThreatAnalysisResult> {
  const findings: string[] = [];
  const sources: string[] = [];

  // WHOIS lookup
  try {
    const whois = cp.execSync(`whois "${domain}" 2>/dev/null | head -30`, {
      encoding: 'utf8', timeout: 10000
    }).trim();
    if (whois) {
      const creation = whois.match(/Creation Date:\s*(.+)/i)?.[1]?.trim();
      const expiry = whois.match(/Expir(?:y|ation) Date:\s*(.+)/i)?.[1]?.trim();
      if (creation) findings.push(`Created: ${creation}`);
      if (expiry) findings.push(`Expires: ${expiry}`);
      sources.push('WHOIS');

      // Newly registered domains (< 30 days) are suspicious
      if (creation) {
        const createdDate = new Date(creation);
        const daysSinceCreation = (Date.now() - createdDate.getTime()) / (1000 * 60 * 60 * 24);
        if (daysSinceCreation < 30) {
          findings.push(`WARNING: Domain registered only ${Math.round(daysSinceCreation)} days ago`);
        }
      }
    }
  } catch { /* whois not available */ }

  // DNS resolution
  try {
    const dns = cp.execSync(`dig +short "${domain}" A 2>/dev/null`, {
      encoding: 'utf8', timeout: 5000
    }).trim();
    if (dns) findings.push(`DNS A records: ${dns}`);
  } catch { /* dig not available */ }

  // Check phishing patterns
  const phishingPatterns = [
    /paypa1|paypai|paypa-l/i, /apple-support|apple-security/i,
    /microsoft-security|windows-support/i, /amazon-prime|amazon-account/i,
    /banking-security|bank-verify/i, /account-verify|secure-login/i,
  ];
  const isPhishing = phishingPatterns.some(p => p.test(domain));
  if (isPhishing) {
    findings.push('Domain matches known phishing patterns');
    return {
      indicator: domain, isMalicious: true, reputation: 80,
      findings, recommendations: ['Block this domain immediately', 'Report to anti-phishing organizations'],
      sources
    };
  }

  return {
    indicator: domain, isMalicious: false, reputation: 0,
    findings: findings.length ? findings : ['No threat indicators found'],
    recommendations: ['Continue monitoring'], sources
  };
}

// ── File hash analysis ────────────────────────────────────────────────────────

export async function analyzeFileHash(
  hash: string,
  type: 'md5' | 'sha1' | 'sha256' = 'sha256'
): Promise<ThreatAnalysisResult> {
  const findings: string[] = [];

  // VirusTotal (public API, no key needed for basic lookup)
  try {
    const res = await httpFetch(
      `https://www.virustotal.com/api/v3/files/${hash}`,
      {
        timeoutMs: 10000,
        headers: { 'x-apikey': process.env.VT_API_KEY || '' }
      }
    );
    if (res.status === 200) {
      const data = JSON.parse(res.text);
      const stats = data?.data?.attributes?.last_analysis_stats || {};
      const malicious = stats.malicious || 0;
      const total = (stats.malicious || 0) + (stats.undetected || 0) + (stats.harmless || 0);
      findings.push(`VirusTotal: ${malicious}/${total} detections`);
      if (malicious > 0) {
        return {
          indicator: hash, isMalicious: true, reputation: Math.round((malicious / total) * 100),
          findings, recommendations: ['Quarantine this file', 'Do not execute'],
          sources: ['VirusTotal']
        };
      }
    }
  } catch { /* API key not configured */ }

  // Calculate hash from common malware indicators (offline check)
  const knownMalwareHashes = new Set([
    'd41d8cd98f00b204e9800998ecf8427e', // empty file (test)
  ]);
  if (knownMalwareHashes.has(hash.toLowerCase())) {
    findings.push('Hash matches known malware signature');
    return { indicator: hash, isMalicious: true, reputation: 100, findings, recommendations: ['Quarantine immediately'], sources: ['Local DB'] };
  }

  return { indicator: hash, isMalicious: false, reputation: 0, findings: ['Hash not found in threat databases'], recommendations: [], sources: [] };
}

// ── Network packet analyzer ────────────────────────────────────────────────────

export function captureNetworkTraffic(
  interface_: string,
  durationSecs: number,
  authorized: boolean,
  filter?: string
): string {
  if (!authorized) throw new Error('Authorization required for network traffic capture.');
  const outFile = `/tmp/devin_capture_${Date.now()}.pcap`;
  try {
    const filterStr = filter ? `"${filter}"` : '';
    cp.execSync(
      `timeout ${durationSecs} tcpdump -i ${interface_} -w ${outFile} ${filterStr} 2>/dev/null || true`,
      { timeout: (durationSecs + 5) * 1000 }
    );
    const stats = cp.execSync(`tcpdump -r ${outFile} -nn 2>/dev/null | wc -l`, { encoding: 'utf8' }).trim();
    return `Capture complete: ${outFile}\nPackets captured: ${stats}`;
  } catch (e) {
    return `Capture failed: ${String(e).slice(0, 200)}`;
  }
}

// ── OSINT gathering ───────────────────────────────────────────────────────────

export interface OSINTResult {
  target: string;
  type: string;
  findings: Array<{ source: string; data: string }>;
}

export async function gatherOSINT(
  target: string,
  type: 'person' | 'company' | 'domain' | 'username'
): Promise<OSINTResult> {
  const findings: Array<{ source: string; data: string }> = [];

  if (type === 'domain') {
    // Shodan-style host discovery (using free alternatives)
    try {
      const cert = cp.execSync(`echo | openssl s_client -connect ${target}:443 -servername ${target} 2>/dev/null | openssl x509 -noout -text 2>/dev/null | head -20`,
        { encoding: 'utf8', timeout: 10000 }).trim();
      if (cert) findings.push({ source: 'TLS Certificate', data: cert.slice(0, 500) });
    } catch { /* skip */ }
  }

  if (type === 'username') {
    const platforms = ['github.com', 'twitter.com', 'reddit.com', 'gitlab.com'];
    for (const platform of platforms) {
      try {
        const url = `https://${platform}/${target}`;
        const res = await httpFetch(url, { timeoutMs: 5000 });
        if (res.status === 200) {
          findings.push({ source: platform, data: `Profile found: ${url}` });
        }
      } catch { /* not found */ }
    }
  }

  return { target, type, findings };
}

// ── Security event logger ─────────────────────────────────────────────────────

export interface SecurityEvent {
  timestamp: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  type: string;
  description: string;
  source: string;
  indicators: string[];
}

const securityLog: SecurityEvent[] = [];

export function logSecurityEvent(event: Omit<SecurityEvent, 'timestamp'>): void {
  const fullEvent: SecurityEvent = { ...event, timestamp: new Date().toISOString() };
  securityLog.push(fullEvent);
  const logFile = path.join(DEVIN_ROOT, 'logs', 'security_events.json');
  fs.mkdirSync(path.dirname(logFile), { recursive: true });
  fs.appendFileSync(logFile, JSON.stringify(fullEvent) + '\n', 'utf8');
}

export function getSecurityEvents(
  severity?: SecurityEvent['severity'],
  limit = 100
): SecurityEvent[] {
  let events = [...securityLog];
  if (severity) events = events.filter(e => e.severity === severity);
  return events.slice(-limit);
}
