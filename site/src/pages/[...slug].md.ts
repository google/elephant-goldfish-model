import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { resolve } from 'node:path';
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkStringify from 'remark-stringify';
import remarkGfm from 'remark-gfm';
import { transformRepositoryMarkdown } from '../lib/repository-markdown.mjs';

export async function getStaticPaths() {
  return (await getCollection('docs')).map(entry => ({ params: { slug: entry.id }, props: { entry } }));
}

export const GET: APIRoute = ({ props }) => {
  const { entry } = props;
  const processor = unified().use(remarkParse).use(remarkGfm).use(remarkStringify);
  const tree = processor.parse(entry.body ?? '');
  transformRepositoryMarkdown(tree, resolve(entry.filePath));
  const markdown = `# ${entry.data.title}\n\n${entry.data.description ?? ''}\n\n${processor.stringify(tree)}`;
  return new Response(markdown, { headers: { 'Content-Type': 'text/markdown; charset=utf-8' } });
};
