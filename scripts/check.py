#!/usr/bin/env python3
"""Independently validate retained source, generated data and static HTML.

No build/extraction code is imported: the workbook is reopened using openpyxl.
Run ``python scripts/check.py --root PATH`` on a staged tree before publishing.
Run ``python scripts/check.py --self-test`` for isolated mutation regression tests.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re
import sys
from datetime import date, datetime
from urllib.parse import urlparse
import unittest

import openpyxl


class ValidationError(ValueError):
    """A source or publication invariant failed."""


def require(condition, message):
    if not condition:
        raise ValidationError(message)


FUNCTION_ROWS = (20, 27, 37, 56, 64, 74, 79, 87, 99, 121, 130)
# Eleven parts plus their independently rounded published total: 12 x £0.5m.
FUNCTION_ROUNDING_TOLERANCE = 6
EXPECTED_LABELS = {
    20: "Total general public services", 27: "Total defence",
    37: "Total public order and safety", 56: "Total economic affairs",
    64: "Total environment protection", 74: "Total housing and community amenities",
    79: "Total health", 87: "Total recreation, culture and religion",
    99: "Total education", 121: "Total social protection", 130: "Total EU transactions",
    131: "Public sector expenditure on services", 132: "Accounting adjustments",
    133: "Total Managed Expenditure (11)", 107: "of which: pensions",
    15: "of which: central government debt interest",
    14: "1.7 Public debt transactions (2), (3)",
}
FISCAL_YEAR = re.compile(r"^(\d{4})-(\d{2})$")


def latest_column(sheet):
    candidates = []
    for cell in sheet[5]:
        match = FISCAL_YEAR.fullmatch(str(cell.value))
        if match:
            start = int(match[1])
            require(int(match[2]) == (start + 1) % 100,
                    f"Invalid fiscal year at {sheet.title}!{cell.coordinate}")
            candidates.append((start, cell.column, cell.value))
    require(bool(candidates), f"No fiscal-year headers in {sheet.title}")
    require(len({x[0] for x in candidates}) == len(candidates),
            f"Duplicate fiscal-year headers in {sheet.title}")
    _, column, year = max(candidates)
    return column, year


def number(value, context):
    require(type(value) in (int, float) and math.isfinite(value),
            f"{context}: expected a finite numeric value, not {value!r}")
    return value


def source_record(sheet, column, row):
    cell = sheet.cell(row, column)
    label = sheet.cell(row, 2).value
    require(isinstance(label, str) and bool(label.strip()),
            f"Missing raw row label at {sheet.title}!B{row}")
    return {"label": label.strip(), "value": number(cell.value, cell.coordinate),
            "cell": cell.coordinate}


def same_record(actual, expected, context):
    require(isinstance(actual, dict), f"{context}: expected an object")
    for key in ("label", "value", "cell"):
        require(key in actual, f"{context}: missing {key}")
        if key == "value":
            number(actual[key], context)
        require(actual[key] == expected[key],
                f"{context}.{key}: got {actual[key]!r}; raw source says {expected[key]!r}")


def validate_data(data, manifest, workbook):
    require(isinstance(data, dict), "Generated spending data must be an object")
    require({"5_2", "5_3"} <= set(workbook.sheetnames), "Missing source tables 5.2 / 5.3")
    functional, economic = workbook["5_2"], workbook["5_3"]
    for row, expected_label in EXPECTED_LABELS.items():
        raw_label = functional.cell(row, 2).value
        require(isinstance(raw_label, str) and raw_label.strip() == expected_label,
                f"Source layout changed at 5_2!B{row}: expected {expected_label!r}, got {raw_label!r}")
    for row, expected_label in ((28, "Total public sector expenditure on services"),
                                (30, "Total Managed Expenditure"), (16, "Public sector debt interest")):
        require(economic.cell(row, 2).value == expected_label,
                f"Source layout changed at 5_3!B{row}")
    col, year = latest_column(functional)
    other_col, other_year = latest_column(economic)
    require(year == other_year, "Source tables have different latest years")
    status = functional.cell(6, col).value
    require(status in ("outturn", "estimate", "forecast"), f"Unknown raw status: {status!r}")
    require(economic.cell(6, other_col).value == status, "Cross-table statuses differ")
    require(functional.cell(3, col).value == "£ million", "Source units changed")
    for key, expected in {"year": year, "status": status, "unit": "GBP million",
                          "geography": "United Kingdom",
                          "scope": "Public sector expenditure on services"}.items():
        require(data.get(key) == expected, f"{key}: expected {expected!r}, got {data.get(key)!r}")
    require(data.get("source") == manifest, "Generated source metadata differs from manifest")
    rows = data.get("rows")
    require(isinstance(rows, list) and len(rows) == len(FUNCTION_ROWS),
            "Expected exactly eleven functional categories (including negative EU transactions)")
    for actual, row in zip(rows, FUNCTION_ROWS):
        same_record(actual, source_record(functional, col, row), f"rows[{row}]")
    for name, row in (("total", 131), ("adjustment", 132), ("tme", 133)):
        same_record(data.get(name), source_record(functional, col, row), name)
    extras = data.get("extras")
    require(isinstance(extras, list) and len(extras) == 2, "Expected pensions and central interest extras")
    # Order is irrelevant; exact source locators distinguish these overlapping subtotals.
    expected_extras = [source_record(functional, col, row) for row in (107, 15)]
    require(all(isinstance(item, dict) for item in extras), "Extras must be records")
    require(len({item.get("cell") for item in extras}) == 2, "Duplicate extras")
    for expected in expected_extras:
        actual = next((item for item in extras if item.get("cell") == expected["cell"]), None)
        same_record(actual, expected, f"extras {expected['cell']}")
    total = data["total"]["value"]
    require(total > 0, "Spending-on-services denominator must be positive")
    gap = abs(sum(item["value"] for item in rows) - total)
    require(gap <= FUNCTION_ROUNDING_TOLERANCE,
            f"Functional parts differ from total by £{gap}m; permitted rounding is £6m")
    gap = abs(total + data["adjustment"]["value"] - data["tme"]["value"])
    require(gap <= 1.5, f"Services + adjustments do not reconcile with TME (gap £{gap}m)")
    for other_row, functional_row in ((28, 131), (30, 133), (16, 14)):
        left = number(economic.cell(other_row, other_col).value, f"5_3 row {other_row}")
        right = number(functional.cell(functional_row, col).value, f"5_2 row {functional_row}")
        require(left == right, f"Cross-table disagreement: 5_3 row {other_row} / 5_2 row {functional_row}")
    health = source_record(functional, col, 79)["value"]
    number(data.get("health_share"), "health_share")
    require(data["health_share"] == health / total * 100,
            "health_share must be exactly health / spending on services * 100, without pre-rounding")


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.visible = []
        self.tags = []
        self.links = []
        self.issues = []
        self.hidden = 0
        self.language = False
        self.viewport = False
        self.rows = {}
        self.current_row = None
        self.current_cells = []
        self.current_cell = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append(tag)
        if tag == "tr":
            self.current_row = attrs.get("id")
            self.current_cells = []
        if tag in ("th", "td"):
            self.current_cell = []
        if tag in ("script", "iframe", "object", "embed"):
            self.issues.append(f"Forbidden active element: {tag}")
        if tag in ("style", "script", "head"):
            self.hidden += 1
        if tag == "html":
            self.language = bool(attrs.get("lang"))
        if tag == "meta" and attrs.get("name", "").lower() == "viewport":
            self.viewport = "width=device-width" in attrs.get("content", "").replace(" ", "")
        for key, value in attrs.items():
            if key.startswith("on"):
                self.issues.append(f"JavaScript event handler: {key}")
            if value and re.match(r"\s*(?:javascript|vbscript):", value, re.I):
                self.issues.append("Script URL")
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])

    def handle_endtag(self, tag):
        if tag in ("th", "td") and self.current_cell is not None:
            self.current_cells.append(" ".join("".join(self.current_cell).split()))
            self.current_cell = None
        if tag == "tr" and self.current_row:
            if self.current_row in self.rows:
                self.issues.append(f"Duplicate source row id: {self.current_row}")
            self.rows[self.current_row] = self.current_cells
            self.current_row = None
        if tag in ("style", "script", "head"):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, text):
        if not self.hidden:
            self.visible.append(text)
            if self.current_cell is not None:
                self.current_cell.append(text)

    @property
    def text(self):
        return " ".join(" ".join(self.visible).split())


def date_forms(value):
    parsed = date.fromisoformat(value[:10])
    return {parsed.isoformat(), f"{parsed.day} {parsed:%B %Y}", parsed.strftime("%d %B %Y")}


def validate_page(path, manifest, banned):
    raw = path.read_bytes()
    require(len(raw) < 500_000, f"{path}: page must be below 500 KB")
    page = Page()
    page.feed(raw.decode("utf-8"))
    require(not page.issues, f"{path}: {', '.join(page.issues)}")
    require("main" in page.tags and "h1" in page.tags, f"{path}: missing static main heading/content")
    require(page.language and page.viewport, f"{path}: missing language or mobile viewport")
    text = page.text
    require("Open Government Licence" in text, f"{path}: missing OGL attribution")
    require(any("nationalarchives.gov.uk/doc/open-government-licence" in x for x in page.links),
            f"{path}: missing OGL licence link")
    if manifest is not None:  # The corrections ledger is not an official data release.
        require(manifest["publication"] in text, f"{path}: missing source publication")
        require(any(form in text for form in date_forms(manifest["date"])),
                f"{path}: missing source publication/update date")
    for word in banned:
        require(not re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", text, re.I),
                f"{path}: banned evaluative wording: {word}")
    return page


def validate_hash(raw, expected):
    require(hashlib.sha256(raw).hexdigest() == expected,
            "Retained source SHA-256 differs from manifest")


def validate_published_data(page, data):
    records = data["rows"] + [data["total"], data["adjustment"], data["tme"]] + data["extras"]
    for record in records:
        expected = [record["label"], f"{record['value']:,}", f"5_2!{record['cell']}"]
        require(page.rows.get(record["cell"]) == expected,
                f"Published HTML source row {record['cell']} differs from verified data")
    require(f"£{data['health_share']:.2f} goes on health" in page.text,
            "Published health share differs from independently verified share")
    require(data["year"] in page.text and data["status"] in page.text,
            "Published HTML missing year/status")


def validate(root):
    # Independent copy parser includes details, source labels, tables and quotes.
    # Run first so all per-page grades are reported even when other checks fail.
    from reading_grade import validate as validate_reading_grade
    validate_reading_grade(root)
    manifest = json.loads((root / "sources/manifest.json").read_text(encoding="utf-8"))
    require(isinstance(manifest, dict), "Source manifest must be an object")
    for key in ("file", "sha256", "url", "publication", "date", "published", "downloaded", "release_url"):
        require(isinstance(manifest.get(key), str) and bool(manifest[key].strip()),
                f"Manifest requires a non-empty {key}")
    require(manifest["file"] == "spending.xlsx", "Unexpected retained source filename")
    require(re.fullmatch(r"[a-f0-9]{64}", manifest["sha256"]) is not None, "Invalid SHA-256")
    for key in ("url", "release_url"):
        parsed = urlparse(manifest[key])
        require(parsed.scheme == "https" and parsed.hostname is not None and
                (parsed.hostname == "gov.uk" or parsed.hostname.endswith(".gov.uk")),
                f"{key} must resolve to an official HTTPS gov.uk source")
    for key in ("date", "published", "downloaded"):
        try:
            datetime.fromisoformat(manifest[key].replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValidationError(f"Manifest {key} is not an ISO date/time") from exc
    source = root / "sources" / manifest["file"]
    validate_hash(source.read_bytes(), manifest["sha256"])
    require((root / "site/sources/spending.xlsx").read_bytes() == source.read_bytes(),
            "Downloadable workbook differs from retained raw source")
    require(json.loads((root / "site/sources/manifest.json").read_text(encoding="utf-8")) == manifest,
            "Downloadable source manifest differs from retained manifest")
    workbook = openpyxl.load_workbook(source, data_only=True, read_only=True)
    try:
        data = json.loads((root / "site/data/spending.json").read_text(encoding="utf-8"))
        validate_data(data, manifest, workbook)
    finally:
        workbook.close()
    from check_history import validate as validate_history
    validate_history(root)
    banned_path = Path(__file__).resolve().parent / "banned-words.txt"
    require((root / "site/banned-words.txt").read_bytes() == banned_path.read_bytes(),
            "Published banned-word list differs from the enforced list")
    banned = [line.strip() for line in banned_path.read_text(encoding="utf-8").splitlines()
              if line.strip() and not line.lstrip().startswith("#")]
    require(bool(banned), "Published banned-word list is empty")
    require({"massive", "slashed", "soaring", "savage", "generous", "reckless"} <= set(banned),
            "Banned-word list omits rubric examples")
    pages = sorted((root / "site").rglob("*.html"))
    require(bool(pages) and (root / "site/index.html") in pages, "Missing static home page")
    for path in pages:
        page_manifest = None if path.name == 'corrections.html' else manifest
        if path.name == 'parties.html':
            page_manifest = json.loads((root / 'sources/party-offers.json').read_text())['roster']
        elif path.name == 'income.html':
            page_manifest = json.loads((root / 'sources/income-manifest.json').read_text())
        elif path.name in ('history.html', 'history-cash.html', 'history-real.html', 'history-gdp.html'):
            page_manifest = json.loads((root / 'sources/history-manifest.json').read_text())
        page = validate_page(path, page_manifest, banned)
        if path == root / "site/index.html":
            validate_published_data(page, data)
    import corrections
    import corrections_page
    entries = corrections.load(root / 'sources/corrections.json')
    require((root / 'site/sources/corrections.json').read_bytes() ==
            (root / 'sources/corrections.json').read_bytes(), 'Published corrections source differs')
    require((root / 'site/corrections.html').read_text() ==
            corrections_page.render(entries, (root / 'site/index.html').read_text()),
            'Corrections page differs from retained log')
    for path in pages:
        if path.name != 'corrections.html':
            require('href="corrections.html"' in path.read_text(), f'{path}: missing corrections link')
    from check_comparisons import validate as validate_comparisons
    validate_comparisons(root)
    from check_income import validate as validate_income
    validate_income(root)
    from parties import validate as validate_parties
    validate_parties(root)
    print(f"PASS: source hash; independent raw values, labels, locators, year and status; "
          f"reconciliation and cross-table checks; {len(pages)} static pages; banned words")


class MutationTests(unittest.TestCase):
    """Synthetic workbook fixtures; no build functions or network access."""
    def setUp(self):
        self.workbook = openpyxl.Workbook()
        self.workbook.remove(self.workbook.active)
        self.sheet = self.workbook.create_sheet("5_2")
        other = self.workbook.create_sheet("5_3")
        for sheet in (self.sheet, other):
            sheet["F5"], sheet["G5"], sheet["G6"] = "2024-25", "2025-26", "outturn"
        self.sheet["G3"] = "£ million"
        for row in (*FUNCTION_ROWS, 131, 132, 133, 107, 15, 14):
            self.sheet.cell(row, 2, EXPECTED_LABELS[row])
            self.sheet.cell(row, 7, 100)
        self.sheet["G130"] = -1
        self.sheet["G131"], self.sheet["G132"], self.sheet["G133"] = 999, 20, 1019
        other["G28"], other["G30"], other["G16"] = 999, 1019, 100
        other["B28"] = "Total public sector expenditure on services"
        other["B30"], other["B16"] = "Total Managed Expenditure", "Public sector debt interest"
        self.manifest = {"test": "source"}
        self.data = {"year": "2025-26", "status": "outturn", "unit": "GBP million",
                     "geography": "United Kingdom", "scope": "Public sector expenditure on services",
                     "source": self.manifest,
                     "rows": [source_record(self.sheet, 7, row) for row in FUNCTION_ROWS],
                     "extras": [source_record(self.sheet, 7, row) for row in (107, 15)],
                     "health_share": 100 / 999 * 100}
        for name, row in (("total", 131), ("adjustment", 132), ("tme", 133)):
            self.data[name] = source_record(self.sheet, 7, row)

    def test_valid(self):
        validate_data(self.data, self.manifest, self.workbook)

    def test_mutated_records_and_metadata(self):
        mutations = [lambda d: d.update(year="2024-25"), lambda d: d.update(status="forecast"),
                     lambda d: d.update(health_share=round(d["health_share"], 2)),
                     lambda d: d["rows"][0].update(value=101),
                     lambda d: d["rows"][0].update(label="Wrong label"),
                     lambda d: d["rows"][0].update(cell="5_2!F20"),
                     lambda d: d["rows"][-1].update(value=1),
                     lambda d: d["extras"][0].update(value=True),
                     lambda d: d.update(source={"changed": True})]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                data = copy.deepcopy(self.data)
                mutation(data)
                with self.assertRaises(ValidationError):
                    validate_data(data, self.manifest, self.workbook)

    def test_cross_table_mutation(self):
        self.workbook["5_3"]["G16"] = 101
        with self.assertRaisesRegex(ValidationError, "Cross-table"):
            validate_data(self.data, self.manifest, self.workbook)

    def test_rounding_limit(self):
        self.sheet["G20"] = 107
        self.data["rows"][0]["value"] = 107
        with self.assertRaisesRegex(ValidationError, "permitted rounding"):
            validate_data(self.data, self.manifest, self.workbook)
        self.sheet["G20"] = 106
        self.data["rows"][0]["value"] = 106
        validate_data(self.data, self.manifest, self.workbook)

    def test_raw_hash_mutation(self):
        raw = b"retained official workbook bytes"
        digest = hashlib.sha256(raw).hexdigest()
        validate_hash(raw, digest)
        with self.assertRaisesRegex(ValidationError, "SHA-256"):
            validate_hash(raw + b"changed", digest)

    def test_source_layout_mutation(self):
        self.sheet["B79"] = "Different series"
        self.data["rows"][6]["label"] = "Different series"
        with self.assertRaisesRegex(ValidationError, "Source layout changed"):
            validate_data(self.data, self.manifest, self.workbook)

    def test_html_source_mutation(self):
        records = self.data["rows"] + [self.data["total"], self.data["adjustment"], self.data["tme"]] + self.data["extras"]
        html = "<table>" + "".join(
            f'<tr id="{r["cell"]}"><th>{r["label"]}</th><td>{r["value"]:,}</td><td>5_2!{r["cell"]}</td></tr>'
            for r in records) + "</table>"
        html += f"<p>2025-26 outturn £{self.data['health_share']:.2f} goes on health</p>"
        page = Page()
        page.feed(html)
        validate_published_data(page, self.data)
        page.rows["G79"][1] = "101"
        with self.assertRaisesRegex(ValidationError, "Published HTML"):
            validate_published_data(page, self.data)

    def test_active_html_is_rejected(self):
        for html in ('<script src="x"></script>', '<a href="javascript:alert(1)">x</a>',
                     '<p onclick="alert(1)">text</p>'):
            with self.subTest(html=html):
                page = Page()
                page.feed(html)
                self.assertTrue(page.issues)

    def test_latest_year_is_discovered(self):
        self.sheet["H5"], self.sheet["H6"] = "2026-27", "forecast"
        self.assertEqual(latest_column(self.sheet), (8, "2026-27"))
        with self.assertRaisesRegex(ValidationError, "different latest years"):
            validate_data(self.data, self.manifest, self.workbook)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--self-test", action="store_true", help="run isolated mutation tests")
    args = parser.parse_args()
    if args.self_test:
        suite = unittest.TestSuite([
            unittest.defaultTestLoader.loadTestsFromTestCase(MutationTests),
            unittest.defaultTestLoader.loadTestsFromName('test_reading_grade'),
        ])
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1
    try:
        validate(args.root.resolve())
    except (ValidationError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
