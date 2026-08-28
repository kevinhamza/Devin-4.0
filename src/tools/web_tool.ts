// src/tools/web_tool.ts — Web fetch and search implementation
// Ported from cheetahclaws/tools/web.py: HTML extraction, DuckDuckGo search
// Used directly by executor.ts for web_fetch and web_search tools

import * as https from 'https';
import * as http from 'http';
import * as zlib from 'zlib';

const DEFAULT_MAX_BYTES = 512 * 1024;
const DEFAULT_TIMEOUT_MS = 30000;

// ── HTML text extractor (from cheetahclaws/tools/web.py) ─────────────────────

const VOID_ELEMENTS = new Set([
  'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
  'link', 'meta', 'param', 'source', 'track', 'wbr',
]);

const SKIP_TAGS = new Set(['script', 'style', 'noscript', 'template', 'head', 'svg', 'iframe']);

export function extractTextFromHTML(html: string, maxChars = 20000): string {
  const text: string[] = [];
  let chars = 0;
  let inSkipped = 0;
  let i = 0;

  while (i < html.length && chars < maxChars) {
    if (html[i] === '<') {
      const end = html.indexOf('>', i);
      if (end === -1) break;
      const tag = html.slice(i + 1, end);
      const isClose = tag.startsWith('/');
      const tagName = (isClose ? tag.slice(1) : tag.split(/[\s/]/)[0]).toLowerCase();

      if (SKIP_TAGS.has(tagName)) {
        if (!isClose) inSkipped++;
        else inSkipped = Math.max(0, inSkipped - 1);
      }
      i = end + 1;
    } else if (!inSkipped) {
      // Collect text
      let j = html.indexOf('<', i);
      if (j === -1) j = html.length;
      const chunk = html.slice(i, j)
        .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&nbsp;/g, ' ')
        .replace(/\s+/g, ' ').trim();
      if (chunk) {
        const remaining = maxChars - chars;
        const part = chunk.slice(0, remaining);
        text.push(part);
        chars += part.length;
      }
      i = j;
    } else {
      i++;
    }
  }

  return text.join(' ').replace(/\s{2,}/g, ' ').trim();
}

// ── HTTP fetch (from cheetahclaws/tools/web.py) ──────────────────────────────

export interface FetchResult {
  status: number;
  url: string;
  contentType: string;
  text: string;
  isHtml: boolean;
}

export function httpFetch(
  url: string,
  options: {
    method?: string;
    headers?: Record<string, string>;
    body?: string;
    maxBytes?: number;
    timeoutMs?: number;
    followRedirects?: number;
  } = {}
): Promise<FetchResult> {
  const maxBytes = options.maxBytes ?? DEFAULT_MAX_BYTES;
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const maxRedirects = options.followRedirects ?? 5;

  return new Promise((resolve, reject) => {
    let redirectCount = 0;

    function doRequest(reqUrl: string): void {
      const parsedUrl = new URL(reqUrl);
      const isHttps = parsedUrl.protocol === 'https:';
      const lib = isHttps ? https : http;

      const reqOptions: http.RequestOptions = {
        hostname: parsedUrl.hostname,
        port: parsedUrl.port || (isHttps ? 443 : 80),
        path: parsedUrl.pathname + parsedUrl.search,
        method: options.method || 'GET',
        headers: {
          'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) DevinAGI/4.0',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'Accept-Encoding': 'gzip, deflate',
          'Accept-Language': 'en-US,en;q=0.9',
          ...options.headers,
        },
      };

      const req = lib.request(reqOptions, (res) => {
        const status = res.statusCode ?? 0;

        if ([301, 302, 303, 307, 308].includes(status) && res.headers.location && redirectCount < maxRedirects) {
          redirectCount++;
          const nextUrl = res.headers.location.startsWith('http')
            ? res.headers.location
            : new URL(res.headers.location, reqUrl).toString();
          res.resume();
          doRequest(nextUrl);
          return;
        }

        const chunks: Buffer[] = [];
        let totalBytes = 0;

        const encoding = res.headers['content-encoding'];
        const stream: NodeJS.ReadableStream = (encoding === 'gzip')
          ? (res.pipe(zlib.createGunzip()) as NodeJS.ReadableStream)
          : (encoding === 'deflate')
          ? (res.pipe(zlib.createInflate()) as NodeJS.ReadableStream)
          : res;

        stream.on('data', (chunk: Buffer) => {
          totalBytes += chunk.length;
          if (totalBytes <= maxBytes) chunks.push(chunk);
        });
        stream.on('end', () => {
          const raw = Buffer.concat(chunks).toString('utf8');
          const contentType = String(res.headers['content-type'] || '');
          const isHtml = contentType.includes('html');
          const text = isHtml ? extractTextFromHTML(raw) : raw.slice(0, maxBytes);
          resolve({ status, url: reqUrl, contentType, text, isHtml });
        });
        stream.on('error', reject);
      });

      req.setTimeout(timeoutMs, () => { req.destroy(new Error(`Timeout after ${timeoutMs}ms`)); });
      req.on('error', reject);

      if (options.body) req.write(options.body);
      req.end();
    }

    doRequest(url);
  });
}

