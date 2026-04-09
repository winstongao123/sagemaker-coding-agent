const { test, expect } = require('@playwright/test');
const path = require('path');

const V4_HTML = 'file:///' + path.resolve(__dirname, '../PS_FLOWCHART_V4.html').replace(/\\/g, '/');
const RUNNABLE_HTML = 'file:///' + path.resolve(__dirname, '../PS_FLOWCHART_RUNNABLE.html').replace(/\\/g, '/');

test.describe('V4.6.0 HTML Validation', () => {

  test('V4 HTML loads and shows V4.6.0 version', async ({ page }) => {
    await page.goto(V4_HTML);
    await page.waitForLoadState('networkidle');

    // Check title
    const title = await page.title();
    expect(title).toContain('V4.6.0');

    // Check stats
    const statsText = await page.locator('.stats').textContent();
    expect(statsText).toContain('9');  // 9 skills
    expect(statsText).toContain('9,299');  // lines of code
    expect(statsText).toContain('V4.6.0');  // version

    // Screenshot
    await page.screenshot({ path: path.resolve(__dirname, '../screenshots/v4_hero_v46.png'), fullPage: false });
  });

  test('V4 HTML shows Runnable-Grade Review System card', async ({ page }) => {
    await page.goto(V4_HTML);
    await page.waitForLoadState('networkidle');

    // Click the Runnable Learnings tab
    const runnableTab = page.locator('.tab', { hasText: /runnable/i });
    if (await runnableTab.count() > 0) {
      await runnableTab.click();
      await page.waitForTimeout(500);
    }

    // Check for V4.6 review system content
    const pageText = await page.textContent('body');
    expect(pageText).toContain('Runnable-Grade Review System');
    expect(pageText).toContain('3-agent parallel review');
    expect(pageText).toContain('Adversarial verification');
    expect(pageText).toContain('Security review');
    expect(pageText).toContain('anti-rationalization');

    await page.screenshot({ path: path.resolve(__dirname, '../screenshots/v4_review_card_v46.png'), fullPage: false });
  });

  test('V4 HTML comparison table shows review parity', async ({ page }) => {
    await page.goto(V4_HTML);
    await page.waitForLoadState('networkidle');

    // Click Comparison tab
    const compTab = page.locator('.tab', { hasText: /comparison|gap/i });
    if (await compTab.count() > 0) {
      await compTab.click();
      await page.waitForTimeout(500);
    }

    const pageText = await page.textContent('body');
    expect(pageText).toContain('Parallel review agents');
    expect(pageText).toContain('Security review');
    expect(pageText).toContain('Feedback refinement');

    await page.screenshot({ path: path.resolve(__dirname, '../screenshots/v4_comparison_v46.png'), fullPage: false });
  });

  test('V4 HTML "is V4 best yet" table updated to V4.6', async ({ page }) => {
    await page.goto(V4_HTML);
    await page.waitForLoadState('networkidle');

    // Navigate to Bedrock tab
    const bedrockTab = page.locator('.tab', { hasText: /bedrock/i });
    if (await bedrockTab.count() > 0) {
      await bedrockTab.click();
      await page.waitForTimeout(500);
    }

    const pageText = await page.textContent('body');
    expect(pageText).toContain('V4.6.0 now has full parity on review/verification quality');
    expect(pageText).toContain('8 Runnable prompt patterns fully ported');

    await page.screenshot({ path: path.resolve(__dirname, '../screenshots/v4_bedrock_v46.png'), fullPage: false });
  });

  test('Runnable HTML shows V4.6 review parity in V4 Does Better tab', async ({ page }) => {
    await page.goto(RUNNABLE_HTML);
    await page.waitForLoadState('networkidle');

    // Click "V4 Does Better" tab
    const betterTab = page.locator('[onclick*="v4better"]');
    if (await betterTab.count() > 0) {
      await betterTab.click();
      await page.waitForTimeout(500);
    }

    const pageText = await page.textContent('body');
    expect(pageText).toContain('Review System Parity');
    expect(pageText).toContain('V4.6.0');
    expect(pageText).toContain('simplify');
    expect(pageText).toContain('security-review');

    await page.screenshot({ path: path.resolve(__dirname, '../screenshots/runnable_v4better_v46.png'), fullPage: false });
  });

  test('No Mermaid syntax errors on V4 HTML', async ({ page }) => {
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error' && msg.text().toLowerCase().includes('syntax')) {
        errors.push(msg.text());
      }
    });

    await page.goto(V4_HTML);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Wait for Mermaid to render

    expect(errors).toEqual([]);
  });
});
