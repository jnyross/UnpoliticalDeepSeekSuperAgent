import assert from 'node:assert/strict';

// Each question must lead directly to its substantive answer, including the
// two distinct questions within the ten-year comparison.
const answers = [
  { name: 'largest-area', href: '#largest-area', paragraph: '#largest-area', expected: [/Social protection is the largest area of spending\./, /pensions, benefits and care/] },
  { name: 'health-share', href: '#health-share', paragraph: '#health-share', expected: [/Of each £100 spent on services/, /£\d+\.\d{2} goes on health/] },
  { name: 'debt-interest', href: '#debt-interest', paragraph: '#debt-interest', expected: [/In 2025-26, central government debt interest was £[\d,.]+ billion/, /\(outturn, not a forecast\)/, /gross interest/] },
  { name: 'pensions-defence', href: '#pensions-defence', paragraph: '#pensions-defence', expected: [/Old-age pensions were £[\d,.]+ billion/, /Defence was £[\d,.]+ billion/, /not NATO's measure/] },
  { name: 'health-ten-years', href: '#health-ten-years', paragraph: '#health-ten-years + p', expected: [/Health spending went (up|down) by \d+\.\d%/, /a change of £[\d,.-]+ billion/, /prices\./] },
  { name: 'gdp-ten-years', href: '#gdp-ten-years', paragraph: '#gdp-ten-years + p', expected: [/Total spending was a (bigger|smaller) share of the economy/, /\d+\.\d% of GDP/, /percentage points\./] },
  { name: 'forecast-status', href: '#forecast-status', paragraph: '#forecast-status', expected: [/UK-wide figures for \d{4}-\d{2}/, /outturn: recorded spending, not a forecast/, /None of the numbers on this page are forecasts\./] },
  { name: 'check-source', href: '#check-source', paragraph: '#check-source ~ p', startsWith: 'Source:', expected: [/Source:/, /HM Treasury/, /First published/, /source page updated/, /Downloaded/] },
];

async function rect(locator) {
  return locator.evaluate(node => {
    const { top, right, bottom, left, width, height } = node.getBoundingClientRect();
    return { top, right, bottom, left, width, height };
  });
}

function withinViewport(box, viewport, message) {
  assert.ok(box.width > 0 && box.height > 0, `${message}: empty box`);
  assert.ok(box.top >= -1 && box.bottom <= viewport.height + 1,
    `${message}: not fully within viewport height: ${JSON.stringify(box)}`);
  assert.ok(box.left >= -1 && box.right <= viewport.width + 1,
    `${message}: not fully within viewport width: ${JSON.stringify(box)}`);
}

/** Exercise real links on the existing browser worker's page and server.
 * JavaScript-disabled contexts still allow Playwright to inspect geometry; no
 * page script, synthetic click, forced click or direct fragment navigation is
 * used to perform the navigation under test.
 */
export async function checkAnswerNavigation({ page, baseURL, javaScriptEnabled }) {
  const viewport = page.viewportSize();
  const report = { javaScriptEnabled, viewport, completed: false, answers: [] };
  for (const answer of answers) {
    const description = `${answer.name} ${viewport.width}×${viewport.height} JS ${javaScriptEnabled ? 'on' : 'off'}`;
    // A new unfragmented visit per answer prevents a previous landing, details
    // expansion or scroll restoration from making a hard-to-find link pass.
    await page.goto(`${baseURL}/index.html`, { waitUntil: 'networkidle' });
    const initialURL = new URL(page.url());
    assert.equal(initialURL.hash, '', `${description}: initial URL`);
    assert.equal(await page.evaluate(() => scrollY), 0, `${description}: initial scroll`);
    const navigation = page.getByRole('navigation', { name: 'Spending questions', exact: true });
    assert.equal(await navigation.count(), 1, `${description}: unique question navigation`);
    assert.ok(await navigation.isVisible(), `${description}: visible question navigation`);
    const navBox = await rect(navigation);
    assert.ok(navBox.top >= 0 && navBox.top <= viewport.height,
      `${description}: more than one screen of unrelated content before navigation`);
    const link = navigation.locator(`a[href="${answer.href}"]`);
    assert.equal(await link.count(), 1, `${description}: unique exact question href`);
    assert.ok(await link.isVisible(), `${description}: visible question link`);
    assert.ok((await link.innerText()).trim(), `${description}: named link`);
    const initialLink = await rect(link);
    // Permit one bounded initial scroll to reveal the nav on narrow screens,
    // but do not let locator.click() silently hunt for an off-screen link.
    const initialScroll = Math.max(0, initialLink.bottom - viewport.height + 8);
    assert.ok(initialScroll <= viewport.height, `${description}: link requires more than one screen of scrolling`);
    if (initialScroll) await page.evaluate(amount => scrollBy(0, amount), initialScroll);
    const clickableLink = await rect(link);
    withinViewport(clickableLink, viewport, `${description}: link before click`);
    const target = page.locator(`[id="${answer.href.slice(1)}"]`);
    assert.equal(await target.count(), 1, `${description}: target exists exactly once`);
    await link.click();
    await page.waitForURL(url => url.hash === answer.href);
    // Observe native fragment targeting without scrolling the target or answer
    // into view ourselves. This also works when site JavaScript is disabled.
    await page.waitForFunction(hash => document.querySelector(':target')?.id === hash.slice(1), answer.href);
    const landingURL = new URL(page.url());
    assert.equal(landingURL.origin + landingURL.pathname + landingURL.search,
      initialURL.origin + initialURL.pathname + initialURL.search, `${description}: native same-page anchor`);
    assert.ok(await target.isVisible(), `${description}: target visible`);
    const targetBox = await rect(target);
    assert.ok(targetBox.top >= -1 && targetBox.top < viewport.height,
      `${description}: target start outside landing viewport: ${JSON.stringify(targetBox)}`);
    let paragraph = page.locator(answer.paragraph);
    if (answer.startsWith) paragraph = paragraph.filter({ hasText: new RegExp(`^${answer.startsWith}`) });
    assert.equal(await paragraph.count(), 1, `${description}: unique answer paragraph`);
    assert.ok(await paragraph.isVisible(), `${description}: answer visible`);
    const text = (await paragraph.innerText()).replace(/\s+/g, ' ').trim();
    for (const expected of answer.expected) assert.match(text, expected, `${description}: actual answer text`);
    const answerBox = await rect(paragraph);
    withinViewport(answerBox, viewport, `${description}: answer after native landing`);
    const metrics = { name: answer.name, href: answer.href, linkText: (await link.innerText()).trim(), navigation: navBox, initialLink, initialScroll, clickableLink, target: targetBox, answer: answerBox, text, landingURL: page.url(), scrollY: await page.evaluate(() => scrollY) };
    if (answer.name === 'debt-interest') {
      // A second native click checks the particular figure, not only a generic
      // publication link: its retained source row must name the exact cell.
      const figure = paragraph.locator('a');
      const sourceHref = await figure.getAttribute('href');
      assert.match(sourceHref, /^#[A-Z]+\d+$/);
      await figure.click();
      await page.waitForURL(url => url.hash === sourceHref);
      const sourceRow = page.locator(sourceHref);
      assert.equal(await sourceRow.count(), 1);
      assert.match(await sourceRow.innerText(), new RegExp(`5_2!${sourceHref.slice(1)}`));
      const sourceBox = await rect(sourceRow);
      withinViewport(sourceBox, viewport, `${description}: exact source row after second click`);
      metrics.sourceCheck = { clicks: 2, landingURL: page.url(), sourceRow: sourceBox };
    }
    report.answers.push(metrics);
  }
  report.completed = true;
  // Leave the existing accessibility/state checks on a fresh, initial page.
  await page.goto(`${baseURL}/index.html`, { waitUntil: 'networkidle' });
  return report;
}
