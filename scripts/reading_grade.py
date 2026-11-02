#!/usr/bin/env python3
"""Deterministic full-copy Flesch–Kincaid check. See docs/reading-grade.md."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
import unicodedata

import cmudict

MAX_GRADE = 7.0
# Do not split inline markup or table cells into artificial sentences.
BLOCKS = frozenset('address article aside blockquote caption dd details div dl dt '
                   'fieldset figcaption figure footer form h1 h2 h3 h4 h5 h6 header '
                   'hr li main nav ol p pre section summary table title tr ul'.split())
TOKEN = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)*|\d+(?:[.,]\d+)*")
# Periods inside numbers, initials and the listed abbreviations are not stops.
ABBREVIATION = re.compile(r'\b(?:Mr|Mrs|Ms|Dr|Prof|St|vs|etc|e\.g|i\.e)\.', re.I)
INITIALS = re.compile(r'\b(?:[A-Za-z]\.){2,}|\b[A-Z]\.(?=\s+[A-Z][a-z])')


class GradeError(ValueError):
    pass


class CopyParser(HTMLParser):
    """Collect all text, including closed details, excluding only script/style data."""
    def __init__(self, *, prose_only=False):
        super().__init__(convert_charrefs=True)
        self.prose_only = prose_only
        self.prose_depth = 0
        self.blocks = []
        self.parts = []
        self.excluded = []

    def boundary(self):
        text = ' '.join(''.join(self.parts).split())
        if text:
            self.blocks.append(text)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style') or (self.prose_only and tag in ('table', 'svg')):
            self.boundary()
            self.excluded.append(tag)
        if self.excluded:
            return
        if tag in ('p', 'li', 'dd', 'blockquote'):
            self.prose_depth += 1
        if tag in BLOCKS:
            self.boundary()
        elif tag in ('td', 'th', 'a', 'text', 'tspan', 'br'):
            self.parts.append(' ')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.excluded:
            if tag == self.excluded[-1]:
                self.excluded.pop()
            return
        if tag in BLOCKS:
            self.boundary()
        elif tag in ('td', 'th', 'a', 'text', 'tspan'):
            self.parts.append(' ')
        if tag in ('p', 'li', 'dd', 'blockquote'):
            self.prose_depth = max(0, self.prose_depth - 1)

    def handle_data(self, data):
        if not self.excluded and (not self.prose_only or self.prose_depth):
            self.parts.append(data)

    def close(self):
        super().close()
        self.boundary()


def copy_blocks(html, *, prose_only=False):
    parser = CopyParser(prose_only=prose_only)
    parser.feed(html)
    parser.close()
    return parser.blocks


def tokens(text):
    # Canonical accents/curly apostrophes, no dependence on host locale.
    normalized = unicodedata.normalize('NFKD', text.replace('’', "'"))
    text = ''.join(char if char.isascii() else ' ' for char in normalized
                   if not unicodedata.combining(char))
    return TOKEN.findall(text)


@lru_cache(maxsize=1)
def pronunciations():
    return cmudict.dict()


def fallback_syllables(word):
    """Explicit approximation only for dictionary misses; surfaced in reports."""
    word = word.lower().replace("'", '')
    groups = len(re.findall(r'[aeiouy]+', word))
    if word.endswith('e') and not word.endswith(('le', 'ye')) and groups > 1:
        groups -= 1
    if word.endswith('es') and not word.endswith(('ses', 'xes', 'zes', 'ches', 'shes')) and groups > 1:
        groups -= 1
    if word.endswith('ed') and not word.endswith(('ted', 'ded')) and groups > 1:
        groups -= 1
    return max(1, groups)


@lru_cache(maxsize=None)
def syllables(token):
    if token[0].isdigit():
        return 1, False
    word = token.lower().replace('’', "'")
    choices = pronunciations().get(word)
    if choices:
        # Minimum across variants is independent of dictionary entry ordering.
        return min(sum(phone[-1:].isdigit() for phone in phones) for phones in choices), False
    if token.isupper():
        return sum(3 if letter == 'W' else 1 for letter in token if letter.isalpha()), False
    if word.endswith("'s") and word[:-2] in pronunciations():
        return syllables(word[:-2])
    return fallback_syllables(word), True


def sentence_count(block):
    # A URL or workbook locator is not a sequence of miniature sentences.
    masked = re.sub(r'(?:https?://|www\.)\S+',
                    lambda m: re.sub(r'[.!?]', '§', m[0].rstrip('.!?')) + m[0][len(m[0].rstrip('.!?')):], block)
    masked = re.sub(r'\b\d+_\d+![A-Za-z]+\d+\b', lambda m: m[0].replace('!', '§'), masked)
    masked = re.sub(r'(?<=\d)\.(?=\d)', '§', masked)
    masked = ABBREVIATION.sub(lambda m: m[0].replace('.', '§'), masked)
    masked = INITIALS.sub(lambda m: m[0].replace('.', '§'), masked)
    # Each nonempty trailing fragment counts too; punctuation-only pieces do not.
    return sum(any(word[0].isalpha() for word in tokens(piece))
               for piece in re.split(r'[.!?]+', masked))


@dataclass(frozen=True)
class Grade:
    words: int
    sentences: int
    syllables: int
    grade: float
    unknown: tuple[str, ...]
    verbal_words: int
    verbal_syllables: int
    verbal_grade: float
    prose_grade: float | None = None


def measure(html, *, prose_only=False):
    blocks = copy_blocks(html, prose_only=prose_only)
    words = [word for block in blocks for word in tokens(block)]
    sentences = sum(sentence_count(block) for block in blocks)
    if not words or not sentences:
        if prose_only:
            return None  # A table-only document is still assessed in full.
        raise GradeError('No readable words/sentences; an empty page cannot pass')
    counts = [syllables(word) for word in words]
    total = sum(count for count, _ in counts)
    grade = 0.39 * len(words) / sentences + 11.8 * total / len(words) - 15.59
    verbal_words = sum(word[0].isalpha() for word in words)
    verbal_syllables = sum(count for word, (count, _) in zip(words, counts) if word[0].isalpha())
    verbal_grade = 0.39 * verbal_words / sentences + 11.8 * verbal_syllables / verbal_words - 15.59
    prose = measure(html, prose_only=True) if not prose_only else None
    return Grade(len(words), sentences, total, grade,
                 tuple(sorted({word.lower() for word, (_, missing) in zip(words, counts) if missing})),
                 verbal_words, verbal_syllables, verbal_grade,
                 prose.verbal_grade if prose else None)


def scan(root):
    pages = sorted((Path(root) / 'site').rglob('*.html'))
    if not pages:
        raise GradeError('No site/**/*.html pages found')
    return {path: measure(path.read_text(encoding='utf-8')) for path in pages}


def validate(root, *, report_only=False):
    results = scan(root)
    failures = []
    for path, result in results.items():
        worst = max(result.grade, result.verbal_grade, result.prose_grade if result.prose_grade is not None else -float('inf'))
        status = 'PASS' if worst <= MAX_GRADE else 'FAIL'
        print(f'{status}: {path.relative_to(root)}: FK {result.grade:.4f}; '
              f'{result.words} words / {result.sentences} sentences / '
              f'{result.syllables} syllables; words-only FK {result.verbal_grade:.4f} '
              f'({result.verbal_words} words / {result.verbal_syllables} syllables); '
              f'non-table words-only FK {result.prose_grade if result.prose_grade is not None else "n/a"}; '
              f'{len(result.unknown)} dictionary misses')
        if result.unknown:
            print('  Estimated words: ' + ', '.join(result.unknown))
        if worst > MAX_GRADE:
            failures.append(f'{path.relative_to(root)} (all {result.grade:.4f}, words-only {result.verbal_grade:.4f}, non-table {result.prose_grade})')
    if failures and not report_only:
        raise GradeError('Flesch–Kincaid grade exceeds 7.0: ' + ', '.join(failures))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--report-only', action='store_true', help='report all grades without enforcing the limit')
    args = parser.parse_args()
    try:
        validate(args.root.resolve(), report_only=args.report_only)
    except (GradeError, OSError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
