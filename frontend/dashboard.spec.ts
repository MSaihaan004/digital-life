import { test, expect } from '@playwright/test';

const API = 'http://127.0.0.1:8000';

async function apiLabel(page, method: string, path: string, body?: unknown) {
  return page.evaluate(
    async ({ method, url, body }) => {
      const response = await fetch(url, {
        method,
        headers: body ? { 'Content-Type': 'application/json' } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      });
      return { status: response.status, json: await response.json().catch(() => null) };
    },
    { method, url: `${API}${path}`, body: body ?? null },
  );
}

test.beforeEach(async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(String(error)));
  (page as unknown as { __errors: string[] }).__errors = errors;
  await page.goto('/index.html');
  await expect(page.locator('#ecosystem-canvas')).toBeVisible();
  /* Backend control state is shared: always start paused + reset. */
  await apiLabel(page, 'POST', '/simulation/pause');
  await apiLabel(page, 'POST', '/simulation/reset', {});
  await page.reload();
  await expect(page.locator('#ecosystem-canvas')).toBeVisible();
});

test('dashboard loads and connects', async ({ page }) => {
  await expect(page.locator('#simulation-tick')).not.toHaveText('—', { timeout: 15000 });
  await expect(page.locator('#living-population')).not.toHaveText('—', { timeout: 15000 });
  await expect(page.locator('#connection-text')).toContainText('Backend connected', { timeout: 15000 });
  await expect(page.locator('#simulation-status')).not.toHaveText('—', { timeout: 15000 });
});

test('no browser console errors on load', async ({ page }) => {
  const messages: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') messages.push(message.text());
  });
  await page.reload();
  await expect(page.locator('#simulation-tick')).not.toHaveText('—', { timeout: 15000 });
  await page.waitForTimeout(2500);
  expect(messages).toEqual([]);
});

test('pause shows paused status; resume restores running', async ({ page }) => {
  await expect(page.locator('#simulation-tick')).not.toHaveText('—', { timeout: 15000 });
  await page.click('#pause-button');
  await expect(page.locator('#control-status')).toContainText('paused', { timeout: 10000 });
  await expect(page.locator('#simulation-status')).toHaveText('Paused', { timeout: 10000 });
  const tickText = await page.locator('#simulation-tick').textContent();
  await page.waitForTimeout(2500);
  /* Paused: the worker must not advance the tick on its own. */
  await expect(page.locator('#simulation-tick')).toHaveText(tickText ?? '', { timeout: 5000 });
  await page.click('#resume-button');
  await expect(page.locator('#simulation-status')).toHaveText('Running', { timeout: 15000 });
});

test('single-step advances exactly one tick while paused', async ({ page }) => {
  await expect(page.locator('#simulation-tick')).not.toHaveText('—', { timeout: 15000 });
  await page.click('#pause-button');
  await expect(page.locator('#simulation-status')).toHaveText('Paused', { timeout: 10000 });
  const before = Number((await page.locator('#simulation-tick').textContent())?.replace(/,/g, ''));
  await page.click('#step-button');
  await expect(page.locator('#control-status')).toContainText('one tick', { timeout: 10000 });
  await expect(async () => {
    const after = Number((await page.locator('#simulation-tick').textContent())?.replace(/,/g, ''));
    expect(after).toBe(before + 1);
  }).toPass({ timeout: 10000 });
});

test('single-step while running explains the pause requirement', async ({ page }) => {
  await expect(page.locator('#simulation-tick')).not.toHaveText('—', { timeout: 15000 });
  await page.click('#resume-button');
  await expect(page.locator('#simulation-status')).toHaveText('Running', { timeout: 15000 });
  await page.click('#step-button');
  await expect(page.locator('#control-error')).toContainText('Pause first', { timeout: 10000 });
});

test('reset recreates the initial state', async ({ page }) => {
  await expect(page.locator('#simulation-tick')).not.toHaveText('—', { timeout: 15000 });
  await page.click('#pause-button');
  await expect(page.locator('#simulation-status')).toHaveText('Paused', { timeout: 10000 });
  await page.click('#reset-button');
  await expect(page.locator('#control-status')).toContainText('reset', { timeout: 10000 });
  await expect(page.locator('#simulation-tick')).toHaveText('0', { timeout: 10000 });
  await expect(page.locator('#living-population')).not.toHaveText('—', { timeout: 10000 });
});

test('population statistics render', async ({ page }) => {
  await expect(page.locator('#simulation-tick')).not.toHaveText('—', { timeout: 15000 });
  await expect(page.locator('#living-population')).not.toHaveText('—', { timeout: 15000 });
  await expect(page.locator('#total-organisms')).not.toHaveText('—', { timeout: 15000 });
  await expect(page.locator('#food-remaining')).not.toHaveText('—', { timeout: 15000 });
  const living = await page.locator('#living-population').textContent();
  const total = await page.locator('#total-organisms').textContent();
  expect(Number(living?.replace(/,/g, ''))).toBeGreaterThanOrEqual(0);
  expect(Number(total?.replace(/,/g, ''))).toBeGreaterThanOrEqual(0);
});

