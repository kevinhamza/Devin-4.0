// src/agents/research.ts — Deep research agent
// Ported from cheetahclaws/tools/research.py: multi-source web research pipeline
// Returns markdown-formatted research briefs with cross-platform attention

import { httpFetch, duckDuckGoSearch, SearchResult } from '../tools/web_tool.js';

export interface ResearchResult {
  source: string;
  url: string;
  title: string;
  content: string;
  timestamp: number;
}

export interface ResearchBrief {
  topic: string;
  results: ResearchResult[];
  synthesis: string;
  durationMs: number;
  cacheHits: number;
  sources: number;
}

// Simple in-memory cache
const researchCache = new Map<string, { brief: ResearchBrief; ts: number }>();
const CACHE_TTL_MS = 30 * 60 * 1000; // 30 minutes

// ── URL fetching with content extraction ──────────────────────────────────────

async function fetchPageContent(url: string, maxChars = 5000): Promise<string> {
  try {
    const result = await httpFetch(url, { timeoutMs: 15000 });
    if (result.isHtml) {
      return result.text.slice(0, maxChars);
    }
    return result.text.slice(0, maxChars);
  } catch {
    return '';
  }
}

// ── Research pipeline (from cheetahclaws/tools/research.py) ──────────────────

export async function runResearch(options: {
  topic: string;
  limit?: number;
  synthesize?: boolean;
  useCache?: boolean;
  domains?: string[];
  fetchContent?: boolean;
}): Promise<ResearchBrief> {
  const { topic, limit = 8, synthesize = true, useCache = true, fetchContent = false } = options;
  const start = Date.now();

  // Check cache
  const cacheKey = `${topic}_${limit}`;
  if (useCache && researchCache.has(cacheKey)) {
    const cached = researchCache.get(cacheKey)!;
    if (Date.now() - cached.ts < CACHE_TTL_MS) {
      return { ...cached.brief, cacheHits: 1 };
    }
  }

  // Web search
  const searchResults = await duckDuckGoSearch(topic, limit);
  const results: ResearchResult[] = [];

  // Optionally fetch page content
  for (const sr of searchResults) {
    const content = fetchContent ? await fetchPageContent(sr.url) : sr.snippet;
    results.push({
      source: 'web',
      url: sr.url,
      title: sr.title,
      content: content || sr.snippet,
      timestamp: Date.now(),
    });
  }

  const durationMs = Date.now() - start;

  let synthText = '';
  if (synthesize && results.length > 0) {
    synthText = buildSynthesis(topic, results);
  }

  const brief: ResearchBrief = {
    topic,
    results,
    synthesis: synthText,
    durationMs,
    cacheHits: 0,
    sources: results.length,
  };

  // Cache result
  if (useCache) {
    researchCache.set(cacheKey, { brief, ts: Date.now() });
  }

  return brief;
}

function buildSynthesis(topic: string, results: ResearchResult[]): string {
  const lines: string[] = [];
  lines.push(`## Research: ${topic}`);
  lines.push('');
  lines.push(`_${results.length} results from web search_`);
  lines.push('');
  lines.push('### Top Sources');
  lines.push('');
  for (const r of results.slice(0, 5)) {
    lines.push(`**${r.title || r.url}**`);
    if (r.content) lines.push(r.content.slice(0, 300));
    lines.push(`→ ${r.url}`);
    lines.push('');
  }
  if (results.length > 5) {
    lines.push(`_...and ${results.length - 5} more sources_`);
  }
  return lines.join('\n');
}

export function formatResearchBrief(brief: ResearchBrief): string {
  if (brief.synthesis) return brief.synthesis;
  if (brief.results.length === 0) return `No results found for: ${brief.topic}`;

  const lines = [
    `## Research: ${brief.topic}`,
    '',
    `*${brief.sources} sources · ${brief.durationMs}ms${brief.cacheHits > 0 ? ' · cached' : ''}*`,
    '',
  ];

  for (const r of brief.results.slice(0, 8)) {
    lines.push(`**${r.title}**`);
    if (r.content) lines.push(r.content.slice(0, 200));
    lines.push(r.url);
    lines.push('');
  }

  return lines.join('\n');
}
