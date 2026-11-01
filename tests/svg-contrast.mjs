import assert from 'node:assert/strict';

export function contrast(foreground, background) {
  const luminance = rgb => rgb.map(channel => channel / 255).map(c => c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)
    .reduce((sum, c, i) => sum + c * [0.2126, 0.7152, 0.0722][i], 0);
  const a = luminance(foreground), b = luminance(background);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}

// axe cannot infer the background behind SVG text (imgNode). Independently
// measure only simple solid-colour SVGs; unsupported paint/overlap fails closed.
export async function checkSVGContrast(page, incomplete) {
  for (const rule of incomplete) {
    assert.equal(rule.id, 'color-contrast', 'Unresolved non-contrast axe result');
    for (const node of rule.nodes) {
      assert.ok(node.any.length && node.any.every(check => check.data?.messageKey === 'imgNode'), 'Unknown contrast uncertainty');
      assert.equal(node.target.length, 1);
      assert.equal(await page.locator(node.target[0]).evaluate(node => node instanceof SVGTextElement), true);
    }
  }
  assert.ok(await page.locator('svg').evaluateAll(nodes => nodes.every(svg => svg.querySelector('text'))), 'SVG without measurable text requires a dedicated contrast check');
  const measurements = await page.locator('svg text, svg polyline, svg circle').evaluateAll(nodes => nodes.map(node => {
    const style = getComputedStyle(node);
    const svg = node.ownerSVGElement;
    const rect = node.getBoundingClientRect();
    const supported = [];
    if (node instanceof SVGTextElement && style.stroke !== 'none') supported.push('unsupported text stroke');
    let background;
    for (let ancestor = node; ancestor; ancestor = ancestor.parentElement) {
      const s = getComputedStyle(ancestor);
      if (Number(s.opacity) !== 1 || s.filter !== 'none' || s.backgroundImage !== 'none' || s.mixBlendMode !== 'normal') supported.push('non-solid ancestor paint');
      if (!background && s.backgroundColor !== 'rgba(0, 0, 0, 0)') background = s.backgroundColor;
    }
    if (node instanceof SVGTextElement) {
      for (const other of svg.querySelectorAll(':scope > :not(text)')) {
        const box = other.getBoundingClientRect();
        if (box.left < rect.right && box.right > rect.left && box.top < rect.bottom && box.bottom > rect.top) supported.push('graphic overlaps text background');
      }
    }
    if (svg.querySelector('image, use, foreignObject, rect, polygon, ellipse, g, line')) supported.push('unsupported SVG geometry');
    // Only the generator's horizontal tick grid is exempt from data-mark contrast.
    // New paths must not silently escape measurement as decorative geometry.
    const paths = [...svg.querySelectorAll('path')];
    if (paths.length > 3 || paths.some(path => !/^M54 -?\d+\.\d{2}H312$/.test(path.getAttribute('d') || '')
      || !['rgb(57, 75, 85)', 'rgb(181, 185, 188)'].includes(getComputedStyle(path).stroke))) supported.push('unsupported SVG path');
    if (Number(node instanceof SVGPolylineElement ? style.strokeOpacity : style.fillOpacity) !== 1) supported.push('transparent foreground');
    return { text: node.textContent, kind: node.tagName, foreground: node instanceof SVGPolylineElement ? style.stroke : style.fill, background, supported };
  }));
  const rgb = value => {
    assert.match(value || '', /^rgb\(\d+, \d+, \d+\)$/, 'Only opaque solid RGB paint is supported');
    return value.match(/\d+/g).map(Number);
  };
  return measurements.map(measurement => {
    assert.deepEqual(measurement.supported, [], JSON.stringify(measurement));
    const ratio = contrast(rgb(measurement.foreground), rgb(measurement.background));
    const minimum = measurement.kind === 'text' ? 4.5 : 3;
    assert.ok(ratio >= minimum, `SVG contrast ${ratio} below ${minimum}: ${JSON.stringify(measurement)}`);
    return { ...measurement, ratio, minimum };
  });
}
