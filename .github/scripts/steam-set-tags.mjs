import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { tagsFor } from './about.mjs';
import { loadConfig } from './config.mjs';

// Sets the Workshop tags of the item through the Steam client protocol and reads them back. steamcmd ignores the tags
// key of workshop.vdf (the 1.7 tag was dropped silently on 2026-10-12), so this runs after the upload, as its own step:
// a failure here does not undo the upload and does not stop the tag and the release from being created.
// The tags replace the page's whole set: Mod plus one tag per supportedVersions entry of About.xml.
const commitDir = process.env.TAG_DIR;
const refreshToken = process.env.STEAM_REFRESH_TOKEN;
if (!commitDir || !refreshToken) throw new Error('TAG_DIR and STEAM_REFRESH_TOKEN are required');

const config = await loadConfig(commitDir);
const tags = tagsFor(await readFile(join(commitDir, 'Mod', 'About', 'About.xml'), 'utf8'));
const { applyWorkshopTags } = await import('semantic-release-steam/lib/workshop-tags.mjs');
await applyWorkshopTags({
  steamRefreshToken: refreshToken,
  appId: 294100,
  mods: [{ name: `item ${config.workshopId}`, publishedFileId: config.workshopId, tags }],
  logger: console,
});
console.log(`tags set and read back from Steam on item ${config.workshopId}: ${tags.join(', ')}`);
process.exit(0);
