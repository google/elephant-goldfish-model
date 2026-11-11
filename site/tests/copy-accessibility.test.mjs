import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';
import ts from 'typescript';

const source = readFileSync(new URL('../src/components/Home.astro', import.meta.url), 'utf8');
const script = ts.transpile(source.match(/<script>([\s\S]*?)<\/script>/)[1]);

for (const denied of [false, true]) {
  test(`copy preserves the command in its accessible name (denied=${denied})`, async () => {
    const command = 'claude plugin marketplace add google/elephant-goldfish-model && \\\nclaude plugin install egm@egm';
    const original = `Copy Claude command: ${command}`;
    let label = original;
    let click;
    let reset;
    let copied;
    const classes = new Set();
    const button = {
      dataset: { copy: command },
      getAttribute: () => label,
      setAttribute: (_, value) => { label = value; },
      addEventListener: (_, handler) => { click = handler; },
      classList: { add: (value) => classes.add(value), remove: (value) => classes.delete(value) },
    };
    vm.runInNewContext(script, {
      document: { querySelectorAll: () => [button] },
      navigator: { clipboard: { writeText: async (value) => {
        if (denied) throw new Error('Permission denied');
        copied = value;
      } } },
      window: { setTimeout: (callback) => { reset = callback; return 1; }, clearTimeout: () => {} },
    });
    await click();
    if (denied) {
      assert.equal(label, original);
      assert.equal(classes.size, 0);
      assert.equal(reset, undefined);
    } else {
      assert.equal(copied, command);
      assert.equal(label, `Copied: ${command}`);
      assert.ok(classes.has('copied'));
      reset();
      assert.equal(label, original);
      assert.equal(classes.size, 0);
    }
  });
}
