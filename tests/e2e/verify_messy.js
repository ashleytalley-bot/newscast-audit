// verify_messy.js
// This script uses Playwright to upload the messy fixture and extract data quality messages.
const { chromium } = require('playwright');
const path = require('path');
(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    await page.goto('http://127.0.0.1:8080/');
    const fileInput = await page.waitForSelector('#file-input');
    const filePath = path.join(__dirname, '../../tests/fixtures/messy_upload.xlsx');
    await fileInput.setInputFiles(filePath);
    // Wait for warnings/info to appear
    await page.waitForSelector('.warnings-card, .info-header', { timeout: 60000 });
    const warnings = await page.$eval('.warnings-card', el => el.innerText).catch(() => '');
    const info = await page.$eval('.info-header', el => el.innerText).catch(() => '');
    console.log(JSON.stringify({ warnings, info }));
    await browser.close();
})();
