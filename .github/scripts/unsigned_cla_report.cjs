// Copyright 2026 Google LLC. SPDX-License-Identifier: Apache-2.0

const DAY = 86_400_000;

function classify({ notice, authorActivity, firstHeadCheck, exempt, now }) {
  const age = now - Date.parse(notice);
  if (!(age >= 7 * DAY)) return null;
  if (exempt) return 'Exempt (keep-open)';
  if (authorActivity.some(date => Date.parse(date) >= Date.parse(notice))) {
    return 'Author replied';
  }
  if (!firstHeadCheck || Date.parse(firstHeadCheck) >= Date.parse(notice)) {
    return 'Head updated or push timing uncertain';
  }
  return age >= 14 * DAY ? 'Would close' : 'Would remind';
}

async function report(github, repo, core) {
  const { pulls, issues, checks } = github.rest;
  const rows = [];
  const now = Date.now();
  for await (const page of github.paginate.iterator(pulls.list, {
    ...repo, state: 'open', per_page: 100,
  })) {
    for (const pr of page.data) {
      const issue = { ...repo, issue_number: pr.number, per_page: 100 };
      const pull = { ...repo, pull_number: pr.number, per_page: 100 };
      const runs = await github.paginate(checks.listForRef, {
        ...repo, ref: pr.head.sha, filter: 'all', per_page: 100,
      });
      const cla = runs.filter(run => run.name === 'cla/google' && run.app?.slug === 'google-cla')
        .sort((a, b) => b.id - a.id)[0];
      if (cla?.conclusion !== 'failure') continue;

      const comments = await github.paginate(issues.listComments, issue);
      const notice = comments.find(comment => comment.user?.login === 'google-cla[bot]' ||
        (comment.user?.login === 'google-cla' && comment.user?.type === 'Bot'));
      if (!notice || now - Date.parse(notice.created_at) < 7 * DAY) continue;
      const [inline, reviews, events] = await Promise.all([
        github.paginate(pulls.listReviewComments, pull),
        github.paginate(pulls.listReviews, pull),
        github.paginate(issues.listEventsForTimeline, issue),
      ]);
      const authorActivity = [...comments, ...inline, ...reviews]
        .filter(entry => entry.user?.login === pr.user?.login && entry.body?.trim())
        .map(entry => entry.submitted_at || entry.created_at);
      const firstHeadCheck = runs.map(run => run.started_at).filter(Boolean).sort()[0];
      const recentForcePush = events.some(event =>
        event.event === 'head_ref_force_pushed' &&
        Date.parse(event.created_at) >= Date.parse(notice.created_at));
      const outcome = classify({
        notice: notice.created_at,
        authorActivity,
        firstHeadCheck: recentForcePush ? undefined : firstHeadCheck,
        exempt: pr.labels.some(label => label.name === 'keep-open'),
        now,
      });
      if (outcome) rows.push([`#${pr.number}`, notice.created_at.slice(0, 10), outcome]);
    }
  }

  await core.summary.addHeading('Unsigned CLA report')
    .addRaw('Report only. Apply `keep-open` to exempt a PR.', true)
    .addList(rows.length ? rows.map(row => row.join(' | ')) : ['No PRs matched.'])
    .write();
}

module.exports = { classify, report };
