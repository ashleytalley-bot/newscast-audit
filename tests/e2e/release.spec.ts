import { test, expect } from '@playwright/test';

/**
 * Release Integration Test
 * 
 * Verifies that the application loads correctly from the production build directory.
 * Uses the global webServer configuration from playwright.config.ts (http-server docs).
 */

test.describe('Release Integration', () => {

    test('should load the production build without critical errors', async ({ page }) => {
        const errors: string[] = [];
        const failedRequests: string[] = [];

        // Capture Console Errors
        page.on('console', msg => {
            if (msg.type() === 'error') {
                // Filter out the known "Critical Boot Error" log we added, we want to catch it via asserts
                // but strictly speaking any console.error is bad.
                errors.push(`[Console Error] ${msg.text()}`);
            }
        });

        // Capture Page Crashes / Unhandled Exceptions
        page.on('pageerror', exception => {
            errors.push(`[Page Error] ${exception.message}`);
        });

        // Capture Network Failures (404s, CORS, etc)
        page.on('requestfailed', request => {
            // Ignore cancelled requests
            if (request.failure()?.errorText === 'net::ERR_ABORTED') return;
            failedRequests.push(`${request.url()} (${request.failure()?.errorText})`);
        });

        page.on('response', response => {
            if (response.status() >= 400) {
                failedRequests.push(`${response.url()} (${response.status()})`);
            }
        });

        // Navigate to the root (Playwright uses baseURL from config)
        await page.goto('/');

        // Wait for connection to settle
        await page.waitForLoadState('networkidle');

        // Check for our custom error message from index.html
        // If this exists, the test definitely failed
        const errorMsg = await page.locator('#error-message').innerText();
        if (errorMsg && await page.locator('#error-message').isVisible()) {
            errors.push(`[UI Error] ${errorMsg}`);
        }

        // Verify "Upload Survey Export" is visible (proof of successful boot)
        await expect(page.locator('#upload-section h2')).toContainText('Upload Survey Export');

        // Verify no network or console errors
        expect(failedRequests, 'Should have no failed network requests').toHaveLength(0);
        expect(errors, 'Should have no console/UI errors').toHaveLength(0);
    });
});
