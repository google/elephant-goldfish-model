// Copyright 2026 Google LLC.
// SPDX-License-Identifier: Apache-2.0

const assert = require('node:assert/strict')
const { mkdtempSync, readFileSync, rmSync, writeFileSync } = require('node:fs')
const { tmpdir } = require('node:os')
const { join } = require('node:path')
const { test } = require('node:test')

const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
const scriptBody = readFileSync(0, 'utf8')
const executePost = new AsyncFunction(
  'github',
  'context',
  'core',
  'require',
  'getOctokit',
  scriptBody,
)

function createHarness(overrides = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'egm-post-test-'))
  const planPath = join(dir, 'review-plan.json')
  const state = {
    reviews: [],
    labels: new Set(overrides.initialLabels || []),
    requestedTeams: [],
    warnings: [],
    infos: [],
    failed: null,
    prState: overrides.prState || 'open',
    prHeadSha: overrides.prHeadSha || 'abc12345',
    rejectInline422: Boolean(overrides.rejectInline422),
    rejectTeam422: Boolean(overrides.rejectTeam422),
    rejectPrimary401: Boolean(overrides.rejectPrimary401),
    usedFallbackClient: false,
  }

  const makeClient = isPrimary => ({
    rest: {
      pulls: {
        get: async () => {
          if (isPrimary && state.rejectPrimary401) {
            throw Object.assign(new Error('Bad credentials'), { status: 401 })
          }
          return {
            data: { state: state.prState, head: { sha: state.prHeadSha } },
          }
        },
        createReview: async req => {
          if (state.rejectInline422 && req.comments && req.comments.length > 0) {
            throw Object.assign(new Error('Unprocessable Entity'), { status: 422 })
          }
          state.reviews.push(req)
        },
        requestReviewers: async ({ team_reviewers }) => {
          if (state.rejectTeam422 || !isPrimary) {
            throw Object.assign(
              new Error('Could not resolve to a node with the global id'),
              { status: 422 },
            )
          }
          state.requestedTeams.push(...team_reviewers)
        },
      },
      issues: {
        addLabels: async ({ labels }) => labels.forEach(l => state.labels.add(l)),
        removeLabel: async ({ name }) => {
          if (!state.labels.delete(name)) {
            throw Object.assign(new Error('Not Found'), { status: 404 })
          }
        },
      },
    },
  })

  const github = makeClient(true)
  const getOctokit = token => {
    assert.equal(token, 'fallback-gh-token')
    state.usedFallbackClient = true
    return makeClient(false)
  }

  const core = {
    info: msg => state.infos.push(msg),
    warning: msg => state.warnings.push(msg),
    setFailed: msg => {
      state.failed = msg
    },
  }

  state.run = async (plan, allowedTeam = 'egm-maintainers') => {
    writeFileSync(planPath, JSON.stringify(plan), 'utf8')
    const prevPlan = process.env.PLAN_PATH
    const prevTeam = process.env.ALLOWED_TEAM
    const prevFallback = process.env.FALLBACK_TOKEN
    process.env.PLAN_PATH = planPath
    process.env.ALLOWED_TEAM = allowedTeam
    process.env.FALLBACK_TOKEN = 'fallback-gh-token'
    try {
      await executePost(
        github,
        { repo: { owner: 'google', repo: 'elephant-goldfish-model' } },
        core,
        require,
        getOctokit,
      )
    } finally {
      if (prevPlan === undefined) delete process.env.PLAN_PATH
      else process.env.PLAN_PATH = prevPlan
      if (prevTeam === undefined) delete process.env.ALLOWED_TEAM
      else process.env.ALLOWED_TEAM = prevTeam
      if (prevFallback === undefined) delete process.env.FALLBACK_TOKEN
      else process.env.FALLBACK_TOKEN = prevFallback
      rmSync(dir, { recursive: true, force: true })
    }
  }

  return state
}

test('clean_handoff posts review, adds triage: passed, and degrades gracefully on 422 team lookup', async () => {
  const state = createHarness({ rejectTeam422: true })
  await state.run({
    action: 'clean_handoff',
    pr_number: 42,
    head_sha: 'abc12345',
    add_labels: ['triage: passed', 'unauthorized-label'],
    remove_labels: [],
    team_reviewers: ['egm-maintainers', 'unauthorized-team'],
    review_payload: {
      commit_id: 'abc12345',
      body: '<!-- egm-triage-review:sha=abc12345 -->\nClean pass.',
      comments: [],
    },
  })
  assert.equal(state.failed, null)
  assert.equal(state.reviews.length, 1)
  assert.deepEqual([...state.labels], ['triage: passed'])
  assert.equal(state.warnings.length, 1)
  assert.match(state.warnings[0], /EGM_TRIAGE_BOT_TOKEN/)
})

test('post_findings retries 422 inline anchors with indented plain code blocks and removes stale label', async () => {
  const state = createHarness({
    rejectInline422: true,
    initialLabels: ['triage: passed', 'ci'],
  })
  await state.run({
    action: 'post_findings',
    pr_number: 42,
    head_sha: 'abc12345',
    add_labels: [],
    remove_labels: ['triage: passed'],
    team_reviewers: [],
    review_payload: {
      commit_id: 'abc12345',
      body: '<!-- egm-triage-review:sha=abc12345 -->',
      comments: [
        {
          path: 'scripts/check.py',
          line: 14,
          side: 'RIGHT',
          body: '**[Blocker]**: Missing guard.\n\n```suggestion\nif ok:\n  run()\n```',
        },
      ],
    },
  })
  assert.equal(state.failed, null)
  assert.equal(state.reviews.length, 1)
  assert.deepEqual(state.reviews[0].comments, [])
  assert.match(state.reviews[0].body, /- `scripts\/check\.py:14` \*\*\[Blocker\]\*\*/)
  assert.doesNotMatch(state.reviews[0].body, /```suggestion/)
  assert.deepEqual([...state.labels], ['ci'])
})

test('stale head_sha or closed PR skips all mutations', async () => {
  const stale = createHarness({ prHeadSha: 'newsha999' })
  await stale.run({
    action: 'clean_handoff',
    pr_number: 42,
    head_sha: 'abc12345',
    add_labels: ['triage: passed'],
    remove_labels: [],
    team_reviewers: ['egm-maintainers'],
    review_payload: { body: 'Clean' },
  })
  assert.equal(stale.reviews.length, 0)
  assert.equal(stale.labels.size, 0)
})

test('expired EGM_TRIAGE_BOT_TOKEN (HTTP 401) falls back to GITHUB_TOKEN via getOctokit', async () => {
  const state = createHarness({ rejectPrimary401: true })
  await state.run({
    action: 'clean_handoff',
    pr_number: 42,
    head_sha: 'abc12345',
    add_labels: ['triage: passed'],
    remove_labels: [],
    team_reviewers: ['egm-maintainers'],
    review_payload: {
      commit_id: 'abc12345',
      body: '<!-- egm-triage-review:sha=abc12345 -->\nClean pass.',
      comments: [],
    },
  })
  assert.equal(state.failed, null)
  assert.equal(state.usedFallbackClient, true)
  assert.equal(state.reviews.length, 1)
  assert.deepEqual([...state.labels], ['triage: passed'])
  assert.ok(state.warnings.some(msg => /HTTP 401/.test(msg)))
})
