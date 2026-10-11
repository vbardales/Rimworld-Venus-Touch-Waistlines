import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtemp, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { existsSync } from 'node:fs';

// On Windows a bare 'bash' can be the WSL launcher, which cannot read C: paths: prefer Git Bash.
const gitBash = 'C:/Program Files/Git/bin/bash.exe';
const bash = process.platform === 'win32' && existsSync(gitBash) ? gitBash : 'bash';

const script = join(dirname(fileURLToPath(import.meta.url)), '..', 'scripts', 'changelog-section.sh');
const changelog = [
  '# Changelog',
  '',
  '## [1.0.2] — unreleased',
  '',
  '### Changed',
  '',
  '- one',
  '',
  '## [1.0.20] — 2026-01-01',
  '',
  '- twenty',
  '',
  '## [1.0.1] — 2026-09-22',
  '',
  '- older',
  '',
].join('\n');

async function fixture(text = changelog) {
  const file = join(await mkdtemp(join(tmpdir(), 'changelog-')), 'CHANGELOG.md');
  await writeFile(file, text);
  return file;
}

test('prints the section body without its heading or trailing blank lines', async () => {
  const out = execFileSync(bash, [script, await fixture(), '1.0.2'], { encoding: 'utf8' });
  assert.equal(out, '\n### Changed\n\n- one\n');
});

test('stops at the next heading and does not confuse 1.0.2 with 1.0.20', async () => {
  const out = execFileSync(bash, [script, await fixture(), '1.0.1'], { encoding: 'utf8' });
  assert.equal(out.trim(), '- older');
});

test('fails for an unknown version and for an empty section', async () => {
  const unknown = spawnSync(bash, [script, await fixture(), '9.9.9'], { encoding: 'utf8' });
  assert.notEqual(unknown.status, 0);
  assert.match(unknown.stderr, /no non-empty/);
  const empty = spawnSync(bash, [script, await fixture('## [1.0.2]\n\n## [1.0.1]\n- x\n'), '1.0.2'], { encoding: 'utf8' });
  assert.notEqual(empty.status, 0);
});

test('a pre-release section is found by its own name only', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'changelog-'));
  const file = join(dir, 'CHANGELOG.md');
  await writeFile(file, ['# Changelog', '', '## [1.0.6-beta.1] - 2026-09-26', '', '- the beta', '', '## [1.0.5] - 2026-09-25', '', '- stable', ''].join('\n'));
  const run = (version) => spawnSync(bash, [join(import.meta.dirname, '..', 'scripts', 'changelog-section.sh'), file, version], { encoding: 'utf8' });
  assert.equal(run('1.0.6-beta.1').stdout.trim(), '- the beta');
  assert.notEqual(run('1.0.6').status, 0, 'the stable 1.0.6 has no section yet');
  assert.notEqual(run('1.0.6-beta.10').status, 0);
});
