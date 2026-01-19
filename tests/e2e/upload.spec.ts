
import { test, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test.describe('File Upload Flow', () => {
    test('should upload an Excel file and generate results', async ({ page }) => {
        test.setTimeout(120000); // 2 minutes for Pyodide init
        // 1. Navigate to the app
        await page.goto('/');

        // 2. Wait for the file input to be ready
        const fileInput = page.locator('#file-input');
        await expect(fileInput).toBeAttached();

        // 3. Define the path to the fixture file
        const filePath = path.join(__dirname, '../fixtures/test_upload.xlsx');

        // 4. Upload the file
        // Note: The app listens for 'change' event on the input
        await fileInput.setInputFiles(filePath);

        // 5. Wait for processing
        // The loading indicator should show up
        const loader = page.locator('#loading-indicator');
        await expect(loader).toBeVisible();

        // 6. Verify Results or Error
        // Wait for results to be visible, but fail fast if error appears
        const resultsSection = page.locator('#results-section');
        const errorMessage = page.locator('#error-message');

        try {
            await expect(resultsSection).toBeVisible({ timeout: 90000 });
        } catch (e) {
            // If results didn't appear, check if there's an error message
            if (await errorMessage.isVisible()) {
                const errorText = await errorMessage.textContent();
                throw new Error(`Upload failed with error: ${errorText}`);
            }
            throw e;
        }

        // The upload section should be hidden
        await expect(page.locator('#upload-section')).toBeHidden();

        // Check for summary values (quick check that data is loaded)
        await expect(page.locator('#summary-rows')).toHaveText('2');

        // Check if charts are rendered (e.g., the overall chart container)
        const overallChart = page.locator('#chart-overall');
        await expect(overallChart).toBeVisible();
        // Plotly adds .plot-container when rendered
        await expect(overallChart.locator('.plot-container')).toBeVisible();
    });

    test('should handle invalid files gracefully', async ({ page }) => {
        await page.goto('/');

        // Upload a non-excel file (e.g. this spec file itself as a dummy)
        const fileInput = page.locator('#file-input');
        const filePath = path.join(__dirname, 'upload.spec.ts');

        await fileInput.setInputFiles(filePath);

        // Error message should appear
        const errorMsg = page.locator('#error-message');
        await expect(errorMsg).toBeVisible();
        await expect(errorMsg).toContainText(/Please upload an Excel file/i);
    });
});
