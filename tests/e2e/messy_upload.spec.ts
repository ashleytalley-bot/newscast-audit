// tests/e2e/messy_upload.spec.ts
import { test, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test.describe('Messy Fixture Upload', () => {
    test('should display data quality warnings and info for messy data', async ({ page }) => {
        test.setTimeout(120000); // allow Pyodide init
        await page.goto('/');

        const fileInput = page.locator('#file-input');
        await expect(fileInput).toBeAttached();

        const filePath = path.join(__dirname, '../fixtures/messy_upload.xlsx');
        await fileInput.setInputFiles(filePath);

        // Wait for warnings/info to appear
        const warningsCard = page.locator('.warnings-card');
        await expect(warningsCard).toBeVisible({ timeout: 60000 });

        const warningsText = await warningsCard.innerText();
        // Check for unexpected entries warning
        expect(warningsText).toContain('unexpected entries');
        // Check for unrecognized newscast warning
        expect(warningsText).toContain('unrecognized newscast');

        // Info section for ignored columns
        const infoHeader = page.locator('.info-header');
        await expect(infoHeader).toBeVisible();
        const infoItems = page.locator('.quality-item.info-item');
        await expect(infoItems.first()).toContainText('Ignored');

        // Expand examples to verify ignored column name appears
        const detailsToggle = page.locator('.info-header >> .error-details-toggle');
        if (await detailsToggle.isVisible()) {
            await detailsToggle.click();
        }
        const examplesList = page.locator('.quality-examples li');
        await expect(examplesList).toContainText('Extra Column');
    });
});
