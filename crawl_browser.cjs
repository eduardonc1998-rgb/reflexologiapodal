const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const [url, outArg, executablePath] = process.argv.slice(2);
if (!url || !outArg) throw new Error('Usage: crawl_browser.cjs URL OUTPUT_DIR');
const out = path.resolve(outArg);
fs.mkdirSync(out, { recursive: true });

(async () => {
  const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
  const context = await browser.newContext({ viewport: { width: 412, height: 915 }, deviceScaleFactor: 1, locale: 'pt-BR', timezoneId: 'America/Sao_Paulo' });
  // Keep analytics and IP lookup calls from firing during the local crawl.
  const blocked = [];
  const isBlocked = u => /utmify\.com\.br|trackerfy\.com\.br|connect\.facebook\.net|facebook\.com|api6?\.ipify\.org|localhost:3001\/tracking|127\.0\.0\.1:8000\/__l5e\/(trackevents|replay)/.test(u);
  await context.route('**/*', route => {
    const u = route.request().url();
    if (isBlocked(u)) { blocked.push(u); return route.abort(); }
    return route.continue();
  });
  const page = await context.newPage();
  const requests = [];
  const errors = [];
  page.on('request', r => requests.push({ type: r.resourceType(), url: r.url() }));
  page.on('requestfailed', r => { if (!isBlocked(r.url())) errors.push({ kind: 'requestfailed', url: r.url(), error: r.failure()?.errorText }); });
  page.on('response', r => { if (r.status() >= 400 && !isBlocked(r.url())) errors.push({ kind: 'http', status: r.status(), url: r.url() }); });
  page.on('console', m => { if (m.type() === 'error' && !/Failed to load resource: net::ERR_FAILED/.test(m.text())) errors.push({ kind: 'console', text: m.text() }); });
  page.on('pageerror', e => errors.push({ kind: 'pageerror', text: e.message }));
  await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(2500);
  const stageDir = path.join(out, 'stage-01-landing');
  fs.mkdirSync(stageDir, { recursive: true });
  await fs.promises.writeFile(path.join(stageDir, 'page.html'), await page.content(), 'utf8');
  await fs.promises.writeFile(path.join(stageDir, 'page.txt'), await page.locator('body').innerText(), 'utf8');
  await page.screenshot({ path: path.join(stageDir, 'screenshot.png'), fullPage: true });
  const options = await page.locator('a, button, [role="button"], label').evaluateAll(els => els.map((e, i) => ({
    index: i, tag: e.tagName.toLowerCase(), text: (e.innerText || e.getAttribute('aria-label') || '').trim(),
    href: e.getAttribute('href'), role: e.getAttribute('role')
  })).filter(x => x.text || x.href));
  await fs.promises.writeFile(path.join(stageDir, 'options.json'), JSON.stringify(options, null, 2), 'utf8');
  const faqButtons = await page.getByRole('button').all();
  const faqAnswers = [];
  for (let i = 0; i < faqButtons.length; i++) {
    const button = faqButtons[i];
    const question = (await button.innerText()).replace(/\s*▼\s*$/, '').trim();
    await button.click();
    const expanded = await button.evaluate(el => el.parentElement.innerText);
    faqAnswers.push({ question, expandedText: expanded.replace(question, '').replace('▼', '').trim() });
    await button.click();
  }
  await fs.promises.writeFile(path.join(stageDir, 'faq-answers.json'), JSON.stringify(faqAnswers, null, 2), 'utf8');
  const grouped = {};
  for (const r of requests) { const host = new URL(r.url).host; (grouped[host] ||= []).push(r); }
  await fs.promises.writeFile(path.join(out, 'network.json'), JSON.stringify(grouped, null, 2), 'utf8');
  await fs.promises.writeFile(path.join(out, 'browser-errors.json'), JSON.stringify(errors, null, 2), 'utf8');
  await fs.promises.writeFile(path.join(out, 'blocked-tracking.json'), JSON.stringify([...new Set(blocked)].sort(), null, 2), 'utf8');
  await fs.promises.writeFile(path.join(out, 'crawl-summary.json'), JSON.stringify({
    url: page.url(), title: await page.title(), stageCount: 1,
    quizBranches: 0, checkoutFormsSubmitted: false,
    faqButtons: faqButtons.length, faqAnswersCaptured: faqAnswers.length,
    checkoutLinks: options.filter(o => (o.href || '').includes('pay.wiapy.com')).length,
    requestCount: requests.length, errors: errors.length, trackingRequestsBlocked: new Set(blocked).size
  }, null, 2), 'utf8');
  console.log(`Saved one landing-page stage to ${out}; requests=${requests.length}; errors=${errors.length}`);
  await browser.close();
})().catch(e => { console.error(e); process.exitCode = 1; });