test('organism selection updates the inspector', async ({ page }) => {
  await expect(page.locator('#simulation-tick')).not.toHaveText('—', { timeout: 15000 });
  await page.click('#pause-button');
  await expect(page.locator('#simulation-status')).toHaveText('Paused', { timeout: 10000 });
  const picked = await page.evaluate(async () => {
    const response = await fetch('http://127.0.0.1:8000/simulation/state?limit=5');
    const state = await response.json();
    const organism = (state.organisms as Array<{ x: number; y: number }>)[0];
    return organism ? { x: organism.x, y: organism.y } : null;
  });
  expect(picked).not.toBeNull();
  const box = await page.locator('#ecosystem-canvas').boundingBox();
  expect(box).not.toBeNull();
  /* The earlier pause-button click may have scrolled the canvas
     out of view; re-anchor it so coordinates are viewport-valid. */
  await page.locator('#ecosystem-canvas').scrollIntoViewIfNeeded();
  const freshBox = await page.locator('#ecosystem-canvas').boundingBox();
  const world = await page.evaluate(async () => {
    const response = await fetch('http://127.0.0.1:8000/simulation/state?limit=1');
    const state = await response.json();
    return state.world as { width: number; height: number };
  });
  const clickX = (freshBox as { x: number; width: number }).x
    + ((picked as { x: number }).x / world.width) * (freshBox as { width: number }).width;
  const clickY = (freshBox as { y: number; height: number }).y
    + ((picked as { y: number }).y / world.height) * (freshBox as { height: number }).height;
  await page.mouse.click(clickX, clickY);
  await expect(page.locator('#inspector-details')).toBeVisible({ timeout: 10000 });
  await expect(page.locator('#selected-organism-id')).toContainText('Organism #');
  await expect(page.locator('#organism-status')).not.toHaveText('—', { timeout: 5000 });
  await expect(page.locator('#organism-energy')).not.toHaveText('—', { timeout: 5000 });
});

test('rendering-style selection persists', async ({ page }) => {
  await expect(page.locator('#simulation-tick')).not.toHaveText('—', { timeout: 15000 });
  /* The sprite selector lives in the settings dropdown. */
  await page.click('#settings-toggle');
  await expect(page.locator('#settings-panel')).toBeVisible();
  await page.selectOption('#sprite-style-select', 'dots');
  await expect(page.locator('body')).toHaveAttribute('data-sprite-style', 'dots');
  await expect(page.locator('#sprite-style-hint')).not.toHaveText('', { timeout: 5000 });
  await page.selectOption('#sprite-style-select', 'pixel');
  await expect(page.locator('body')).toHaveAttribute('data-sprite-style', 'pixel');
});

test('analytics charts render from backend metrics', async ({ page }) => {
  await expect(page.locator('#simulation-tick')).not.toHaveText('—', { timeout: 15000 });
  await page.click('#pause-button');
  await expect(page.locator('#simulation-status')).toHaveText('Paused', { timeout: 10000 });
  /* Generate a few recorded ticks, then wait for the chart poll. */
  await apiLabel(page, 'POST', '/simulation/step');
  await apiLabel(page, 'POST', '/simulation/step');
  await apiLabel(page, 'POST', '/simulation/step');
  await expect(page.locator('#analytics-status')).toContainText('recorded tick', { timeout: 20000 });
  for (const id of ['#chart-population', '#chart-vitality', '#chart-energy', '#chart-trait']) {
    await expect(page.locator(id)).toBeVisible();
  }
});

test('responsive layout keeps controls reachable', async ({ page }) => {
  await page.setViewportSize({ width: 480, height: 900 });
  await expect(page.locator('#simulation-tick')).not.toHaveText('—', { timeout: 15000 });
  await expect(page.locator('#pause-button')).toBeVisible();
  await expect(page.locator('#step-button')).toBeVisible();
  await expect(page.locator('#reset-button')).toBeVisible();
  await expect(page.locator('#ecosystem-canvas')).toBeVisible();
});

test('backend disconnection shows stale state, reconnection recovers', async ({ page }) => {
  await expect(page.locator('#simulation-tick')).not.toHaveText('—', { timeout: 15000 });
  const tickBefore = await page.locator('#simulation-tick').textContent();
  /* Simulate an outage: abort backend traffic but keep serving the page. */
  await page.route('http://127.0.0.1:8000/**', (route) => route.abort('failed'));
  await expect(page.locator('#connection-text')).toContainText('unreachable', { timeout: 15000 });
  await expect(page.locator('#data-freshness')).toHaveText('Stale', { timeout: 15000 });
  /* Last valid state stays visible during the outage. */
  await expect(page.locator('#simulation-tick')).toHaveText(tickBefore ?? '', { timeout: 5000 });
  await page.unroute('http://127.0.0.1:8000/**');
  await expect(page.locator('#connection-text')).toContainText('Backend connected', { timeout: 15000 });
  await expect(page.locator('#data-freshness')).toHaveText('Live', { timeout: 15000 });
});
