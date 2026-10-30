// Copyright 2026 Google LLC
// SPDX-License-Identifier: Apache-2.0

// Verify built HTML with controlled Google script responses, without telemetry.
// Build once without an ID and save its HTML, then build with G-TEST:
// npm run test:browser -- /path/to/disabled-build.html
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import puppeteer from 'puppeteer-core';

const enabled = await readFile(new URL('../dist/index.html', import.meta.url), 'utf8');
assert.ok(process.argv[2], 'Pass the HTML from the build without an analytics ID');
const disabled = await readFile(process.argv[2], 'utf8');
const browser = await puppeteer.launch({ channel: 'chrome', executablePath: process.env.CHROME_PATH });
const results = [];

async function visit(host, { failed = false, html = enabled } = {}) {
  const page = await browser.newPage();
  const requests = [];
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.setRequestInterception(true);
  page.on('request', request => {
    const url = new URL(request.url());
    let body = '';
    let contentType = 'text/plain';
    if (url.hostname === 'www.gstatic.com' || url.hostname === 'www.googletagmanager.com') {
      requests.push(request.url());
      if (url.pathname.endsWith('cookienotificationbar.min.js')) {
        if (failed) return void request.abort('failed');
        contentType = 'application/javascript';
        body = `window.__cookieScriptLoaded = true;
          const layer = document.currentScript.dataset.glueCookieNotificationBarCustomDataLayerName;
          const listeners = [];
          window.glue = { CookieNotificationBar: { instance: {
            listen: (name, listener) => { if (name === 'statuschange') listeners.push(listener); }
          } } };
          window.__finishConsent = (status = 'UNKNOWN', required = true) => {
            window[layer] = window[layer] || [];
            window[layer].unshift(['consent', 'update', { analytics_storage: 'granted' }]);
            window.glueCookieNotificationBarLoaded({ detail: { required, status } });
          };
          window.__changeConsent = status => {
            listeners.forEach(listener => listener({ detail: { status } }));
            window[layer].push(['consent', 'update', { analytics_storage: status === 'ACCEPTED' ? 'granted' : 'denied' }]);
          };`;
      } else if (url.hostname === 'www.googletagmanager.com') {
        contentType = 'application/javascript';
        body = `window.__gaCommands = [];
          window.__disabledAtDenial = [];
          const processCommand = args => {
            window.__gaCommands.push(Array.from(args));
            if (args[0] === 'consent' && args[2].analytics_storage === 'denied') {
              window.__disabledAtDenial.push(window['ga-disable-G-TEST']);
            }
            if (['event', 'config'].includes(args[0]) && !window['ga-disable-G-TEST']) {
              fetch('https://www.google-analytics.com/g/collect?event=' + args[0]);
            }
          };
          window.dataLayer.forEach(processCommand);
          const push = window.dataLayer.push.bind(window.dataLayer);
          window.dataLayer.push = (...commands) => { commands.forEach(processCommand); return push(...commands); };`;
      } else {
        contentType = 'text/css';
      }
    } else if (url.hostname === 'www.google-analytics.com') {
      requests.push(request.url());
    } else if (request.isNavigationRequest() && request.frame() === page.mainFrame()) {
      contentType = 'text/html';
      body = html;
    }
    // Respond to every request; nothing reaches Google or another network host.
    void request.respond({ status: 200, contentType, headers: { 'access-control-allow-origin': '*' }, body });
  });
  await page.goto(`https://${host}/?private=secret&utm_source=test#private`, { waitUntil: 'load' });
  const gaRequests = () => requests.filter(url => new URL(url).hostname === 'www.googletagmanager.com');
  const collects = () => requests.filter(url => new URL(url).hostname === 'www.google-analytics.com');
  return { page, requests, gaRequests, collects, errors };
}

