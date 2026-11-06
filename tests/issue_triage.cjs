// Copyright 2026 Google LLC.
// SPDX-License-Identifier: Apache-2.0

const assert = require('node:assert/strict')
const { readFileSync } = require('node:fs')
const { test } = require('node:test')

const AsyncFunction = Object.getPrototypeOf(async function () { }).constructor
const evaluate = new AsyncFunction('github', 'context', 'core', readFileSync(0, 'utf8'))

const DEFAULT_TYPES = [
    { id: 'IT_bug', name: 'Bug' },
    { id: 'IT_feature', name: 'Feature' },
    { id: 'IT_task', name: 'Task' },
]

const DEFAULT_REPO_LABELS = [
    'ci',
    'tests',
    'deps',
    'docs',
    'site',
    'harness',
    'isolation',
    'release',
    'design-ready',
    'pr-ready',
    'design-needed',
    'advisory: design-doc-suggested',
]

function fixture() {
    const state = {
        title: '',
        body: '',
        issueType: null,
        labels: new Set(),
        repoIssueTypes: [...DEFAULT_TYPES],
        repoLabels: new Set(DEFAULT_REPO_LABELS),
        timeline: [],
        mutations: [],
        addLabelsCalls: [],
    }

    const github = {
        graphql: async (query, variables) => {
            if (query.includes('mutation')) {
                state.mutations.push(variables)
                const matched = state.repoIssueTypes.find(t => t.id === variables.issueTypeId)
                assert.ok(matched, `Unknown issueTypeId: ${variables.issueTypeId}`)
                state.issueType = { id: matched.id, name: matched.name }
                return { updateIssue: { issue: { id: variables.issueId } } }
            }
            return {
                repository: {
                    issueTypes: { nodes: state.repoIssueTypes },
                    labels: { nodes: [...state.repoLabels].map(name => ({ name })) },
                    issue: {
                        id: 'I_1',
                        title: state.title,
                        body: state.body,
                        issueType: state.issueType,
                        labels: { nodes: [...state.labels].map(name => ({ name })) },
                        timelineItems: { nodes: state.timeline },
                    },
                },
            }
        },
        rest: {
            issues: {
                addLabels: async ({ labels }) => {
                    state.addLabelsCalls.push(labels)
                    labels.forEach(l => state.labels.add(l))
                },
            },
        },
    }

    state.run = async (extraIssuePayload = {}) => {
        await evaluate(
            github,
            {
                repo: { owner: 'google', repo: 'elephant-goldfish-model' },
                payload: {
                    action: 'opened',
                    issue: {
                        number: 328,
                        title: state.title,
                        body: state.body,
                        ...extraIssuePayload,
                    },
                },
            },
            { setFailed: message => assert.fail(message), info: () => { } }
        )
    }

    return state
}

test('untyped host installation regression receives Bug and harness', async () => {
    const state = fixture()
    state.title = 'EGM fails to install in Claude Cowork'
    state.body = 'Host installation regression when installing the plugin.'
    await state.run()
    assert.equal(state.issueType?.name, 'Bug')
    assert.deepEqual([...state.labels], ['harness'])
})

test('documentation-only task receives Task and docs, and repeated runs are idempotent', async () => {
    const state = fixture()
    state.title = 'Correct an outdated installation command'
    state.body = readFileSync(`${__dirname}/../.github/ISSUE_TEMPLATE/task.md`, 'utf8')
        .replace('<!-- Describe the work and why it is needed. Use the Feature / Architectural Inquiry template for new features or architectural changes. -->', 'Update README.md installation command examples.')
    await state.run()
    assert.equal(state.issueType?.name, 'Task')
    assert.deepEqual([...state.labels], ['docs'])
    assert.equal(state.mutations.length, 1)
    assert.equal(state.addLabelsCalls.length, 1)

    // Repeated run produces no duplicate mutations or label calls
    await state.run()
    assert.equal(state.mutations.length, 1)
    assert.equal(state.addLabelsCalls.length, 1)
    assert.equal(state.issueType?.name, 'Task')
    assert.deepEqual([...state.labels], ['docs'])
})

test('issue template takes precedence over conflicting keywords in body', async () => {
    const state = fixture()
    state.title = 'Align on new workflow for broken links'
    state.body = readFileSync(`${__dirname}/../.github/ISSUE_TEMPLATE/feature_proposal.md`, 'utf8')
    await state.run()
    assert.equal(state.issueType?.name, 'Feature')
})

test('preserves existing issue type and existing labels while adding missing topical labels', async () => {
    const state = fixture()
    state.issueType = { id: 'IT_task', name: 'Task' }
    state.labels.add('design-ready')
    state.title = 'A required Actions job fails because its token lacks permissions'
    state.body = 'Workflow fails in CI.'
    await state.run()
    assert.equal(state.issueType?.name, 'Task')
    assert.equal(state.mutations.length, 0)
    assert.deepEqual([...state.labels], ['design-ready', 'ci'])
})

test('leaves ambiguous issues untyped and unlabeled', async () => {
    const state = fixture()
    state.title = 'Question about phase handoffs'
    state.body = 'How do maintainers think about general workflow ergonomics?'
    await state.run()
    assert.equal(state.issueType, null)
    assert.deepEqual([...state.labels], [])
})

test('retried run respects human label removal and human cleared issue type', async () => {
    const state = fixture()
    state.title = 'EGM fails to install in Claude Cowork'
    state.body = 'Host installation regression.'
    state.timeline = [
        { __typename: 'IssueTypeRemovedEvent', actor: { login: 'n3wth' } },
        { __typename: 'UnlabeledEvent', actor: { login: 'n3wth' }, label: { name: 'harness' } },
    ]
    await state.run()
    assert.equal(state.issueType, null)
    assert.deepEqual([...state.labels], [])
})

test('skips labels that have been renamed or removed from the repository', async () => {
    const state = fixture()
    state.repoLabels.delete('site')
    state.title = 'The guide sidebar is broken on mobile on egm.dev'
    state.body = 'Website navigation fails.'
    await state.run()
    assert.equal(state.issueType?.name, 'Bug')
    assert.deepEqual([...state.labels], [])
})

test('never applies approval or legacy advisory labels', async () => {
    const state = fixture()
    state.title = 'Need design-ready, pr-ready, design-needed, and advisory: design-doc-suggested'
    state.body = 'Update a pinned dependency with a known vulnerability.'
    await state.run()
    assert.deepEqual([...state.labels], ['deps'])
})

test('classifies all 8 allowlisted topical domains accurately', async () => {
    const cases = [
        ['ci', 'A required Actions job fails because its token lacks permissions'],
        ['tests', 'Add a regression test for interrupted reviews'],
        ['deps', 'Update a pinned dependency with a known vulnerability'],
        ['docs', 'Correct an outdated installation command in documentation'],
        ['site', 'The guide sidebar is broken on mobile on egm.dev'],
        ['harness', 'EGM fails to install in Claude Cowork'],
        ['isolation', 'A reviewer receives the drafting conversation causing instruction leakage'],
        ['release', 'A published plugin bundle is missing its manifest'],
    ]
    for (const [expectedLabel, sampleText] of cases) {
        const state = fixture()
        state.title = sampleText
        await state.run()
        assert.ok(
            state.labels.has(expectedLabel),
            `Expected "${sampleText}" to receive label "${expectedLabel}", got: ${[...state.labels]}`
        )
    }
})