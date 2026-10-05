const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined, headless: true });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    let healthProbes = 0;
    let chatRequests = 0;
    await page.route('https://scholarbot-demo-api.onrender.com/**', async route => {
      const path = new URL(route.request().url()).pathname;
      if (path === '/api/health') {
        healthProbes++;
        if (healthProbes === 1) return route.fulfill({ status: 503, json: { status: 'waking' } });
        return route.fulfill({ json: { status: 'healthy', groq_configured: true } });
      }
      if (path === '/api/chat') {
        chatRequests++;
        return route.fulfill({ contentType: 'text/plain', body: 'Ini jawaban **demo** untuk pengujian.' });
      }
      return route.fulfill({ json: { messages: [], uploaded_docs: [] } });
    });
    await page.goto('http://127.0.0.1:4175/');
    await page.getByRole('link', { name: 'Coba live demo', exact: true }).first().click();
    await page.getByRole('status').getByText('Menyiapkan demo', { exact: false }).waitFor();
    assert.equal(await page.getByRole('button', { name: 'Kirim pesan' }).isDisabled(), true);
    await page.getByRole('status').getByText('Demo siap.', { exact: false }).waitFor();
    await page.getByPlaceholder('Tanya apa saja tentang pelajaran...').fill('Halo');
    await page.getByRole('button', { name: 'Kirim pesan' }).click();
    await page.getByText('Ini jawaban', { exact: false }).waitFor();
    assert.equal(chatRequests, 1);
    assert.ok(healthProbes >= 2);
    assert.deepEqual(errors, []);
    await page.reload();
    await page.getByRole('status').getByText('Demo siap.', { exact: false }).waitFor();
    const blocked = await browser.newPage();
    await blocked.route('**/main.js', route => route.abort());
    await blocked.goto('http://127.0.0.1:4175/');
    assert.equal(await blocked.locator('.reveal').first().evaluate(el => getComputedStyle(el).opacity), '1');
    console.log('PASS landing → app, cold start, disabled send, one chat request, reload, no JS errors, readable landing with blocked script');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
