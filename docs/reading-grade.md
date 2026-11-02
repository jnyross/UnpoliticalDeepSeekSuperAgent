# Reproducible reading-grade check

Run from the repository root after installing the pinned dependencies in
[requirements.txt](../requirements.txt):

```sh
python3 -m pip install -r requirements.txt
python3 scripts/check.py --self-test
python3 scripts/check.py
```

The regular check runs the independent
[reading-grade checker](../scripts/reading_grade.py) first. It scans **every
`site/**/*.html` file recursively**, in sorted path order, including newly added
pages. It reports every page before rejecting any that exceed the limit. Missing
pages, empty pages and numeric-only pages cannot pass. Use a staged repository
with `--root PATH`. To inspect all scores without enforcing the threshold:

```sh
python3 scripts/reading_grade.py --root . --report-only
```

## Scope: no selective copy exclusions

The full-copy measurement includes text in closed and nested `details`, summaries,
all table cells, headings, navigation, source labels, citations, chart/SVG text,
quotes, licence text and the document title. HTML entities are decoded. Only
`script` and `style` data are excluded as nonreadable code. No text is exempted
because it is official wording, technical, quoted, hidden with an attribute, or
placed behind an expander. Templates and `noscript` text are conservatively
included too. Attributes, comments, URLs in link *targets*, and CSS declarations
are not text nodes. Visible URL *labels* are included.

This is a static text parser, not a browser visibility or accessibility-tree
simulation. It does not execute scripts or interpret CSS. CSS-hidden text may
therefore be counted; CSS-generated text and image-only words are not extracted.
Do not use CSS-generated or image-only text for substantive site copy.

## Formula and gates

The unrounded Flesch–Kincaid US school grade is:

```text
0.39 × (words / sentences) + 11.8 × (syllables / words) − 15.59
```

There are **three gates**, each at **grade ≤ 7.0**, with no per-page allowlist:

1. **Full copy**: all extracted word and numeric tokens.
2. **Full copy, words only**: the same copy and boundaries, without purely numeric
   tokens. This prevents number-heavy tables from diluting linguistic difficulty.
3. **Prose, words only**: text in `p`, `li`, `dd` and `blockquote` elements, including
   their inline text/quotes and expanded details, but outside `table` and `svg`.
   This supplementary check prevents many short table labels from masking hard
   explanatory prose. Table and chart text remains assessed by both full-copy
   gates; it is **not exempt**. When there is no prose subset, this third gate is
   reported as `n/a`, never substituted for the full-copy check.

The output gives full-copy word/sentence/syllable counts, words-only counts,
all three grades and all dictionary misses. Display rounding does not determine
pass/fail. Negative calculated grades are not clamped. These scores are a
mechanical writing aid, not proof that a 12-year-old understands the content,
and not evidence of people testing. In particular, full-page means can conceal
a difficult individual sentence; simplify explanations and technical labels even
when the aggregate passes.

## Token rules

- English alphabetic runs are words. Internal straight/curly apostrophes are
  retained, so `can't` is one word. Possessives are words, not a separate `s`.
- Unicode is NFKD-normalized; combining accents are removed (`Féin` → `Fein`).
  Other non-ASCII characters become separators, rather than joining adjacent
  words. Hyphens/dashes split compounds and year ranges into components.
- Digit runs with internal decimal/grouping commas or full stops are one numeric
  token (`1,234.50`). Currency and percent symbols are separators. For the first
  gate each numeric token contributes one word and one syllable; this is a
  convention, **not** a claim about how a particular amount is read aloud.
  Both words-only gates remove those tokens, rather than guessing a verbal form.
- Source locators and hashes are not exempt: their alphabetic and digit runs are
  tokenized by the same rules. Link labels and adjacent SVG text nodes receive
  separating spaces; ordinary inline emphasis does not split a word.

## Sentence/fragment boundaries

The same deterministic boundary policy applies across pages and gates:

- `.`, `!` and `?` end sentences; a run such as `?!` or `...` is one boundary.
- Decimal points between digits are not stops. Dots in URLs starting `http://`,
  `https://` or `www.` are protected, as are their internal `!`/`?`; a trailing
  sentence stop is retained. The `!` in workbook locators such as `5_2!G79` is
  not a sentence stop.
- The fixed abbreviation list is `Mr. Mrs. Ms. Dr. Prof. St. vs. etc. e.g. i.e.`
  (case insensitive). Dotted initials (`U.K.`) and a single capital initial
  preceding a capitalized name are protected. These intentionally simple rules
  cannot infer whether an abbreviation also ends a sentence.
- Block starts/ends flush a text unit: paragraphs, headings, list/definition
  items, summaries/details, sections, containers, table rows and the other
  structural elements enumerated in `BLOCKS` in the checker. A nonempty trailing
  **alphabetic** fragment counts as one sentence unit even without punctuation.
  Thus a heading is a fragment, not silently appended to the next paragraph.
- A table **row**, not each cell, is one unit before punctuation splitting.
  Cells are joined with spaces. Numeric-only rows/fragments add **no sentences**.
  `<br>` is whitespace, never an automatic sentence boundary; long source labels
  do not gain fake sentences merely because they wrap onto several lines.
- Inline elements, quotes and links never create sentence boundaries. Whitespace
  is collapsed. Punctuation-only fragments contribute nothing. This treatment
  of headings and other fragments is explicit because HTML is not just prose;
  different tools may choose different conventions and produce different grades.

## Syllables: dictionary first, explicit estimates

The dependency is pinned to **cmudict 1.1.3**, which bundles the CMU Pronouncing
Dictionary. No network calls, corpus downloads, host dictionaries, locale-specific
services or randomized models occur during checking. A word is looked up
case-insensitively; syllables are the ARPABET phonemes ending in a stress digit.
For multiple pronunciations the **minimum** count is used, independent of entry
ordering (for example, `fire` has a one-syllable pronunciation). This is a declared
US-English convention; UK pronunciation can differ.

If there is no dictionary entry:

1. An all-uppercase token is spelled as letters, one syllable each except `W`
   (three). Dictionary entries take precedence for recognized acronyms.
2. A possessive ending `'s` inherits a known base word's count.
3. Otherwise count `[aeiouy]+` groups after removing apostrophes. Subtract one
   for final silent `e` except `le`/`ye`, for final `es` except
   `ses/xes/zes/ches/shes`, and for final `ed` except `ted/ded`, only while the
   count exceeds one. The minimum is one syllable.

The last step is an **approximation**, not a reliable pronunciation dictionary
for every invented or specialist word. Every such estimated word is printed in
sorted order for review; none are omitted from the score. There is no site-word
override list or tuning to make a page pass. The dictionary handles the ordinary
and difficult English vocabulary; the fallback keeps unknown proper names and
technical terms deterministic while exposing the uncertainty.

## Regression coverage

[The regression tests](../scripts/test_reading_grade.py) run through
`python3 scripts/check.py --self-test`, alongside the existing source mutation
tests. They cover the formula, dictionary pronunciations, unknown words,
normalization, abbreviations/decimals/URLs/locators, inline markup, `<br>`, table
rows, numeric-only fragments, all-copy extraction, nested closed details,
quotes/source labels, recursive discovery of a newly added page, an unrounded
threshold, and integration into the main check. Deliberately difficult copy must
fail. Separate padding tests ensure neither numeric tables nor easy table labels
can mask difficult prose. Tests are offline and do not import the page builder.
