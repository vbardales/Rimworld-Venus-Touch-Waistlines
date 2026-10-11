import { mkdtemp, readFile, readdir, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { aboutName, tagsFor } from './about.mjs';
import { aboutProblem, descriptionMarkdown } from './about-description.mjs';
import { changenoteFor, fencedBlockUnder } from './changenote.mjs';
import { checkMod, loadConfig } from './config.mjs';
import { formatGallery, listGallery } from './gallery.mjs';
import { LIMITS, checkBytes } from './limits.mjs';
import { digest, checkPreview } from './preview.mjs';
import { formatDiff, isIdentical, lineDiff } from './line-diff.mjs';
import { relocatingExec } from './relocate-vdf.mjs';
import { formatSummary, measure, topLevelSummary } from './stage-summary.mjs';
import { fetchImageDigest, fetchPage } from './steam-page.mjs';

const APP_ID = '294100';

function required(name) {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is required`);
  return value;
}

const flag = (name) => process.env[name] === 'true';
const dryRun = process.env.DRY_RUN !== 'false';
const updatePreview = flag('UPDATE_PREVIEW');
const updateDescription = flag('UPDATE_DESCRIPTION');
const updateTitle = flag('UPDATE_TITLE');
const updateTags = flag('UPDATE_TAGS');
const version = required('VERSION');
const commitDir = required('TAG_DIR');
const modPath = join(commitDir, 'Mod');

const config = await loadConfig(commitDir);
const changenote = changenoteFor(await readFile(join(commitDir, 'PUBLICATION.md'), 'utf8'), version);
await checkMod(modPath, config);
checkBytes('the change note', changenote, LIMITS.changenote);
// With aboutFromDescription the <description> of About.xml is generated from the description source: a hand edit that
// drifted from it stops the run, in the dry-run as in the publish.
if (config.aboutFromDescription) {
  const problem = await aboutProblem(commitDir, config);
  if (problem) throw new Error(problem);
  console.log(`About.xml: its description is the plain text of ${config.description.file}`);
}

const { stageModContent } = await import('semantic-release-steam/lib/stage-content.mjs');
const { uploadWorkshopItem } = await import('semantic-release-steam/lib/steamcmd.mjs');
const { createWorkshopVdf } = await import('semantic-release-steam/lib/vdf.mjs');
if (typeof uploadWorkshopItem !== 'function' || typeof createWorkshopVdf !== 'function') {
  throw new Error('semantic-release-steam does not export the upload functions this script relies on');
}
const stagePath = await stageModContent({ modPath });
const { files, bytes } = await measure(stagePath);
console.log(`staged ${files} files, ${(bytes / 1e6).toFixed(2)} MB, from ${modPath}`);
console.log(`content by top-level entry:\n${formatSummary(await topLevelSummary(stagePath))}`);
console.log(`target: Workshop item ${config.workshopId} (app ${APP_ID}); visibility is never sent`);
console.log(`publish template: ${config.templateStamp ?? 'unknown'}`);
console.log(`options: update_preview=${updatePreview} update_description=${updateDescription} update_title=${updateTitle} update_tags=${updateTags}`);
console.log(`change note (from PUBLICATION.md, section ${version}):\n${changenote}`);
if (config.galleryDir) {
  // Not an option: SteamCMD cannot send gallery images, so this only lists what is to be uploaded by hand.
  console.log(await listGallery(join(commitDir, config.galleryDir)).then((files) => formatGallery(files, config.galleryDir), () => `gallery: folder ${config.galleryDir} not found in this commit`));
}

// What the public page serves now. Reading it needs no login; when it fails the dry-run says so
// and the comparison is skipped, the update itself is not affected.
let page = null;
try { page = process.env.SKIP_PAGE_READ === 'true' ? null : await fetchPage(config.workshopId); } catch (error) { console.log(`public page not readable (${error.message}): comparisons skipped`); }

let previewfile;
const stagedPreview = join(stagePath, config.previewFile);
if (updatePreview) {
  const local = await checkPreview(stagedPreview).catch((error) => { throw new Error(`update_preview: ${error.message}`); });
  previewfile = stagedPreview;
  console.log(`preview to send: Mod/${config.previewFile}, ${local.bytes} bytes, sha256 ${local.sha256}`);
} else {
  console.log('preview: not sent (update_preview is false)');
}
if (page?.previewUrl && updatePreview) {
  try {
    const current = await fetchImageDigest(page.previewUrl);
    console.log(`preview on the page now: ${current.bytes} bytes, sha256 ${current.sha256}`);
    const local = digest(await readFile(stagedPreview));
    console.log(local.sha256 === current.sha256 ? 'the page already serves this image: nothing would change' : 'the page serves a different image: it would be replaced');
  } catch (error) {
    console.log(`preview on the page not readable (${error.message})`);
  }
}

let description;
if (updateDescription) {
  if (!config.description) throw new Error('update_description: publish.config.json has no "description" source');
  const markdown = config.description.format === 'markdown';
  if (markdown) {
    // The same extraction aboutProblem/About.xml already used above, so the two never diverge on the same source file.
    const text = await descriptionMarkdown(commitDir, config.description);
    if (!text.trim()) throw new Error(`update_description: ${config.description.file} is empty`);
    // The same converter semantic-release-steam uses for a README: Markdown in, Steam BBCode out.
    const { renderSteamBBCode } = await import('semantic-release-steam/lib/description.mjs');
    description = renderSteamBBCode(text).trim();
  } else {
    const source = await readFile(join(commitDir, config.description.file), 'utf8');
    description = config.description.heading
      ? fencedBlockUnder(source, new RegExp(config.description.heading), { label: `"${config.description.heading}"`, what: 'description' })
      : source.trim();
  }
  const descriptionBytes = checkBytes('update_description: the description', description, LIMITS.description);
  const local = digest(Buffer.from(description));
  console.log(`description to send: ${description.length} characters (${descriptionBytes} bytes), sha256 ${local.sha256}, from ${config.description.file}${markdown ? `${config.description.heading ? ', block under the heading,' : ''} (Markdown converted to BBCode)` : ''}`);
  if (markdown) console.log(`description as converted (this exact text is sent):\n${description}`);
  if (page) {
    const diff = lineDiff(page.description, description);
    console.log(isIdentical(diff) ? 'the page already has this description: nothing would change' : `changes against the description on the page ('-' is on the page now, '+' would be sent):\n${formatDiff(diff)}`);
  }
} else {
  console.log('description: not sent (update_description is false)');
}

const about = await readFile(join(modPath, 'About', 'About.xml'), 'utf8');
let title;
if (updateTitle) {
  title = aboutName(about);
  checkBytes('update_title: the title', title, LIMITS.title);
  console.log(`title to send: "${title}" (the <name> of Mod/About/About.xml)`);
  if (page) console.log(page.title === title ? 'the page already has this title: nothing would change' : `title on the page now: "${page.title}"`);
} else {
  console.log('title: not sent (update_title is false)');
}

let tags;
if (updateTags) {
  tags = tagsFor(about);
  console.log(`tags to send (the whole set, replacing the page's): ${tags.join(', ')}`);
  if (page) {
    const removed = page.tags.filter((tag) => !tags.includes(tag));
    const added = tags.filter((tag) => !page.tags.includes(tag));
    console.log(`tags on the page now: ${page.tags.join(', ') || '(none)'}`);
    console.log(removed.length + added.length === 0 ? 'the page already has these tags: nothing would change' : `tags removed: ${removed.join(', ') || '(none)'}; tags added: ${added.join(', ') || '(none)'}`);
  }
} else {
  console.log('tags: not sent (update_tags is false)');
}

if (dryRun) {
  // Everything the upload does except talking to Steam: the VDF it would write, and the move of
  // workshop.vdf out of the content folder, run against a fake steamcmd.
  const vdf = createWorkshopVdf({ appId: APP_ID, publishedFileId: config.workshopId, contentFolder: stagePath, changenote, previewfile, description, title, tags });
  for (const expected of [`"publishedfileid" "${config.workshopId}"`, `"appid" "${APP_ID}"`, '"changenote"']) {
    if (!vdf.includes(expected)) throw new Error(`the generated workshop.vdf lacks ${expected}`);
  }
  if (vdf.includes('"previewfile"') !== updatePreview) throw new Error(`the generated workshop.vdf ${updatePreview ? 'lacks' : 'has'} "previewfile" although update_preview is ${updatePreview}`);
  if (vdf.includes('"description"') !== updateDescription) throw new Error(`the generated workshop.vdf ${updateDescription ? 'lacks' : 'has'} "description" although update_description is ${updateDescription}`);
  if (vdf.includes('"title"') !== updateTitle) throw new Error(`the generated workshop.vdf ${updateTitle ? 'lacks' : 'has'} "title" although update_title is ${updateTitle}`);
  if (vdf.includes('"tags"') !== updateTags) throw new Error(`the generated workshop.vdf ${updateTags ? 'lacks' : 'has'} "tags" although update_tags is ${updateTags}`);
  if (vdf.includes('"visibility"')) throw new Error('the generated workshop.vdf would set "visibility", which this workflow never sends');
  const probe = await mkdtemp(join(tmpdir(), 'vdf-probe-'));
  const probeVdf = join(probe, 'workshop.vdf');
  await writeFile(probeVdf, vdf);
  let seen;
  await relocatingExec(async (file, args) => { seen = args; return { stdout: '', stderr: '' }; })(
    'steamcmd', ['+login', 'user', '+workshop_build_item', probeVdf, '+quit'], {});
  const moved = seen?.find((arg) => arg.endsWith('workshop.vdf'));
  if (!moved || moved === probeVdf || (await readdir(probe)).includes('workshop.vdf')) {
    throw new Error('workshop.vdf is not moved out of the content folder before steamcmd runs');
  }
  console.log('upload path checked without contacting Steam: workshop.vdf content and its relocation are correct.');
  console.log('DRY RUN: nothing was sent to Steam.');
} else {
  // No process.exit() above: after a fetch it can crash Node on Windows, and the script ends by itself.
  await uploadWorkshopItem({
    steamCmdPath: required('STEAMCMD_PATH'),
    steamUsername: required('STEAM_USERNAME'),
    steamConfigPath: required('STEAM_CONFIG_VDF'),
    stagePath,
    appId: APP_ID,
    publishedFileId: config.workshopId,
    changenote,
    previewfile,
    description,
    title,
    tags,
    execFileAsync: relocatingExec(),
    verbose: true,
    logger: console,
  });
  console.log(`uploaded to Workshop item ${config.workshopId}. Verify the public page before recording it as published.`);
}