// ── DuckDuckGo search (from cheetahclaws/tools/web.py) ───────────────────────

export interface SearchResult {
  title: string;
  url: string;
  snippet: string;
}

export async function duckDuckGoSearch(query: string, maxResults = 8): Promise<SearchResult[]> {
  const encodedQuery = encodeURIComponent(query);
  const url = `https://lite.duckduckgo.com/lite/?q=${encodedQuery}`;

  try {
    const result = await httpFetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) DevinAGI/4.0',
        'Accept': 'text/html',
      },
    });

    // Parse DuckDuckGo lite results
    const results: SearchResult[] = [];
    const html = result.text;

    // Extract result links and snippets using simple pattern matching
    const linkPattern = /href="(https?:\/\/[^"]+)"[^>]*>([^<]+)<\/a>/g;
    const snippetPattern = /<td[^>]*class="result-snippet"[^>]*>([^<]+(?:<[^>]+>[^<]*<\/[^>]+>[^<]*)*)<\/td>/g;

    const links: Array<{ url: string; title: string }> = [];
    let m: RegExpExecArray | null;

    while ((m = linkPattern.exec(html)) !== null && links.length < maxResults * 2) {
      const href = m[1];
      const title = m[2].trim();
      if (href && title && !href.includes('duckduckgo.com') && !href.includes('javascript:')) {
        links.push({ url: href, title });
      }
    }

    const snippets: string[] = [];
    while ((m = snippetPattern.exec(html)) !== null) {
      snippets.push(extractTextFromHTML(m[1], 300));
    }

    for (let i = 0; i < Math.min(links.length, maxResults); i++) {
      results.push({
        title: links[i].title,
        url: links[i].url,
        snippet: snippets[i] || '',
      });
    }

    // Fallback: try to extract any URLs if no structured results
    if (results.length === 0) {
      const urlPattern = /https?:\/\/(?!.*duckduckgo)[^\s"'>)]+/g;
      const seenUrls = new Set<string>();
      while ((m = urlPattern.exec(html)) !== null && results.length < maxResults) {
        const u = m[0].replace(/[.,;)]+$/, '');
        if (!seenUrls.has(u)) {
          seenUrls.add(u);
          results.push({ title: u, url: u, snippet: '' });
        }
      }
    }

    return results;
  } catch (e) {
    return [{ title: 'Search failed', url: url, snippet: String(e) }];
  }
}

export function formatSearchResults(results: SearchResult[]): string {
  if (results.length === 0) return 'No results found.';
  return results.map((r, i) =>
    `${i + 1}. ${r.title}\n   ${r.url}${r.snippet ? '\n   ' + r.snippet : ''}`
  ).join('\n\n');
}
