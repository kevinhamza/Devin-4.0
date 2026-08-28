// src/integrations/index.ts — Registry of all external repo integrations

import * as path from 'path';
import * as fs from 'fs';
import { PROJECT_ROOT } from '../config.js';

export interface RepoInfo {
  name: string;
  path: string;
  available: boolean;
  description: string;
  usedFor: string;
}

export function getIntegratedRepos(): RepoInfo[] {
  const extDir = path.join(PROJECT_ROOT, 'external');

  const repos: Array<Omit<RepoInfo, 'available'>> = [
    { name: 'gemini-cli',          path: 'external/gemini-cli',          description: 'Google Gemini CLI',                        usedFor: 'Gemini provider, delegate_to_gemini_cli' },
    { name: 'claude-code',         path: 'external/claude-code',         description: 'Anthropic Claude Code CLI source',         usedFor: 'TypeScript CLI architecture reference' },
    { name: 'claude-code-source',  path: 'external/claude-code-source',  description: 'Claude Code source collection',            usedFor: 'Pattern reference for src/ layer' },
    { name: 'cheetahclaws',        path: 'external/cheetahclaws',        description: 'Python-native AI assistant (SafeRL-Lab)',   usedFor: 'AgentState, streaming, compaction patterns' },
    { name: 'openclaw',            path: 'external/openclaw',            description: 'Multi-channel messaging',                  usedFor: 'MessagingGateway (Telegram/Discord/Slack)' },
    { name: 'AIA',                 path: 'external/AIA',                 description: 'AI Assistant (kevinhamza)',                usedFor: 'Social media, device control, face recognition' },
    { name: 'Devin',               path: 'external/Devin',               description: 'Devin v1',                                 usedFor: 'v1 feature parity (merged into modules/)' },
    { name: 'Devin-2.0',           path: 'external/Devin-2.0',           description: 'Devin v2',                                 usedFor: 'v2 feature parity (merged into modules/)' },
    { name: 'Devin-3.0',           path: 'external/Devin-3.0',           description: 'Devin v3',                                 usedFor: 'v3 feature parity (merged into modules/)' },
    { name: 'shannon',             path: 'external/shannon',             description: 'KeygraphHQ Shannon',                      usedFor: 'run_shannon_pentest via ExternalAgentTools' },
    { name: 'hexstrike-ai',        path: 'hexstrike-ai',                 description: 'HexStrike AI pentesting',                  usedFor: 'HexStrikeClient — AI-driven pentesting' },
    { name: 'airgorah',            path: 'external/airgorah',            description: 'WiFi audit toolkit',                      usedFor: 'WifiAuditTools — aircrack-ng suite' },
    { name: 'metasploit-framework',path: 'external/metasploit-framework',description: 'Metasploit Framework',                    usedFor: 'run_metasploit via pymetasploit3 (auth required)' },
    { name: 'nishang',             path: 'external/nishang',             description: 'PowerShell pentesting toolkit',           usedFor: 'PowerShell payloads via execute_shell' },
    { name: 'Responder',           path: 'external/Responder',           description: 'Network responder',                       usedFor: 'LLMNR/NBT-NS poisoning (auth only)' },
    { name: 'PowerTools',          path: 'external/PowerTools',          description: 'Windows PowerShell toolkit',              usedFor: 'Windows privilege escalation reference' },
    { name: 'hackability',         path: 'external/hackability',         description: 'Burp Suite extension',                    usedFor: 'Web app security testing reference' },
    { name: 'vulnerability-analysis', path: 'external/vulnerability-analysis', description: 'CVE scanning pipeline',            usedFor: 'Docker-based vulnerability scanning' },
    { name: 'moltbots.github.io',  path: 'external/moltbots.github.io',  description: 'MoltBots site',                           usedFor: 'Static site reference' },
    { name: 'Holomat',             path: 'external/Holomat',             description: 'Holographic/spatial computing',           usedFor: 'HolomatBridge — spatial display interface' },
    { name: 'Jarvis',              path: 'external/Jarvis',              description: 'Concept-Bytes Jarvis',                    usedFor: 'JarvisBridge — voice assistant skills' },
    { name: 'JARVIS-microsoft',    path: 'external/JARVIS-microsoft',    description: 'Microsoft HuggingGPT/JARVIS',             usedFor: 'Multi-model orchestration patterns' },
    { name: 'OpenDevin',           path: 'external/OpenDevin',           description: 'OpenHands/OpenDevin',                     usedFor: 'OpenDevinBridge — sandboxed execution, web browsing' },
    { name: 'self-operating-computer', path: 'self-operating-computer',  description: 'Self-operating computer',                 usedFor: 'operate_computer tool via PyAutoGUI + vision' },
  ];

  return repos.map(r => ({
    ...r,
    available: fs.existsSync(path.join(PROJECT_ROOT, r.path)) &&
      fs.readdirSync(path.join(PROJECT_ROOT, r.path)).length > 1,
  }));
}

export function printIntegrationStatus(): void {
  const repos = getIntegratedRepos();
  const ready = repos.filter(r => r.available).length;
  console.log(`\nIntegrated repos: ${ready}/${repos.length} ready\n`);
  for (const r of repos) {
    const status = r.available ? '\x1b[32m✓\x1b[0m' : '\x1b[33m○\x1b[0m';
    const name = r.name.padEnd(30);
    console.log(`  ${status} \x1b[36m${name}\x1b[0m \x1b[90m${r.usedFor.slice(0, 50)}\x1b[0m`);
  }
  console.log();
}
