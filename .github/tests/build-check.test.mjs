import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { chmod, mkdir, mkdtemp, readFile, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { delimiter, join } from 'node:path';
import { existsSync } from 'node:fs';

// On Windows a bare 'bash' can be the WSL launcher, which cannot read C: paths: prefer Git Bash.
const gitBash = 'C:/Program Files/Git/bin/bash.exe';
const bash = process.platform === 'win32' && existsSync(gitBash) ? gitBash : 'bash';

const script = join(import.meta.dirname, '..', 'scripts', 'build-check.sh');
const git = (cwd, ...args) => spawnSync('git', ['-c', 'user.name=t', '-c', 'user.email=t@t', ...args], { cwd, encoding: 'utf8' });

// A repository with a tracked Mod/Assemblies/X.dll, and a stub `dotnet` that writes what STUB_DLL says over it, or fails.
async function setup({ build, requirePaths }) {
  const cwd = await mkdtemp(join(tmpdir(), 'buildcheck-'));
  await mkdir(join(cwd, '.github'), { recursive: true });
  await mkdir(join(cwd, 'Mod', 'Assemblies'), { recursive: true });
  await mkdir(join(cwd, 'Source'), { recursive: true });
  await writeFile(join(cwd, '.github', 'publish.config.json'), JSON.stringify({ ...(build ? { build } : {}), ...(requirePaths ? { requirePaths } : {}) }));
  await writeFile(join(cwd, 'Mod', 'Assemblies', 'X.dll'), 'committed');
  await writeFile(join(cwd, 'Source', 'X.csproj'), '<Project/>');
  git(cwd, 'init', '-q', '--initial-branch=main'); git(cwd, 'add', '.'); git(cwd, 'commit', '-q', '-m', 'one');
  const bin = await mkdtemp(join(tmpdir(), 'dotnet-'));
  await writeFile(join(bin, 'dotnet'), '#!/usr/bin/env bash\n[[ "${STUB_FAIL:-}" != 1 ]] || { echo "error CS1002" >&2; exit 1; }\n[[ "${STUB_NODLL:-}" == 1 ]] || printf "%s" "${STUB_DLL:-committed}" > Mod/Assemblies/X.dll\necho "built $*" >> "$STUB_LOG"\n');
  await chmod(join(bin, 'dotnet'), 0o755);
  const log = join(bin, 'log');
  await writeFile(log, '');
  const summary = join(bin, 'summary');
  await writeFile(summary, '');
  const run = (env = {}, ...args) => spawnSync(bash, [script, ...args], { cwd, encoding: 'utf8', env: { ...process.env, PATH: `${bin}${delimiter}${process.env.PATH}`, STUB_LOG: log, GITHUB_STEP_SUMMARY: summary, ...env } });
  return { cwd, run, log, summary };
}

test('without a build project nothing is built and the tracked Mod/ ships', async () => {
  const t = await setup({});
  const r = t.run();
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /No build project/);
  assert.equal(await readFile(t.log, 'utf8'), '');
});

test('a build that reproduces the tracked files is reported as identical', async () => {
  const t = await setup({ build: { project: 'Source/X.csproj' } });
  const r = t.run();
  assert.equal(r.status, 0, r.stderr);
  assert.match(await readFile(t.log, 'utf8'), /built build Source\/X\.csproj -c Release/);
  assert.match(r.stdout, /byte for byte/);
});

test('a build that differs is reported with both hashes, and the committed file is put back', async () => {
  const t = await setup({ build: { project: 'Source/X.csproj' } });
  const r = t.run({ STUB_DLL: 'rebuilt' });
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /::warning::The runner's build differs/);
  assert.match(await readFile(t.summary, 'utf8'), /Mod\/Assemblies\/X\.dll: committed [0-9a-f]{64}, rebuilt [0-9a-f]{64}/);
  assert.equal(await readFile(join(t.cwd, 'Mod', 'Assemblies', 'X.dll'), 'utf8'), 'committed', 'what ships is what is committed');
});

test('a project that does not compile, or that is not in the commit, stops the run', async () => {
  const t = await setup({ build: { project: 'Source/X.csproj' } });
  const failed = t.run({ STUB_FAIL: '1' });
  assert.notEqual(failed.status, 0);
  const missing = await setup({ build: { project: 'Source/Other.csproj' } });
  const r = missing.run();
  assert.notEqual(r.status, 0);
  assert.match(r.stderr, /does not exist in this commit/);
});

test('--ci builds from scratch and requires every path of requirePaths', async () => {
  const t = await setup({ build: { project: 'Source/X.csproj' }, requirePaths: ['Assemblies/X.dll', 'About'] });
  await mkdir(join(t.cwd, 'Mod', 'About'), { recursive: true });
  const r = t.run({}, '--ci');
  assert.equal(r.status, 0, r.stderr);
  assert.match(await readFile(t.log, 'utf8'), /built build Source\/X\.csproj -c Release/);
  assert.match(r.stdout, /every required path exists/);
});

test('--ci deletes the committed assembly first, so a build that produces nothing cannot pass on the tracked file', async () => {
  const t = await setup({ build: { project: 'Source/X.csproj' }, requirePaths: ['Assemblies/X.dll'] });
  const r = t.run({ STUB_NODLL: '1' }, '--ci');
  assert.notEqual(r.status, 0);
  assert.match(r.stderr, /Mod\/Assemblies\/X\.dll is required \(requirePaths\) and the build did not produce it/);
});

test('--ci fails when the build does not compile, has no project, or when the argument is unknown', async () => {
  const failed = await setup({ build: { project: 'Source/X.csproj' }, requirePaths: ['Assemblies/X.dll'] });
  assert.notEqual(failed.run({ STUB_FAIL: '1' }, '--ci').status, 0);
  const none = await setup({ requirePaths: ['Assemblies/X.dll'] });
  const r = none.run({}, '--ci');
  assert.notEqual(r.status, 0);
  assert.match(r.stderr, /names no build project/);
  const bad = await setup({ build: { project: 'Source/X.csproj' } });
  const u = bad.run({}, '--wat');
  assert.equal(u.status, 2);
});
