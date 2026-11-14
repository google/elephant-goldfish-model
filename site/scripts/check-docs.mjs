import assert from 'node:assert/strict';
import { readFile, readdir, access } from 'node:fs/promises';
import { repositoryLink, transformRepositoryMarkdown, remarkRepositoryLinks } from '../src/lib/repository-markdown.mjs';
import { createMarkdownProcessor } from '@astrojs/markdown-remark';
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import remarkStringify from 'remark-stringify';

const originalFetch = globalThis.fetch;
try {
  const cases = [
    { ok: true, count: 11832, expected: 11832 },
    { ok: true, count: -1, expected: null },
    { ok: true, count: '11832', expected: null },
    { ok: false, count: 11832, expected: null },
    { error: true, expected: null },
  ];
  for (const [index, sample] of cases.entries()) {
    globalThis.fetch = async () => {
      if (sample.error) throw new Error('GitHub unavailable');
      return { ok: sample.ok, json: async () => ({ stargazers_count: sample.count }) };
    };
    const { githubStars } = await import(`../src/lib/github-stars.ts?test=${index}`);
    assert.equal(await githubStars, sample.expected);
  }
} finally {
  globalThis.fetch = originalFetch;
}

const source = new URL('../../skills/egm-draft/SKILL.md', import.meta.url).pathname;
assert.equal(repositoryLink('../../docs/codex.md', source), 'https://github.com/google/elephant-goldfish-model/blob/main/docs/codex.md');
assert.equal(repositoryLink('references/design_doc.md', source), 'https://github.com/google/elephant-goldfish-model/blob/main/skills/egm-draft/references/design_doc.md');
for (const url of ['#section', '/guide', 'https://egm.dev', 'mailto:hello@example.com']) assert.equal(repositoryLink(url, source), url);
assert.equal(repositoryLink('../../docs/codex.md#verification', source), 'https://github.com/google/elephant-goldfish-model/blob/main/docs/codex.md#verification');
assert.equal(repositoryLink('../../docs/', source), 'https://github.com/google/elephant-goldfish-model/tree/main/docs/');
assert.equal(repositoryLink('../../site/public/favicon.svg', source, true), 'https://raw.githubusercontent.com/google/elephant-goldfish-model/main/site/public/favicon.svg');
assert.equal(repositoryLink('[RelativePath]#L1', source), '[RelativePath]#L1');
assert.throws(() => repositoryLink('../../../outside.md', source), /escapes/);
assert.throws(() => repositoryLink('missing-file.md', source), /ENOENT/);
const imageTree = { children: [
  { type: 'image', url: '../../site/public/favicon.svg' },
  { type: 'imageReference', identifier: 'mark' },
  { type: 'definition', identifier: 'mark', url: '../../site/public/favicon.svg' },
] };
transformRepositoryMarkdown(imageTree, source);
for (const node of [imageTree.children[0], imageTree.children[2]]) {
  assert.equal(node.url, 'https://raw.githubusercontent.com/google/elephant-goldfish-model/main/site/public/favicon.svg');
}
const tree = { children: [{ type: 'heading', depth: 1 }, { type: 'paragraph', children: [{ type: 'link', url: '../../docs/codex.md' }] }, { type: 'code', value: '[Example](./example.md)' }] };
transformRepositoryMarkdown(tree, source);
assert.equal(tree.children.length, 2);
assert.equal(tree.children[0].children[0].url, 'https://github.com/google/elephant-goldfish-model/blob/main/docs/codex.md');
assert.equal(tree.children[1].value, '[Example](./example.md)');

const fixture = '[Guide](../../docs/codex.md#verification)\n\n[Folder](../../docs/)\n\n![Inline](../../site/public/favicon.svg)\n\n![Reference][mark]\n\n[mark]: ../../site/public/favicon.svg';
const htmlProcessor = await createMarkdownProcessor({ remarkPlugins: [remarkRepositoryLinks] });
const rendered = await htmlProcessor.render(fixture, { fileURL: new URL(`file://${source}`) });
const markdownProcessor = unified().use(remarkParse).use(remarkGfm).use(remarkStringify);
const fixtureTree = markdownProcessor.parse(fixture);
transformRepositoryMarkdown(fixtureTree, source);
const exported = markdownProcessor.stringify(fixtureTree);
for (const output of [rendered.code, exported]) {
  assert.ok(output.includes('https://github.com/google/elephant-goldfish-model/blob/main/docs/codex.md#verification'));
  assert.ok(output.includes('https://github.com/google/elephant-goldfish-model/tree/main/docs/'));
  assert.ok(output.includes('https://raw.githubusercontent.com/google/elephant-goldfish-model/main/site/public/favicon.svg'));
  assert.ok(!output.includes('blob/main/site/public/favicon.svg'));
}

const pages = ['install', 'guide', 'getting-started', 'workflow', 'skills', 'skills/egm-ask', 'skills/egm-bootstrap', 'skills/egm-brainstorm', 'skills/egm-draft', 'skills/egm-drift-report', 'skills/egm-resolve', 'skills/egm-review', 'skills/egm-review-loop'];
const skillNames = (await readdir(new URL('../../skills/', import.meta.url), { withFileTypes: true }))
  .filter(entry => entry.isDirectory()).map(entry => entry.name);
for (const name of skillNames) {
  assert.ok(pages.includes(`skills/${name}`), `${name}: skill page in the checked routes`);
  const page = await readFile(new URL(`../../docs/site/skills/${name}.md`, import.meta.url), 'utf8');
  assert.ok(page.includes(`skills/${name}/SKILL.md`), `${name}: link to its own SKILL.md`);
}
for (const page of pages) {
  const html = await readFile(new URL(`../dist/${page}/index.html`, import.meta.url), 'utf8');
  const markdown = await readFile(new URL(`../dist/${page}.md`, import.meta.url), 'utf8');
  assert.equal((html.match(/<h1\b/g) ?? []).length, 1, `${page}: one page title`);
  assert.ok(html.includes('type="text/markdown"'), `${page}: discoverable Markdown`);
  assert.ok(markdown.startsWith('# '), `${page}: Markdown title`);
  assert.ok(!markdown.includes('<nav'), `${page}: no page chrome`);
  for (const [, asset] of html.matchAll(/(?:href|src)="(\/_astro\/[^"?#]+)"/g)) {
    await access(new URL(`../dist${asset}`, import.meta.url));
  }
}
for (const file of ['llms.txt', 'llms-full.txt', 'llms-small.txt', 'pagefind/pagefind.js']) await access(new URL(`../dist/${file}`, import.meta.url));
const redirects = [['docs', 'guide'], ['docs/getting-started', 'getting-started'], ['docs/workflow', 'workflow'], ['docs/skills', 'skills'],
  ...pages.filter(page => page.startsWith('skills/')).map(page => [`docs/${page}`, page])];
for (const [oldPath, target] of redirects) {
  const html = await readFile(new URL(`../dist/${oldPath}/index.html`, import.meta.url), 'utf8');
  assert.ok(html.includes(`content="0;url=/${target}"`), `${oldPath}: redirect target`);
}
const full = await readFile(new URL('../dist/llms-full.txt', import.meta.url), 'utf8');
assert.ok(full.includes('egm-review-loop'));
assert.ok(full.includes('Getting started'));
console.log('Documentation routes, Markdown exports, repository links, llms.txt and search index passed.');
