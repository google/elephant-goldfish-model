// Copyright 2026 Google LLC.
// SPDX-License-Identifier: Apache-2.0

const assert = require('node:assert/strict')
const triage = require('../.github/scripts/metadata-triage.cjs')

const base = {
  number: 42, title: 'Host install fails', body: 'Cannot install EGM in Codex',
  updated_at: '2026-11-06T00:00:00Z', state: 'open', labels: [], type: null
}
const context = { repo: { owner: 'example', repo: 'egm' }, eventName: 'issues', payload: { issue: base } }
const core = { info() {}, setOutput() {}, summary: {
  addHeading() { return this }, addCodeBlock() { return this }, async write() {}
} }

function harness(issue = base, events = [], available = Object.keys(triage.areas)) {
  let current = structuredClone(issue)
  const writes = []
  const methods = { events: Symbol(), labels: Symbol(), files: Symbol() }
  const github = {
    rest: {
      issues: {
        get: async () => ({ data: structuredClone(current) }),
        listEvents: methods.events, listLabelsForRepo: methods.labels,
        update: async args => {
          writes.push(['type', args.type])
          current.type = { name: args.type }
          current.updated_at = '2026-11-06T00:00:01Z'
          return { data: structuredClone(current) }
        },
        addLabels: async args => {
          writes.push(['labels', args.labels])
          current.labels.push(...args.labels.map(name => ({ name })))
          return { data: current.labels }
        }
      },
      pulls: { get: async () => ({ data: { head: { sha: 'head' } } }), listFiles: methods.files }
    },
    request: async () => ({ data: [{ name: 'Bug', is_enabled: true }] }),
    paginate: async method => method === methods.events ? events :
      method === methods.labels ? available.map(name => ({ name })) : [{ filename: 'site/a.astro' }]
  }
  return { github, context, core, writes, setIssue: value => { current = value } }
}

function plan(issue = base, proposal = { type: 'Bug', labels: ['harness'] }) {
  return { snapshot: triage.snapshot(issue, issue.pull_request ? 'head' : null), proposal,
    isPR: Boolean(issue.pull_request) }
}

async function main() {
  assert.deepEqual(triage.validate({ type: null, labels: ['docs', 'docs'] }), { type: null, labels: ['docs'] })
  for (const proposal of [null, {}, { type: 'Unknown', labels: [] },
    { type: null, labels: ['design-ready'] }, { type: null, labels: ['pr-ready'] },
    { type: null, labels: ['design-needed'] }, { type: null, labels: [null] },
    { type: null, labels: [], execute: 'shell' }]) {
    assert.throws(() => triage.validate(proposal))
  }
  assert.equal(triage.templateType('## Expected Behavior\r\n## Actual Behavior'), 'Bug')
  assert.equal(triage.templateType('## Objective\n## Completion Criteria'), 'Task')
  assert.equal(triage.templateType('## Problem Statement & Motivation\n## Proposed Scope (Goals vs. Non-Goals)'), 'Feature')
  assert.equal(triage.templateType('## Objective\n## Completion Criteria\n## Expected Behavior\n## Actual Behavior'), null)
  assert.deepEqual(triage.pathLabels([{ filename: '.github/workflows/release.yml' },
    { filename: 'site/package-lock.json' }, { filename: 'tests/test_a.py' },
    { filename: 'other', previous_filename: 'docs/codex.md' }]),
  ['ci', 'tests', 'deps', 'docs', 'site', 'harness', 'release'])

  const result = proposal => ({ ok: true, json: async () => ({ candidates: [{ finishReason: 'STOP',
    content: { parts: [{ text: JSON.stringify(proposal) }] } }] }) })
  const expected = { type: 'Bug', labels: ['harness'] }
  let calls = 0
  assert.deepEqual(await triage.classify(base, 'secret', 'gemini-2.5-flash', async (url, options) => {
    calls++
    assert.equal(new URL(url).search, '')
    assert.equal(options.headers['x-goog-api-key'], 'secret')
    const request = JSON.parse(options.body)
    assert.equal(request.tools, undefined)
    assert.equal(request.generationConfig.maxOutputTokens, 1024)
    assert.match(request.contents[0].parts[0].text, /Host install fails/)
    return result(expected)
  }), expected)
  assert.equal(calls, 1)
  await assert.rejects(triage.classify(base, '', 'gemini-2.5-flash'))
  await assert.rejects(triage.classify({ ...base, body: 'x'.repeat(20001) }, 'key', 'model'))
  await assert.rejects(triage.classify(base, 'key', '../escape'))
  await assert.rejects(triage.classify(base, 'key', 'model', async () => ({ ok: false, status: 429 })), /HTTP 429/)
  await assert.rejects(triage.classify(base, 'key', 'model', async () => { throw new Error('timeout') }), /timeout/)
  await assert.rejects(triage.classify(base, 'key', 'model', async () => ({ ok: true, json: async () => ({}) })), /incomplete/)
  await assert.rejects(triage.classify(base, 'key', 'model', async () => result({ type: null, labels: ['pr-ready'] })))

  const fresh = harness()
  await triage.publish(fresh, plan())
  assert.deepEqual(fresh.writes, [['type', 'Bug'], ['labels', ['harness']]])
  fresh.writes.length = 0
  await triage.publish(fresh, plan())
  assert.deepEqual(fresh.writes, [])

  const existing = { ...base, type: { name: 'Task' }, labels: [{ name: 'pr-ready' }] }
  const preserved = harness(existing)
  await triage.publish(preserved, plan(existing))
  assert.deepEqual(preserved.writes, [['labels', ['harness']]])

  for (const changed of [{ ...base, state: 'closed' }, { ...base, title: 'Edited' },
    { ...base, updated_at: 'later' }, { ...base, labels: [{ name: 'docs' }] }]) {
    const stale = harness(changed)
    await triage.publish(stale, plan())
    assert.deepEqual(stale.writes, [])
  }
  const human = harness(base, [{ event: 'unlabeled', label: { name: 'harness' } }, { event: 'untyped' }])
  await triage.publish(human, plan())
  assert.deepEqual(human.writes, [])
  const renamed = harness(base, [], ['docs'])
  await triage.publish(renamed, plan(base, { type: null, labels: ['harness'] }))
  assert.deepEqual(renamed.writes, [])
  const ambiguous = harness()
  await triage.publish(ambiguous, plan(base, { type: null, labels: [] }))
  assert.deepEqual(ambiguous.writes, [])

  const pr = { ...base, pull_request: {} }
  const prRun = harness(pr)
  const prepared = await triage.prepare({ ...prRun, context: { ...context, eventName: 'pull_request_target',
    payload: { pull_request: { number: base.number } } } })
  assert.deepEqual(prepared.proposal, { type: null, labels: ['site'] })
  await triage.publish(prRun, prepared)
  assert.deepEqual(prRun.writes, [['labels', ['site']]])
  await assert.rejects(triage.prepare({ ...harness({ ...base, title: 'Changed' }), context }), /changed since opening/)

  // A maintainer edits the issue between the inventory lookup and the write.
  const racing = harness()
  racing.github.request = async () => {
    racing.setIssue({ ...base, type: { name: 'Task' } })
    return { data: [{ name: 'Bug', is_enabled: true }] }
  }
  await triage.publish(racing, plan())
  assert.deepEqual(racing.writes, [])
  console.log('Metadata triage checks passed')
}

main().catch(error => { console.error(error); process.exitCode = 1 })
