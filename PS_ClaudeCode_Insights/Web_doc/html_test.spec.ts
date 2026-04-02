import { test, expect } from '@playwright/test';
import path from 'path';

const RUNNABLE_PATH = 'file:///' + path.resolve(__dirname, 'PS_FLOWCHART_RUNNABLE.html').replace(/\\/g, '/');
const V4_PATH = 'file:///' + path.resolve(__dirname, 'PS_FLOWCHART_V4.html').replace(/\\/g, '/');

for (const [name, url] of [['Runnable', RUNNABLE_PATH], ['V4', V4_PATH]]) {
  test.describe(`${name} HTML`, () => {

    test('loads without errors', async ({ page }) => {
      const errors: string[] = [];
      page.on('pageerror', (err) => errors.push(err.message));
      await page.goto(url, { waitUntil: 'networkidle' });
      // Allow mermaid loading errors but not JS crashes
      const criticalErrors = errors.filter(e => !e.includes('mermaid') && !e.includes('Mermaid'));
      expect(criticalErrors).toHaveLength(0);
    });

    test('all 5 tabs are clickable', async ({ page }) => {
      await page.goto(url, { waitUntil: 'networkidle' });
      const tabs = page.locator('.tab');
      await expect(tabs).toHaveCount(5);
      for (let i = 0; i < 5; i++) {
        await tabs.nth(i).click();
        await expect(tabs.nth(i)).toHaveClass(/active/);
      }
    });

    test('has mermaid charts', async ({ page }) => {
      await page.goto(url, { waitUntil: 'networkidle' });
      await page.waitForTimeout(2000); // Wait for mermaid render
      const charts = page.locator('.mermaid svg');
      const count = await charts.count();
      expect(count).toBeGreaterThan(0);
    });

    test('no garbled characters', async ({ page }) => {
      await page.goto(url, { waitUntil: 'networkidle' });
      const body = await page.textContent('body');
      // Check for common garbled character indicators
      expect(body).not.toContain('\ufffd'); // replacement character
      expect(body).not.toContain('â€'); // double-encoded UTF-8
    });

    test('responsive at 375px (iPhone)', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 812 });
      await page.goto(url, { waitUntil: 'networkidle' });
      // Check no horizontal overflow
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = await page.evaluate(() => window.innerWidth);
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 10); // 10px tolerance
    });

    test('responsive at 768px (iPad)', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto(url, { waitUntil: 'networkidle' });
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = await page.evaluate(() => window.innerWidth);
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 10);
    });

    test('charts are centered', async ({ page }) => {
      await page.goto(url, { waitUntil: 'networkidle' });
      await page.waitForTimeout(2000);
      const containers = page.locator('.chart-container');
      const count = await containers.count();
      if (count > 0) {
        const style = await containers.first().evaluate((el) => {
          return window.getComputedStyle(el).textAlign;
        });
        expect(style).toBe('center');
      }
    });

    test('cross-compare tab has 7 sections', async ({ page }) => {
      await page.goto(url, { waitUntil: 'networkidle' });
      // Click on Cross-Compare tab (tab index 2)
      await page.locator('.tab').nth(2).click();
      const sections = page.locator('#tab-2 h3');
      const count = await sections.count();
      expect(count).toBe(7);
    });
  });
}
