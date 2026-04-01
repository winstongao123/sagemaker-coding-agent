const { test, expect } = require('@playwright/test');
const path = require('path');
const { pathToFileURL } = require('url');

function localFileUrl(...parts) {
  return pathToFileURL(path.join(__dirname, '..', ...parts)).href;
}

test.describe('architecture flowchart pages', () => {
  test('V4 HTML tabs switch correctly', async ({ page }) => {
    await page.goto(localFileUrl('PS_FLOWCHART_V4.html'));
    await expect(page.locator('h1')).toContainText('SageMaker Coding Agent V4.2.1');
    await expect(page.locator('.mermaid')).toHaveCount(3);

    const tabs = [
      { label: 'Architecture', panel: '#architecture', heading: 'Architecture' },
      { label: 'Runnable Comparison', panel: '#comparison', heading: 'Runnable Comparison' },
      { label: 'What V4 Does Better', panel: '#better', heading: 'What V4 Does Better' },
      { label: 'Beginner Guide', panel: '#beginner', heading: 'Beginner Guide' },
      { label: 'Bedrock + Verification', panel: '#bedrock', heading: 'Bedrock + Verification' },
    ];

    for (const tab of tabs) {
      await page.getByRole('button', { name: tab.label }).click();
      await expect(page.locator(tab.panel)).toHaveClass(/active/);
      await expect(page.locator(`${tab.panel} h2`).first()).toHaveText(tab.heading);
    }

    const bodyText = await page.locator('body').textContent();
    expect(bodyText).not.toContain('Ã');
    expect(bodyText).not.toContain('â€');
  });

  test('Runnable HTML tabs and all detail modals work correctly', async ({ page }) => {
    await page.goto(localFileUrl('PS_FLOWCHART_RUNNABLE.html'));
    await expect(page.locator('h1')).toContainText('Claude Code Runnable');

    const tabs = [
      { label: 'Architecture', panel: '#tab-arch' },
      { label: 'V4 Has', panel: '#tab-v4has' },
      { label: 'V4 Missing', panel: '#tab-v4missing' },
      { label: 'V4 Does Better', panel: '#tab-v4better' },
      { label: 'Deep Details', panel: '#tab-details' },
    ];

    for (const tab of tabs) {
      await page.locator('.tab', { hasText: tab.label }).click();
      await expect(page.locator(tab.panel)).toHaveClass(/active/);
    }

    const nodeIds = await page.evaluate(() => Object.keys(NODE_DETAILS));
    expect(nodeIds.length).toBeGreaterThan(20);

    for (const id of nodeIds) {
      await page.evaluate((nodeId) => nodeClick(nodeId), id);
      await expect(page.locator('.modal-overlay')).toHaveClass(/active/);
      await expect(page.locator('.modal h3')).not.toHaveText('');
      await expect(page.locator('.modal-body')).not.toHaveText('');
      await page.locator('.modal-close').click();
      await expect(page.locator('.modal-overlay')).not.toHaveClass(/active/);
    }

    const bodyText = await page.locator('body').textContent();
    expect(bodyText).not.toContain('Ã');
    expect(bodyText).not.toContain('â€');
  });
});
