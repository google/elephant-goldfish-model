import { relative, resolve } from 'node:path';
import { statSync } from 'node:fs';

// Astro relocates this module during prerendering. npm runs from site/.
const root = resolve(process.cwd(), '..');
const repository = 'https://github.com/google/elephant-goldfish-model/blob/main/';

export function repositoryLink(url, file, image = false) {
  if (/^(?:[a-z][a-z\d+.-]*:|\/|#)/i.test(url) || /[\[\]]/.test(url)) return url;
  const sourcePath = relative(root, file).replaceAll('\\', '/');
  const target = new URL(url, repository + sourcePath);
  const path = decodeURIComponent(target.pathname.replace('/google/elephant-goldfish-model/blob/main/', ''));
  const local = resolve(root, path);
  const boundary = relative(root, local);
  if (boundary.startsWith('..') || target.origin !== 'https://github.com' || !target.pathname.startsWith('/google/elephant-goldfish-model/blob/main/')) {
    throw new Error(`Repository reference escapes the repository: ${url} in ${file}`);
  }
  const directory = statSync(local).isDirectory();
  if (image) return `https://raw.githubusercontent.com/google/elephant-goldfish-model/main/${target.pathname.split('/blob/main/')[1]}${target.search}${target.hash}`;
  if (directory) target.pathname = target.pathname.replace('/blob/main/', '/tree/main/');
  return target.href;
}

export function transformRepositoryMarkdown(tree, file) {
  if (/(?:^|[\\/])SKILL\.md$/.test(String(file)) && tree.children[0]?.type === 'heading' && tree.children[0].depth === 1) {
    tree.children.shift();
  }
  const imageReferences = new Set();
  function collect(node) {
    if (node.type === 'imageReference') imageReferences.add(node.identifier);
    node.children?.forEach(collect);
  }
  collect(tree);
  function visit(node) {
    if (['link', 'image', 'definition'].includes(node.type)) {
      node.url = repositoryLink(node.url, String(file), node.type === 'image' || (node.type === 'definition' && imageReferences.has(node.identifier)));
    }
    node.children?.forEach(visit);
  }
  visit(tree);
}

export function remarkRepositoryLinks() {
  return (tree, file) => transformRepositoryMarkdown(tree, file.path);
}
