import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { aboutProblem, aboutState, markdownToPlainText, readAboutDescription, replaceAboutDescription } from '../scripts/about-description.mjs';

const NL = String.fromCharCode(10);
const fence = String.fromCharCode(96).repeat(3);

test('Markdown becomes the plain text a player reads in the mod list', () => {
  const markdown = ['# Groups', '', 'Some **bold** and *italic* text, `code`, and a [link](https://example.com/a).', '', '## Works with', '', '- [Better Architect Menu](https://steamcommunity.com/sharedfiles/filedetails/?id=1)', '* second', '  - nested', '', '---', '', '> quoted', '', '[https://example.com](https://example.com)'].join(NL);
  assert.equal(markdownToPlainText(markdown), [
    'Groups', '',
    'Some bold and italic text, code, and a link (https://example.com/a).', '',
    'Works with', '',
    '- Better Architect Menu (https://steamcommunity.com/sharedfiles/filedetails/?id=1)',
    '- second',
    '  - nested', '',
    'quoted', '',
    'https://example.com',
  ].join(NL));
});

test('words with underscores or asterisks are left alone, and blank lines are collapsed', () => {
  assert.equal(markdownToPlainText('a snake_case_name and 2 * 3 * 4' + NL + NL + NL + NL + 'end'), 'a snake_case_name and 2 * 3 * 4' + NL + NL + 'end');
  assert.equal(markdownToPlainText('![alt text](https://x.test/i.png) and ![https://x.test/j.png](https://x.test/j.png)'), 'alt text (https://x.test/i.png) and https://x.test/j.png');
  assert.equal(markdownToPlainText('line one  ' + NL + 'line two\r\nline three'), 'line one' + NL + 'line two' + NL + 'line three');
});

test('a link whose visible text itself contains brackets still converts', () => {
  assert.equal(
    markdownToPlainText('[[XND] Nocturnal Animals (Continued)](https://steamcommunity.com/sharedfiles/filedetails/?id=2269731409)'),
    '[XND] Nocturnal Animals (Continued) (https://steamcommunity.com/sharedfiles/filedetails/?id=2269731409)',
  );
  assert.equal(
    markdownToPlainText('![[alt]](https://x.test/i.png)'),
    '[alt] (https://x.test/i.png)',
  );
});

const about = (description, extra = '') => `<?xml version="1.0" encoding="utf-8"?>${NL}<ModMetaData>${NL}  <name>T</name>${NL}${extra}  <description>${description}</description>${NL}  <url>https://example.com</url>${NL}</ModMetaData>${NL}`;

test('the description of About.xml is read decoded, from CDATA too, and never from a comment', () => {
  assert.equal(readAboutDescription(about('Tom &amp; Jerry &lt;3' + NL + 'two')), 'Tom & Jerry <3' + NL + 'two');
  assert.equal(readAboutDescription(about('<![CDATA[Tom & Jerry]]>')), 'Tom & Jerry');
  assert.equal(readAboutDescription(about('real', '  <!-- <description>old</description> -->' + NL)), 'real');
  assert.equal(readAboutDescription(about('a' + '\r\n' + 'b')), 'a' + NL + 'b');
  assert.throws(() => readAboutDescription('<ModMetaData/>'), /no <description>/);
});

test('replacing the description touches that element only, escapes it, and skips a commented one', () => {
  const xml = about('old', '  <!-- <description>commented</description> -->' + NL);
  const next = replaceAboutDescription(xml, 'Tom & Jerry <3' + NL + 'two');
  assert.equal(next, xml.replace('<description>old</description>', '<description>Tom &amp; Jerry &lt;3' + NL + 'two</description>'));
  assert.ok(next.includes('<description>commented</description>'));
  assert.equal(readAboutDescription(next), 'Tom & Jerry <3' + NL + 'two');
});

async function repo({ description, block = '# Title' + NL + NL + 'Some **bold** text.', publication = null }) {
  const dir = await mkdtemp(join(tmpdir(), 'about-desc-'));
  await mkdir(join(dir, 'Mod', 'About'), { recursive: true });
  await writeFile(join(dir, 'Mod', 'About', 'About.xml'), about(description));
  await writeFile(join(dir, 'PUBLICATION.md'), publication ?? ['# Publication', '', '## Steam description', '', fence + 'markdown', block, fence, ''].join(NL));
  return dir;
}
const config = { description: { file: 'PUBLICATION.md', format: 'markdown', heading: '^## Steam description$' } };

test('the check passes when About.xml carries the plain text of the source, and says what to run when it does not', async () => {
  assert.equal(await aboutProblem(await repo({ description: 'Title' + NL + NL + 'Some bold text.' }), config), null);
  const problem = await aboutProblem(await repo({ description: 'A hand-written text' }), config);
  assert.match(problem, /the <description> of Mod[\\/]About[\\/]About\.xml is not the plain text of PUBLICATION\.md/);
  assert.match(problem, /sync-about-description\.mjs --write/);
  const state = await aboutState(await repo({ description: 'x' }), config);
  assert.equal(readAboutDescription(state.next), 'Title' + NL + NL + 'Some bold text.');
});

test('a source that is not Markdown, or is empty, cannot generate About.xml', async () => {
  await assert.rejects(aboutProblem(await repo({ description: 'x' }), { description: { file: 'PUBLICATION.md' } }), /needs a Markdown description source/);
  await assert.rejects(aboutProblem(await repo({ description: 'x', block: '---' }), config), /the description is empty/);
  await assert.rejects(aboutProblem(await repo({ description: 'x' }), { description: { ...config.description, heading: '^## Nowhere$' } }), /no "\^## Nowhere\$" section found/);
});

test('a link whose URL holds balanced parentheses is not cut short', () => {
  assert.equal(
    markdownToPlainText('[Foo](https://en.wikipedia.org/wiki/Foo_(bar))'),
    'Foo (https://en.wikipedia.org/wiki/Foo_(bar))',
  );
  assert.equal(markdownToPlainText('See [a](https://x.test/a) and [b](https://x.test/b_(c)) now'), 'See a (https://x.test/a) and b (https://x.test/b_(c)) now');
  assert.equal(markdownToPlainText('![i](https://x.test/i_(2).png)'), 'i (https://x.test/i_(2).png)');
});

test('a bare bracketed word before a link is not swallowed into the link text', () => {
  assert.equal(markdownToPlainText('See [note] and [Pickle](https://x.test/p)'), 'See [note] and Pickle (https://x.test/p)');
  assert.equal(markdownToPlainText('[a] [b] [c](https://x.test/c) [d]'), '[a] [b] c (https://x.test/c) [d]');
  assert.equal(markdownToPlainText('[[XND] Nocturnal Animals (Continued)](https://x.test/n)'), '[XND] Nocturnal Animals (Continued) (https://x.test/n)');
  assert.equal(markdownToPlainText('![[alt]](https://x.test/i.png)'), '[alt] (https://x.test/i.png)');
  assert.equal(markdownToPlainText('![](https://x.test/i.png)'), 'https://x.test/i.png');
});
