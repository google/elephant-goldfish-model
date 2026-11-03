// Copyright 2026 Google LLC
// SPDX-License-Identifier: Apache-2.0

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const layout = readFileSync(new URL('../src/layouts/Base.astro', import.meta.url), 'utf8');
const source = layout.match(/<script is:inline define:vars=\{\{ gaMeasurementId, pageTitle: title \}\}>([\s\S]*?)<\/script>/)[1];

function page({ hostname = 'egm.dev', measurementId = 'G-TEST' } = {}) {
  const elements = [];
  const window = {
    location: {
      hostname,
      href: `https://${hostname}/guide?private=secret&utm_source=test#private`,
    },
  };
  const document = {
    referrer: 'https://example.com/start?private=secret#private',
    createElement: (tag) => ({ tag, dataset: {} }),
    head: {
      appendChild: (element) => {
        if (element.src?.includes('cookienotificationbar.min.js')) {
          assert.equal(typeof window.glueCookieNotificationBarLoaded, 'function');
        }
        elements.push(element);
      },
    },
  };
  vm.runInNewContext(source, {
    window, document, URL, gaMeasurementId: measurementId, pageTitle: 'EGM',
  });
  const gaScripts = () => elements.filter((element) => element.src?.includes('googletagmanager.com'));
  const commands = () => Array.from(window.dataLayer ?? [], (args) => Array.from(args));
  function loadConsent({ required = true, status = 'UNKNOWN' } = {}) {
    const listeners = [];
    const instance = { listen: (name, listener) => {
      assert.equal(name, 'statuschange');
      listeners.push(listener);
    } };
    window.glue = { CookieNotificationBar: { instance } };
    const cookieScript = elements.find(element => element.src?.includes('cookienotificationbar.min.js'));
    const layer = cookieScript.dataset.glueCookieNotificationBarCustomDataLayerName;
    window[layer] = [];
    window[layer].unshift(['consent', 'update', { analytics_storage: 'granted' }]);
    const loaded = () => window.glueCookieNotificationBarLoaded({ detail: { required, status } });
    loaded();
    return {
      loaded,
      change: next => {
        listeners.forEach(listener => listener({ detail: { status: next } }));
        window[layer].push(['consent', 'update', { analytics_storage: next === 'ACCEPTED' ? 'granted' : 'denied' }]);
      },
    };
  }
  return { window, elements, gaScripts, commands, loadConsent };
}

test('pending and rejected consent never load GA; a later affirmative choice starts it', () => {
  const p = page();
  const cookieScript = p.elements.find((element) => element.src?.includes('cookienotificationbar.min.js'));
  assert.ok(cookieScript);
  assert.equal(typeof p.window.glueCookieNotificationBarLoaded, 'function');
  assert.equal(p.gaScripts().length, 0);
  assert.equal(p.commands().some(([command]) => command === 'config'), false);

  // Loading the JS alone does not mean its asynchronous configuration is ready.
  cookieScript.onload?.();
  assert.equal(p.gaScripts().length, 0);

  const consent = p.loadConsent();
  assert.equal(p.gaScripts().length, 0);
  consent.change('REJECTED');
  p.window.gtag('event', 'should_not_send');
  assert.equal(p.gaScripts().length, 0);
  assert.equal(p.commands().some(([command]) => command === 'event'), false);
  consent.change('ACCEPTED');
  assert.equal(p.gaScripts().length, 1);
  const commands = p.commands();
  assert.ok(commands.findIndex(([command, type, value]) => command === 'consent' && type === 'update' && value.analytics_storage === 'granted')
    < commands.findIndex(([command]) => command === 'config'));
  const config = commands.find(([command]) => command === 'config')[2];
  assert.equal(config.page_location, 'https://egm.dev/guide?utm_source=test');
  assert.equal(config.page_referrer, 'https://example.com/start');
  assert.equal(config.allow_google_signals, false);
  assert.equal(config.allow_ad_personalization_signals, false);
  assert.equal(p.window['ga-disable-G-TEST'], false);
});

test('failed cookie-bar initialization never starts GA', () => {
  const p = page();
  assert.equal(p.gaScripts().length, 0);
  assert.equal(p.commands().some(([command]) => command === 'config'), false);
  assert.equal(p.commands()[0][2].analytics_storage, 'denied');
});

test('stored affirmative choice starts GA once and revocation blocks future events', () => {
  const p = page();
  const consent = p.loadConsent({ status: 'ACCEPTED' });
  consent.loaded();
  assert.equal(p.gaScripts().length, 1);
  assert.equal(p.commands().filter(([command]) => command === 'config').length, 1);
  consent.change('REJECTED');
  assert.equal(p.window['ga-disable-G-TEST'], true);
  p.window.gtag('event', 'after_revocation');
  p.window.gtag('config', 'G-TEST');
  assert.equal(p.commands().some(([command]) => command === 'event'), false);
  assert.equal(p.commands().filter(([command]) => command === 'config').length, 1);
  assert.equal(p.commands().at(-1)[2].analytics_storage, 'denied');
  consent.change('ACCEPTED');
  assert.equal(p.window['ga-disable-G-TEST'], false);
  assert.equal(p.gaScripts().length, 1);
});

for (const options of [{ status: 'REJECTED' }, { required: false, status: 'ACCEPTED' }]) {
  test(`loaded does not imply affirmative consent: ${JSON.stringify(options)}`, () => {
    const p = page();
    p.loadConsent(options);
    assert.equal(p.gaScripts().length, 0);
    assert.equal(p.window['ga-disable-G-TEST'], true);
  });
}

test('loaded callback without valid vendor details fails closed', () => {
  const p = page();
  p.window.glueCookieNotificationBarLoaded();
  p.window.glueCookieNotificationBarLoaded({ detail: { required: true, status: 'ACCEPTED' } });
  assert.equal(p.gaScripts().length, 0);
});

for (const options of [{ hostname: 'localhost' }, { hostname: 'preview.example.com' }, { measurementId: '' }]) {
  test(`no Google resources outside the configured canonical site: ${JSON.stringify(options)}`, () => {
    const p = page(options);
    assert.equal(p.elements.length, 0);
    assert.equal(p.window.glueCookieNotificationBarLoaded, undefined);
    assert.equal(p.window.dataLayer, undefined);
  });
}
