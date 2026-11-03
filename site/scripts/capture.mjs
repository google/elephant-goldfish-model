// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// Regenerates every committed site image: public/og.png and screenshots/*.png.
// Usage: npm run capture   (builds first, then serves dist/ and drives Chrome).
// Uses puppeteer-core with the installed Chrome; set CHROME_PATH if it is not found.

import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import puppeteer from 'puppeteer-core';

const site = fileURLToPath(new URL('..', import.meta.url));
const dist = join(site, 'dist');
const types = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2' };

// Serves dist/ so the built page's absolute /_astro/* asset paths resolve.
const server = createServer(async (req, res) => {
  const path = normalize(decodeURIComponent(new URL(req.url, 'http://x').pathname));
  const file = join(dist, path.endsWith('/') ? `${path}index.html` : path);
  try {
    const body = await readFile(file);
    res.writeHead(200, { 'content-type': types[extname(file)] ?? 'application/octet-stream' });
    res.end(body);
  } catch {
    res.writeHead(404).end();
  }
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const base = `http://127.0.0.1:${server.address().port}`;

// channel: 'chrome' finds the installed Chrome on Linux, macOS, and Windows; CHROME_PATH overrides it.
const browser = await puppeteer.launch({ channel: 'chrome', executablePath: process.env.CHROME_PATH, args: ['--no-sandbox'] });

async function capture({ url, out, width, height, scheme = 'light', fullPage = false, scale = 1 }) {
  const page = await browser.newPage();
  await page.setViewport({ width, height, deviceScaleFactor: scale });
  await page.emulateMediaFeatures([{ name: 'prefers-color-scheme', value: scheme }]);
  await page.goto(url, { waitUntil: 'networkidle0' });
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: join(site, out), fullPage });
  await page.close();
  console.log(`wrote ${out}`);
}

try {
  await capture({ url: pathToFileURL(join(site, 'scripts/og.html')).href, out: 'public/og.png', width: 1200, height: 630, scale: 2 });
  await capture({ url: `${base}/`, out: 'screenshots/hero-light.png', width: 1200, height: 600 });
  await capture({ url: `${base}/`, out: 'screenshots/hero-dark.png', width: 1200, height: 600, scheme: 'dark' });
  await capture({ url: `${base}/`, out: 'screenshots/full-light.png', width: 1000, height: 800, fullPage: true });
  await capture({ url: `${base}/`, out: 'screenshots/full-dark.png', width: 1000, height: 800, scheme: 'dark', fullPage: true });
  await capture({ url: `${base}/`, out: 'screenshots/mobile.png', width: 375, height: 812, fullPage: true });
  await capture({ url: `${base}/`, out: 'screenshots/mobile-dark.png', width: 375, height: 812, scheme: 'dark', fullPage: true });
} finally {
  await browser.close();
  server.close();
}
