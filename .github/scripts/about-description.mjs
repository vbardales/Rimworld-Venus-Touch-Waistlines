import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { fencedBlockUnder } from './changenote.mjs';

// One source for the description: the Markdown of the repository (a fenced block of PUBLICATION.md, or a whole file).
// The Steam page gets it converted to BBCode; the <description> of Mod/About/About.xml, which the game shows in the
// mod list, gets it as plain text, produced here and checked by every dry-run so that no hand edit can drift from it.

const encode = (text) => text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
const decode = (text) => text.replaceAll('&lt;', '<').replaceAll('&gt;', '>').replaceAll('&quot;', '"').replaceAll('&apos;', "'").replaceAll('&amp;', '&');

// The subset of Markdown a Workshop description uses, as text a player can read where tags are not rendered.
export function markdownToPlainText(markdown) {
  const lines = markdown.replace(/\r\n?/g, '\n').split('\n').map((raw) => {
    let line = raw.replace(/\s+$/, '');
    if (/^\s*([-*_])(\s*\1){2,}\s*$/.test(line)) return '';
    line = line.replace(/^\s{0,3}#{1,6}\s+/, '').replace(/\s+#+$/, '');
    line = line.replace(/^(\s*)>\s?/, '$1');
    line = line.replace(/^(\s*)[-*+]\s+/, '$1- ');
    // The URL may hold one level of balanced parentheses (https://en.wikipedia.org/wiki/Foo_(bar)), which [^)\s]+ cut short.
    // The link text may hold one level of balanced brackets ("[XND] Nocturnal Animals"); an unbalanced "]" ends it, so
    // "See [note] and [Pickle](u)" links only Pickle.
    line = line.replace(/!\[((?:[^\[\]]|\[[^\[\]]*\])*)\]\(((?:[^()\s]|\([^()\s]*\))+)(?:\s+"[^"]*")?\)/g, (_, alt, url) => (alt && alt !== url ? `${alt} (${url})` : url));
    line = line.replace(/\[((?:[^\[\]]|\[[^\[\]]*\])+)\]\(((?:[^()\s]|\([^()\s]*\))+)(?:\s+"[^"]*")?\)/g, (_, text, url) => (text === url ? url : `${text} (${url})`));
    line = line.replace(/\*\*(.+?)\*\*/g, '$1').replace(/__(.+?)__/g, '$1');
    line = line.replace(/(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])/g, '$1').replace(/(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])/g, '$1');
    line = line.replace(/`([^`]+)`/g, '$1');
    return line;
  });
  return lines.join('\n').replace(/\n{3,}/g, '\n\n').trim();
}

// The position of the real <description>, not one inside an XML comment.
function locate(xml) {
  const masked = xml.replace(/<!--[\s\S]*?-->/g, (comment) => ' '.repeat(comment.length));
  const match = masked.match(/<description>([\s\S]*?)<\/description>/);
  if (!match) throw new Error('About.xml has no <description>');
  return { start: match.index + '<description>'.length, end: match.index + '<description>'.length + match[1].length };
}

const normalize = (text) => text.replace(/\r\n?/g, '\n').trim();

export function readAboutDescription(xml) {
  const { start, end } = locate(xml);
  const inner = xml.slice(start, end);
  const cdata = inner.match(/^\s*<!\[CDATA\[([\s\S]*?)\]\]>\s*$/);
  return normalize(cdata ? cdata[1] : decode(inner));
}

export function replaceAboutDescription(xml, text) {
  const { start, end } = locate(xml);
  return xml.slice(0, start) + encode(text) + xml.slice(end);
}

// The Markdown of the description source of publish.config.json: the fenced block under the heading when there is
// one, the whole file otherwise.
export async function descriptionMarkdown(commitDir, description) {
  const source = await readFile(join(commitDir, description.file), 'utf8');
  return description.heading
    ? fencedBlockUnder(source, new RegExp(description.heading), { label: `"${description.heading}"`, what: 'description' })
    : source;
}

const ABOUT_PATH = join('Mod', 'About', 'About.xml');

// Everything the check and the writer need: the expected text, the About.xml as it is, and what it would become.
export async function aboutState(commitDir, config) {
  if (config.description?.format !== 'markdown') throw new Error('aboutFromDescription needs a Markdown description source (description.format "markdown")');
  const expected = markdownToPlainText(await descriptionMarkdown(commitDir, config.description));
  if (!expected) throw new Error(`${config.description.file}: the description is empty, so About.xml cannot be generated from it`);
  const xml = await readFile(join(commitDir, ABOUT_PATH), 'utf8');
  return { expected, xml, current: readAboutDescription(xml), path: ABOUT_PATH, next: replaceAboutDescription(xml, expected) };
}

export async function aboutProblem(commitDir, config) {
  const { expected, current, path } = await aboutState(commitDir, config);
  if (current === expected) return null;
  return `the <description> of ${path} is not the plain text of ${config.description.file}${config.description.heading ? ` (section "${config.description.heading}")` : ''}: run "node .github/scripts/sync-about-description.mjs --write", read the diff and commit it`;
}
