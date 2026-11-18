import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';
import ts from 'typescript';

const source = readFileSync(new URL('../src/components/Explainer.astro', import.meta.url), 'utf8');
const script = ts.transpile(source.match(/<script>([\s\S]*?)<\/script>/)[1]);

test('explainer embeds no YouTube player before the visitor clicks play', () => {
  assert.doesNotMatch(source.split('<script>')[0], /<iframe/i);
  assert.doesNotMatch(source.split('<script>')[0], /youtube(-nocookie)?\.com\/embed/);
  assert.match(source, /aria-label=\{`Play video: \$\{title\}`\}/);
});

test('clicking the explainer button replaces it with a youtube-nocookie iframe and focuses it', () => {
  let click;
  let replaced;
  let focused = false;
  const button = {
    dataset: { video: '8_x1u7qSqGs', title: 'Elephant-Goldfish Model explainer' },
    addEventListener: (_, handler) => { click = handler; },
    replaceWith: (node) => { replaced = node; },
  };
  vm.runInNewContext(script, {
    document: {
      querySelectorAll: () => [button],
      createElement: (tag) => ({
        tag,
        focus: () => { focused = true; },
      }),
    },
  });
  click();
  assert.equal(replaced.tag, 'iframe');
  assert.equal(replaced.src, 'https://www.youtube-nocookie.com/embed/8_x1u7qSqGs?autoplay=1&rel=0');
  assert.equal(replaced.title, 'Elephant-Goldfish Model explainer');
  assert.equal(replaced.allowFullscreen, true);
  assert.equal(replaced.referrerPolicy, 'strict-origin-when-cross-origin');
  assert.equal(focused, true);
});
