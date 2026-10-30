// Copyright 2026 Google LLC.
// SPDX-License-Identifier: Apache-2.0

const assert = require('node:assert/strict')
const { readFileSync } = require('node:fs')
const { test } = require('node:test')

const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
const evaluate = new AsyncFunction('github', 'context', 'core', readFileSync(0, 'utf8'))
const signature = '<!-- egm-scope-advisory -->'
const legacy = 'advisory: design-doc-suggested'

function fixture() {
  const state = { comments: [], labels: new Set(['ci']), changes: 101, minor: true }
  let nextId = 1
  const issues = {
    listComments: async () => state.comments,
    createComment: async ({ body }) => {
      state.comments.push({ id: nextId++, body, user: { login: 'github-actions[bot]' } })
    },
    updateComment: async ({ comment_id, body }) => {
      const comment = state.comments.find(c => c.id === comment_id)
      assert.ok(comment, 'updated comment must exist')
      comment.body = body
    },
    deleteComment: async ({ comment_id }) => {
      assert.ok(state.comments.some(c => c.id === comment_id), 'deleted comment must exist')
      state.comments = state.comments.filter(c => c.id !== comment_id)
    },
    addLabels: async ({ labels }) => labels.forEach(label => state.labels.add(label)),
    removeLabel: async ({ name }) => {
      if (!state.labels.delete(name)) {
        throw Object.assign(new Error('Label not found'), { status: 404 })
      }
    },
  }
  const pulls = { listFiles: async () => [{ filename: 'src/example.js', changes: state.changes }] }
  const github = {
    rest: { issues, pulls },
    paginate: async (method, args, map) => {
      const data = await method(args)
      return map ? map({ data }, () => {}) : data
    },
  }
  state.run = async (labels = [...state.labels], cleanupError) => {
    if (cleanupError) {
      const removeLabel = issues.removeLabel
      issues.removeLabel = async args => {
        if (args.name === legacy) throw cleanupError
        return removeLabel(args)
      }
    }
    const body = [
      '## Contribution Type',
      state.minor ? '[x] **Bug Fix / Minor Patch**' : '[x] **Feature / Architectural Change**',
      '## Summary of Key Changes',
      '## Human Accountability Affirmation',
      '[x] I am a human contributor',
      '## Verification',
    ].join('\n')
    await evaluate(github, {
      repo: { owner: 'fixture', repo: 'example' },
      payload: { pull_request: {
        number: 1, body, user: { type: 'User' },
        labels: labels.map(name => ({ name })),
      } },
    }, { setFailed: message => assert.fail(message) })
  }
  return state
}

test('create, refresh and retain one notice with current scope counts', async () => {
  const state = fixture()
  await state.run()
  assert.equal(state.comments.length, 1)
  const id = state.comments[0].id
  assert.ok(state.comments[0].body.includes(signature))
  assert.match(state.comments[0].body, /101 counted lines/)
  assert.ok(state.labels.has('design-needed'))
  state.changes = 150
  await state.run()
  assert.equal(state.comments.length, 1)
  assert.equal(state.comments[0].id, id)
  assert.match(state.comments[0].body, /150 counted lines/)
  const body = state.comments[0].body
  await state.run()
  assert.equal(state.comments.length, 1)
  assert.equal(state.comments[0].id, id)
  assert.equal(state.comments[0].body, body)
})

for (const resolution of ['trim diff', 'switch track']) {
  test(`remove resolved notice and label: ${resolution}`, async () => {
    const state = fixture()
    await state.run()
    if (resolution === 'trim diff') state.changes = 100
    else state.minor = false
    await state.run()
    assert.deepEqual(state.comments, [])
    assert.deepEqual([...state.labels], ['ci'])
  })
}

test('user marker cannot suppress a bot notice or be updated/deleted', async () => {
  const state = fixture()
  const human = { id: 99, body: `${signature} User discussion`, user: { login: 'contributor' } }
  state.comments.push(structuredClone(human))
  for (const changes of [101, 150, 100]) {
    state.changes = changes
    await state.run()
    assert.deepEqual(state.comments.find(c => c.id === human.id), human)
    assert.equal(state.comments.length, changes > 100 ? 2 : 1)
    const bot = state.comments.find(c => c.id !== human.id)
    if (bot) assert.ok(bot.body.includes(`${changes} counted lines`))
  }
})

for (const changes of [100, 101]) {
  test(`remove legacy label while preserving unrelated labels: ${changes} lines`, async () => {
    const state = fixture()
    state.changes = changes
    state.labels.add(legacy)
    await state.run()
    assert.ok(!state.labels.has(legacy))
    assert.ok(state.labels.has('ci'))
    assert.equal(state.labels.has('design-needed'), changes > 100)
    await state.run()
    assert.ok(!state.labels.has(legacy))
    assert.equal(state.comments.length, changes > 100 ? 1 : 0)
  })
}

test('stale event label does not fail cleanup', async () => {
  const state = fixture()
  await state.run(['ci', legacy])
  assert.ok(!state.labels.has(legacy))
  assert.ok(state.labels.has('design-needed'))
})

test('unexpected legacy cleanup errors remain visible', async () => {
  const state = fixture()
  const error = Object.assign(new Error('Forbidden'), { status: 403 })
  await assert.rejects(state.run(['ci', legacy], error), error)
})
