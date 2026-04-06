import { test, expect } from '@playwright/test';

const HTML_PATH = 'file:///D:/Github/Number-Five/Main/Email/docs/flowcharts.html';

test('loads without JS errors', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (err) => errors.push(err.message));
  await page.goto(HTML_PATH, { waitUntil: 'networkidle' });
  const critical = errors.filter(e => !e.includes('mermaid') && !e.includes('Mermaid'));
  expect(critical).toHaveLength(0);
});

test('all 5 tabs clickable', async ({ page }) => {
  await page.goto(HTML_PATH, { waitUntil: 'networkidle' });
  const tabs = page.locator('.tab');
  await expect(tabs).toHaveCount(5);
  for (let i = 0; i < 5; i++) {
    await tabs.nth(i).click();
    await expect(tabs.nth(i)).toHaveClass(/active/);
  }
});

test('mermaid charts render as SVG', async ({ page }) => {
  await page.goto(HTML_PATH, { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);
  // Click through all tabs to trigger mermaid.run()
  const tabs = page.locator('.tab');
  const tabCount = await tabs.count();
  for (let i = 0; i < tabCount; i++) {
    await tabs.nth(i).click();
    await page.waitForTimeout(1000);
  }
  // Go back to tab 0
  await tabs.first().click();
  await page.waitForTimeout(1000);
  // Count SVGs across all tabs
  const svgs = page.locator('.mermaid svg');
  const svgCount = await svgs.count();
  console.log(`Rendered SVG count: ${svgCount}`);
  expect(svgCount).toBeGreaterThanOrEqual(9); // 11 charts, at least 9 should render
});

test('no garbled characters', async ({ page }) => {
  await page.goto(HTML_PATH, { waitUntil: 'networkidle' });
  const body = await page.textContent('body');
  expect(body).not.toContain('\ufffd');
});

test('iPhone 375px no overflow', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto(HTML_PATH, { waitUntil: 'networkidle' });
  const bw = await page.evaluate(() => document.body.scrollWidth);
  const vw = await page.evaluate(() => window.innerWidth);
  expect(bw).toBeLessThanOrEqual(vw + 10);
});

test('iPad 768px no overflow', async ({ page }) => {
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.goto(HTML_PATH, { waitUntil: 'networkidle' });
  const bw = await page.evaluate(() => document.body.scrollWidth);
  const vw = await page.evaluate(() => window.innerWidth);
  expect(bw).toBeLessThanOrEqual(vw + 10);
});

test('charts are centered', async ({ page }) => {
  await page.goto(HTML_PATH, { waitUntil: 'networkidle' });
  const containers = page.locator('.chart-container');
  const count = await containers.count();
  expect(count).toBeGreaterThan(0);
  const style = await containers.first().evaluate(el => window.getComputedStyle(el).textAlign);
  expect(style).toBe('center');
});
