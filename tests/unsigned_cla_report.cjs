// Copyright 2026 Google LLC. SPDX-License-Identifier: Apache-2.0

const assert = require('node:assert/strict');
const { classify, report } = require('../.github/scripts/unsigned_cla_report.cjs');
const { test } = require('node:test');

const input = {
  notice: '2026-11-01T12:00:00Z',
  authorActivity: [],
  firstHeadCheck: '2026-11-01T11:59:00Z',
  exempt: false,
  now: Date.parse('2026-11-15T12:00:00Z'),
};

assert.equal(classify({ ...input, now: Date.parse('2026-11-08T11:59:59Z') }), null);
assert.equal(classify({ ...input, now: Date.parse('2026-11-08T12:00:00Z') }), 'Would remind');
assert.equal(classify({ ...input, now: Date.parse('2026-11-15T11:59:59Z') }), 'Would remind');
assert.equal(classify(input), 'Would close');
assert.equal(classify({ ...input, exempt: true }), 'Exempt (keep-open)');
assert.equal(classify({ ...input, authorActivity: ['2026-11-14T00:00:00Z'] }), 'Author replied');
for (const firstHeadCheck of [undefined, '2026-11-02T00:00:00Z']) {
  assert.equal(classify({ ...input, firstHeadCheck }), 'Head updated or push timing uncertain');
}

test('empty report explicitly says no PRs matched', async () => {
  const github = {
    rest: { pulls: {} },
    paginate: { async *iterator() {} },
  };
  const summary = {
    addHeading() { return this; },
    addRaw() { return this; },
    addList(items) {
      assert.deepEqual(items, ['No PRs matched.']);
      return this;
    },
    async write() {},
  };
  await report(github, {}, { summary });
});
