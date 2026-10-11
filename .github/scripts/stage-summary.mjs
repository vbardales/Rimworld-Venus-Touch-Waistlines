import { readdir, stat } from 'node:fs/promises';
import { join } from 'node:path';

export async function measure(dir) {
  let files = 0;
  let bytes = 0;
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      const sub = await measure(path);
      files += sub.files;
      bytes += sub.bytes;
    } else {
      files += 1;
      bytes += (await stat(path)).size;
    }
  }
  return { files, bytes };
}

// One line per top-level entry of the folder Steam receives, so a folder that ships (or does not)
// is visible before the approval.
export async function topLevelSummary(dir) {
  const rows = [];
  for (const entry of (await readdir(dir, { withFileTypes: true })).sort((a, b) => a.name.localeCompare(b.name))) {
    if (entry.isDirectory()) {
      const { files, bytes } = await measure(join(dir, entry.name));
      rows.push({ name: `${entry.name}/`, files, bytes });
    } else {
      rows.push({ name: entry.name, files: 1, bytes: (await stat(join(dir, entry.name))).size });
    }
  }
  return rows;
}

export function formatSummary(rows) {
  return rows.map(({ name, files, bytes }) => `  ${name.padEnd(28)} ${String(files).padStart(5)} file${files === 1 ? ' ' : 's'} ${(bytes / 1e6).toFixed(2).padStart(7)} MB`).join('\n');
}
