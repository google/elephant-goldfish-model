// Run one request per build. A GitHub outage must not block the documentation.
export const githubStars = fetch('https://api.github.com/repos/google/elephant-goldfish-model', {
  headers: {
    Accept: 'application/vnd.github+json',
    ...(process.env.GITHUB_TOKEN ? { Authorization: `Bearer ${process.env.GITHUB_TOKEN}` } : {}),
  },
  signal: AbortSignal.timeout(5000),
}).then(async response => {
  if (!response.ok) return null;
  const data = await response.json();
  return Number.isSafeInteger(data.stargazers_count) && data.stargazers_count >= 0 ? data.stargazers_count as number : null;
}).catch(() => null);
