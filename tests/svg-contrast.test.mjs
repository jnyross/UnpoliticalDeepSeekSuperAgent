import test from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { contrast, checkSVGContrast } from './svg-contrast.mjs';

test('WCAG relative luminance has known endpoints', () => {
  assert.equal(contrast([0, 0, 0], [255, 255, 255]), 21);
  assert.equal(contrast([255, 255, 255], [255, 255, 255]), 1);
});

test('SVG measurement passes solid dark text and fails low contrast, overlap and unknown paint', async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const render = async (fill, extra = '') => page.setContent(`<body style="background:white"><svg width="300" height="100"><text x="20" y="40" fill="${fill}">Label</text>${extra}</svg></body>`);
  try {
    await render('black');
    assert.equal((await checkSVGContrast(page, []))[0].ratio, 21);
    await render('#aaa');
    await assert.rejects(checkSVGContrast(page, []), /below/);
    await render('black', '<polyline points="0,20 200,60" stroke="black"/>');
    await assert.rejects(checkSVGContrast(page, []), /graphic overlaps/);
    await render('url(#paint)');
    await assert.rejects(checkSVGContrast(page, []), /opaque solid/);
    await render('black');
    await page.locator('text').evaluate(node => { node.style.stroke = 'white'; node.style.strokeWidth = '8px'; node.style.paintOrder = 'fill stroke'; });
    await assert.rejects(checkSVGContrast(page, []), /unsupported text stroke/);
    await render('black', '<path d="M10 20H200" stroke="white"/>');
    await assert.rejects(checkSVGContrast(page, []), /unsupported SVG path/);
    await page.setContent('<body style="background:white"><svg><path d="M10 20H200" stroke="white"/></svg></body>');
    await assert.rejects(checkSVGContrast(page, []), /without measurable text/);
    await render('black');
    await assert.rejects(checkSVGContrast(page, [{ id: 'other-rule', nodes: [] }]), /Unresolved/);
  } finally { await browser.close(); }
});
