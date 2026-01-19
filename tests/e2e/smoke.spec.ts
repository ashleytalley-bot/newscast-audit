import { test, expect } from '@playwright/test';

test.describe('Newscast Audit App', () => {
    test('should load without console errors', async ({ page }) => {
        // 1. Capture console messages
        const consoleErrors: string[] = [];
        page.on('console', msg => {
            if (msg.type() === 'error') {
                consoleErrors.push(msg.text());
            }
        });

        // 2. Navigate to the app
        await page.goto('/');

        // 3. Wait for the app title to be visible to ensure basic render
        await expect(page.locator('.header-title')).toHaveText('Newscast Audit Report');

        // 4. Wait for potential async initialization errors (Pyodide loading)
        // We can wait for the loading indicator to disappear or for a specific log
        // For now, let's wait a reasonable amount of time or for a success signal if valid
        // Ideally, we check if the file input is clickable, which means overlay is gone?
        // The loading overlay is #loading-indicator. It starts hidden? 
        // Let's check app.js: init() runs.

        // Let's wait for a bit to let network requests fail if they are going to.
        await page.waitForTimeout(3000);

        // 5. Assert no errors
        if (consoleErrors.length > 0) {
            console.error('Console Errors detected:', consoleErrors);
        }
        expect(consoleErrors).toEqual([]);
    });

    test('should complete initialization', async ({ page }) => {
        await page.goto('/');

        // The loading indicator should eventually disappear (have class 'hidden')
        // This confirms Pyodide loaded, bootstrapped, and the app is ready.
        const loader = page.locator('#loading-indicator');
        await expect(loader).toHaveClass(/hidden/, { timeout: 30000 });

        // Check that the upload section is visible
        await expect(page.locator('#upload-section')).toBeVisible();
    });
});
