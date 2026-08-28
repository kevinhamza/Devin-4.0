#!/usr/bin/env node
/**
 * build.mjs — Best-effort build of Claude Code v2.1.88 from source
 *
 * ⚠️  IMPORTANT: A complete rebuild requires the Bun runtime's compile-time
 *     intrinsics (feature(), MACRO, bun:bundle). This script provides a
 *     best-effort build using esbuild. See KNOWN_ISSUES.md for details.
 *
 * What this script does:
 *   1. Copy src/ → build-src/ (original untouched)
 *   2. Replace `feature('X')` → `false`  (compile-time → runtime)
 *   3. Replace `MACRO.VERSION` etc → string literals
 *   4. Replace `import from 'bun:bundle'` → stub
 *   5. Create stubs for missing feature-gated modules
 *   6. Bundle with esbuild → dist/cli.js
 *
 * Requirements: Node.js >= 18, npm
 * Usage:       node scripts/build.mjs
 */

import { readdir, readFile, writeFile, mkdir, cp, rm, stat } from 'node:fs/promises'
import { join, dirname } from 'node:path'
import { execSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT = join(__dirname, '..')
const VERSION = '2.1.88'
const BUILD = join(ROOT, 'build-src')
const ENTRY = join(BUILD, 'entry.ts')

// ── Helpers ────────────────────────────────────────────────────────────────

async function* walk(dir) {
  for (const e of await readdir(dir, { withFileTypes: true })) {
    const p = join(dir, e.name)
    if (e.isDirectory() && e.name !== 'node_modules') yield* walk(p)
    else yield p
  }
}

async function exists(p) { try { await stat(p); return true } catch { return false } }

async function ensureEsbuild() {
  try { execSync('npx esbuild --version', { stdio: 'pipe' }) }
  catch {
    console.log('📦 Installing esbuild...')
    execSync('npm install --save-dev esbuild', { cwd: ROOT, stdio: 'inherit' })
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// PHASE 1: Copy source
// ══════════════════════════════════════════════════════════════════════════════

await rm(BUILD, { recursive: true, force: true })
await mkdir(BUILD, { recursive: true })
await cp(join(ROOT, 'src'), join(BUILD, 'src'), { recursive: true })
console.log('✅ Phase 1: Copied src/ → build-src/')

// ══════════════════════════════════════════════════════════════════════════════
// PHASE 2: Transform source
// ══════════════════════════════════════════════════════════════════════════════

let transformCount = 0

// MACRO replacements
const MACROS = {
  'MACRO.VERSION': `'${VERSION}'`,
  'MACRO.BUILD_TIME': `''`,
  'MACRO.FEEDBACK_CHANNEL': `'https://github.com/anthropics/claude-code/issues'`,
  'MACRO.ISSUES_EXPLAINER': `'https://github.com/anthropics/claude-code/issues/new/choose'`,
  'MACRO.FEEDBACK_CHANNEL_URL': `'https://github.com/anthropics/claude-code/issues'`,
  'MACRO.ISSUES_EXPLAINER_URL': `'https://github.com/anthropics/claude-code/issues/new/choose'`,
  'MACRO.NATIVE_PACKAGE_URL': `'@anthropic-ai/claude-code'`,
  'MACRO.PACKAGE_URL': `'@anthropic-ai/claude-code'`,
  'MACRO.VERSION_CHANGELOG': `''`,
}

for await (const file of walk(join(BUILD, 'src'))) {
  if (!file.match(/\.[tj]sx?$/)) continue

  let src = await readFile(file, 'utf8')
  let changed = false

  // 2a. feature('X') → false
  if (/\bfeature\s*\(\s*['"][A-Z_]+['"]\s*\)/.test(src)) {
    src = src.replace(/\bfeature\s*\(\s*['"][A-Z_]+['"]\s*\)/g, 'false')
    changed = true
  }

  // 2b. MACRO.X → literals
  for (const [k, v] of Object.entries(MACROS)) {
    if (src.includes(k)) {
      src = src.replaceAll(k, v)
      changed = true
    }
  }

  // 2c. Remove bun:bundle import (feature() is already replaced)
  if (src.includes("from 'bun:bundle'") || src.includes('from "bun:bundle"')) {
    src = src.replace(/import\s*\{\s*feature\s*\}\s*from\s*['"]bun:bundle['"];?\n?/g, '// feature() replaced with false at build time\n')
    changed = true
  }

  // 2d. Remove type-only import of global.d.ts
  if (src.includes("import '../global.d.ts'") || src.includes("import './global.d.ts'")) {
    src = src.replace(/import\s*['"][.\/]*global\.d\.ts['"];?\n?/g, '')
    changed = true
  }

  if (changed) {
    await writeFile(file, src, 'utf8')
    transformCount++
  }
}
console.log(`✅ Phase 2: Transformed ${transformCount} files`)

// ══════════════════════════════════════════════════════════════════════════════
// PHASE 3: Create entry wrapper
// ══════════════════════════════════════════════════════════════════════════════

await writeFile(ENTRY, `#!/usr/bin/env node
// Claude Code v${VERSION} — built from source
// Copyright (c) Anthropic PBC. All rights reserved.
import './src/entrypoints/cli.tsx'
`, 'utf8')
console.log('✅ Phase 3: Created entry wrapper')

// ══════════════════════════════════════════════════════════════════════════════
// PHASE 4: Iterative stub + bundle
// ══════════════════════════════════════════════════════════════════════════════

await ensureEsbuild()

const OUT_DIR = join(ROOT, 'dist')
await mkdir(OUT_DIR, { recursive: true })
const OUT_FILE = join(OUT_DIR, 'cli.js')

// Run up to 5 rounds of: esbuild → collect missing → create stubs → retry
const MAX_ROUNDS = 5
let succeeded = false

for (let round = 1; round <= MAX_ROUNDS; round++) {
  console.log(`\n🔨 Phase 4 round ${round}/${MAX_ROUNDS}: Bundling...`)

  let esbuildOutput = ''
  try {
    esbuildOutput = execSync([
      'npx esbuild',
      `"${ENTRY}"`,
      '--bundle',
      '--platform=node',
      '--target=node18',
      '--format=esm',
      `--outfile="${OUT_FILE}"`,
      `--banner:js=$'#!/usr/bin/env node\\n// Claude Code v${VERSION} (built from source)\\n// Copyright (c) Anthropic PBC. All rights reserved.\\n'`,
      '--packages=external',
      '--external:bun:*',
      '--allow-overwrite',
      '--log-level=error',
      '--log-limit=0',
      '--sourcemap',
    ].join(' '), {
      cwd: ROOT,
      stdio: ['pipe', 'pipe', 'pipe'],
      shell: true,
    }).stderr?.toString() || ''
    succeeded = true
    break
  } catch (e) {
    esbuildOutput = (e.stderr?.toString() || '') + (e.stdout?.toString() || '')
  }

  // Parse missing modules
  const missingRe = /Could not resolve "([^"]+)"/g
  const missing = new Set()
  let m
  while ((m = missingRe.exec(esbuildOutput)) !== null) {
    const mod = m[1]
    if (!mod.startsWith('node:') && !mod.startsWith('bun:') && !mod.startsWith('/')) {
      missing.add(mod)
    }
  }

  if (missing.size === 0) {
    // No more missing modules but still errors — check what
    const errLines = esbuildOutput.split('\n').filter(l => l.includes('ERROR')).slice(0, 5)
    console.log('❌ Unrecoverable errors:')
    errLines.forEach(l => console.log('   ' + l))
    break
  }

  console.log(`   Found ${missing.size} missing modules, creating stubs...`)

  // Create stubs
  let stubCount = 0
  for (const mod of missing) {
    // Resolve relative path from the file that imports it — but since we
    // don't have that info easily, create stubs at multiple likely locations
    const cleanMod = mod.replace(/^\.\//, '')

    // Text assets → empty file
    if (/\.(txt|md|json)$/.test(cleanMod)) {
      const p = join(BUILD, 'src', cleanMod)
      await mkdir(dirname(p), { recursive: true }).catch(() => {})
      if (!await exists(p)) {
        await writeFile(p, cleanMod.endsWith('.json') ? '{}' : '', 'utf8')
        stubCount++
      }
      continue
    }

    // JS/TS modules → export empty
    if (/\.[tj]sx?$/.test(cleanMod)) {
      for (const base of [join(BUILD, 'src'), join(BUILD, 'src', 'src')]) {
        const p = join(base, cleanMod)
        await mkdir(dirname(p), { recursive: true }).catch(() => {})
        if (!await exists(p)) {
          const name = cleanMod.split('/').pop().replace(/\.[tj]sx?$/, '')
          const safeName = name.replace(/[^a-zA-Z0-9_$]/g, '_') || 'stub'
          await writeFile(p, `// Auto-generated stub\nexport default function ${safeName}() {}\nexport const ${safeName} = () => {}\n`, 'utf8')
          stubCount++
        }
      }
    }
  }
  console.log(`   Created ${stubCount} stubs`)
}

if (succeeded) {
  const size = (await stat(OUT_FILE)).size
  console.log(`\n✅ Build succeeded: ${OUT_FILE}`)
  console.log(`   Size: ${(size / 1024 / 1024).toFixed(1)}MB`)
  console.log(`\n   Usage:  node ${OUT_FILE} --version`)
  console.log(`           node ${OUT_FILE} -p "Hello"`)
} else {
  console.error('\n❌ Build failed after all rounds.')
  console.error('   The transformed source is in build-src/ for inspection.')
  console.error('\n   To fix manually:')
  console.error('   1. Check build-src/ for the transformed files')
  console.error('   2. Create missing stubs in build-src/src/')
  console.error('   3. Re-run: node scripts/build.mjs')
  process.exit(1)
}
