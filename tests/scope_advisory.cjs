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
      state.track ?? (state.minor ? '[x] **Bug Fix / Minor Patch**' : '[x] **Feature / Architectural Change -- Stage 1: Design Doc PR**'),
      '## Summary of Key Changes',
      '## Human Accountability Affirmation',
      state.affirmation ?? '[x] I am a human contributor',
      '## Verification',
    ].join('\n')
    await evaluate(github, {
      repo: { owner: 'fixture', repo: 'example' },
      payload: { action: state.action ?? 'opened', changes: state.editedFields, pull_request: {
        number: 1, body: state.body ?? body, user: { type: state.bot ? 'Bot' : 'User' },
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

for (const track of [
  'Bug Fix / Minor Patch',
  'Feature / Architectural Change -- Stage 1: Design Doc PR',
  'Feature / Architectural Change -- Stage 2: Implementation PR',
]) {
  for (const selection of [`Track: ${track}`, `- [x] **${track}** (track requirements)`]) {
    test(`accept exactly one track: ${selection}`, async () => {
      const state = fixture()
      state.track = selection
      await state.run()
      assert.equal(state.labels.has('design-needed'), track === 'Bug Fix / Minor Patch')
    })
  }
}

for (const track of [
  '',
  'Track: ',
  'Track: Other',
  '- [x] **Other**',
  'Track: Bug Fix / Minor Patch\nTrack: Feature / Architectural Change -- Stage 1: Design Doc PR',
  '- [x] **Bug Fix / Minor Patch**\n- [x] **Feature / Architectural Change -- Stage 1: Design Doc PR**',
  'Track: Bug Fix / Minor Patch\n- [x] **Bug Fix / Minor Patch**',
  'Track: Other\n- [x] **Bug Fix / Minor Patch**',
]) {
  test(`reject missing, unknown, or conflicting tracks: ${JSON.stringify(track)}`, async () => {
    const state = fixture()
    state.track = track
    await assert.rejects(state.run(), /track/i)
  })
}

test('a track outside Contribution Type cannot satisfy the selection', async () => {
  const state = fixture()
  state.track = ''
  state.affirmation = '[x] I am a human contributor\nTrack: Bug Fix / Minor Patch'
  await assert.rejects(state.run(), /track/i)
})

test('new track descriptions still require human affirmation', async () => {
  const state = fixture()
  state.track = 'Track: Bug Fix / Minor Patch'
  state.affirmation = '[ ] I am a human contributor'
  await assert.rejects(state.run(), /Affirmation/)
})

test('bots remain exempt from description and affirmation requirements', async () => {
  const state = fixture()
  state.bot = true
  state.body = ''
  await state.run()
})

test('filled current PR template passes without deleting track explanations', async () => {
  const state = fixture()
  state.body = readFileSync(`${__dirname}/../.github/PULL_REQUEST_TEMPLATE.md`, 'utf8')
    .replace('Track: <choose one track>', 'Track: Bug Fix / Minor Patch')
    .replace('[ ] I am a human contributor', '[x] I am a human contributor')
  await state.run()
  assert.ok(state.labels.has('design-needed'))
})

test('body edits and title-only edits validate the current description', async () => {
  const state = fixture()
  state.action = 'edited'
  state.editedFields = { body: { from: 'older description' } }
  state.track = 'Track: Bug Fix / Minor Patch'
  state.affirmation = '[ ] I am a human contributor'
  await assert.rejects(state.run(), /Affirmation/)
  state.editedFields = { title: { from: 'older title' } }
  await assert.rejects(state.run(), /Affirmation/)
  state.affirmation = '[x] I am a human contributor'
  await state.run()
  state.track = 'Track: Other'
  await assert.rejects(state.run(), /track/i)
})
