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

        // Manually trigger initialization since it is lazy-loaded (normally on file drop)
        // This is required to catch startup errors like missing packages (e.g. pyyaml)
        await page.evaluate(async () => {
            // @ts-ignore
            if (window.app && window.app.pyodideService) {
                // @ts-ignore
                window.app.showLoading("Testing Initialization...");
                // @ts-ignore
                await window.app.pyodideService.initialize();
                // @ts-ignore
                window.app.hideLoading();
            }
        });

        // The loading indicator should eventually disappear
        const loader = page.locator('#loading-indicator');
        await expect(loader).toHaveClass(/hidden/, { timeout: 30000 });

        // Check that the upload section is visible
        await expect(page.locator('#upload-section')).toBeVisible();
    });

    test('should process mock data', async ({ page }) => {
        await page.goto('/');

        // Initialize and process mock data
        const result = await page.evaluate(async () => {
            // @ts-ignore
            if (!window.app || !window.app.pyodideService) throw new Error("App not found");

            // @ts-ignore
            await window.app.pyodideService.initialize();

            // Minimal valid data structure expected by the pipeline
            const mockData = [
                {
                    "Timestamp": "2023-10-27 10:00:00",
                    "Email": "test@example.com",
                    "Date": "2023-10-27",
                    "Newscast": "Morning",
                    "Story Slug": "Test Story",
                    "Does the story address the audience as \"you,\" end with \"Here's what you need to know,\" or include a perspective from a specific person?": "Yes"
                }
            ];

            // @ts-ignore
            return await window.app.pyodideService.processData(mockData);
        });

        expect(result).toBeDefined();
        // We expect success or at least a structured response, not a crash
        // If the pipeline validation fails (missing columns), success might be false, 
        // but we verify we got a result object back, not an exception.
        expect(result.success).toBeDefined();
    });
});