try {
  const delayed = await visit('egm.dev');
  assert.equal(await delayed.page.evaluate(() => window.__cookieScriptLoaded), true);
  assert.equal(delayed.gaRequests().length, 0, 'GA must not load before asynchronous configuration completes');
  assert.equal(await delayed.page.evaluate(() => window.dataLayer.some(args => args[0] === 'config')), false);
  await delayed.page.evaluate(() => window.__finishConsent());
  assert.equal(delayed.gaRequests().length, 0, 'pending consent must not load GA');
  await delayed.page.evaluate(() => window.__changeConsent('REJECTED'));
  assert.equal(delayed.gaRequests().length, 0, 'rejected consent must not load GA');
  assert.equal(delayed.collects().length, 0);
  await delayed.page.evaluate(() => window.__changeConsent('ACCEPTED'));
  await delayed.page.waitForFunction(() => window.__gaCommands !== undefined);
  await delayed.page.waitForFunction(() => window.__gaCommands.some(args => args[0] === 'config'));
  assert.equal(delayed.gaRequests().length, 1);
  const config = await delayed.page.evaluate(() => window.__gaCommands.find(args => args[0] === 'config')[2]);
  assert.equal(config.page_location, 'https://egm.dev/?utm_source=test');
  assert.equal(config.allow_google_signals, false);
  assert.equal(config.allow_ad_personalization_signals, false);
  await delayed.page.waitForNetworkIdle();
  assert.equal(delayed.collects().length, 1, 'grant must permit the initial measurement');
  results.push({ case: 'pending, rejected, then granted', pass: true, requests: [...delayed.requests] });

  await delayed.page.evaluate(() => {
    window.gtag('event', 'positive_control');
  });
  await delayed.page.waitForNetworkIdle();
  assert.equal(delayed.collects().length, 2, 'event fixture must send before revocation');
  await delayed.page.evaluate(() => {
    window.__changeConsent('REJECTED');
    window.gtag('event', 'after_revocation');
    window.gtag('config', 'G-TEST');
  });
  await delayed.page.waitForNetworkIdle();
  assert.equal(delayed.collects().length, 2, 'revocation must prevent later measurements');
  assert.equal(await delayed.page.evaluate(() => window['ga-disable-G-TEST']), true);
  assert.equal(await delayed.page.evaluate(() => window.__disabledAtDenial.at(-1)), true);
  results.push({ case: 'revocation blocks future measurements', pass: true });

  await delayed.page.evaluate(() => { window.__finishConsent(); window.__finishConsent(); });
  assert.equal(await delayed.page.evaluate(() => document.querySelectorAll('script[src*="googletagmanager.com"]').length), 1);
  assert.equal(await delayed.page.evaluate(() => window.dataLayer.filter(args => args[0] === 'config').length), 1);
  assert.deepEqual(delayed.errors, []);
  results.push({ case: 'repeated callbacks', pass: true });
  await delayed.page.close();

  for (const [status, required] of [['REJECTED', true], ['ACCEPTED', false], ['ACCEPTED', true]]) {
    const initial = await visit('egm.dev');
    await initial.page.evaluate((state, needed) => window.__finishConsent(state, needed), status, required);
    await initial.page.waitForNetworkIdle();
    const granted = status === 'ACCEPTED' && required;
    assert.equal(initial.gaRequests().length, granted ? 1 : 0);
    assert.equal(initial.collects().length, granted ? 1 : 0);
    assert.deepEqual(initial.errors, []);
    results.push({ case: `initial ${status}, required=${required}`, pass: true });
    await initial.page.close();
  }

  const failure = await visit('egm.dev', { failed: true });
  assert.equal(failure.gaRequests().length, 0);
  assert.equal(await failure.page.evaluate(() => window.dataLayer.some(args => args[0] === 'config')), false);
  assert.deepEqual(failure.errors, []);
  results.push({ case: 'cookie script failure', pass: true });
  await failure.page.close();

  for (const [host, html] of [['preview.example.com', enabled], ['localhost', enabled], ['egm.dev', disabled]]) {
    const gated = await visit(host, { html });
    assert.equal(gated.requests.length, 0);
    assert.equal(await gated.page.evaluate(() => window.dataLayer === undefined), true);
    assert.deepEqual(gated.errors, []);
    results.push({ case: host === 'egm.dev' ? 'measurement ID unset' : `noncanonical ${host}`, pass: true });
    await gated.page.close();
  }
  console.log(JSON.stringify({ browser: await browser.version(), googleResponses: 'intercepted fixtures; no live vendor verification', results }, null, 2));
} finally {
  await browser.close();
}
