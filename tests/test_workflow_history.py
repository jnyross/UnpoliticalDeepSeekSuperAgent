"""Guard history required by comprehension-kit git-show checks in automation.

Read the workflows' deliberately simple checkout blocks with the standard library;
this is a focused configuration guard, not a general-purpose YAML parser.
"""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


def main_checkout_has_full_history(workflow):
    # Stop at the next step: another action's options cannot satisfy this guard.
    steps = re.split(r'^      - ', workflow, flags=re.MULTILINE)[1:]
    for step in steps:
        if not re.match(r'uses: actions/checkout@[^\s]+\s*\n', step):
            continue
        # Scope options to this checkout's `with`, not a later env/run block.
        match = re.search(r'^        with:\s*\n((?:^          .*\n|^\s*\n)*)',
                          step, flags=re.MULTILINE)
        if match is None:
            continue
        options = match.group(1)
        if re.search(r'^          ref: main\s*$', options, flags=re.MULTILINE):
            return bool(re.search(r'^          fetch-depth: 0\s*$', options,
                                  flags=re.MULTILINE))
    return False


class WorkflowHistoryTests(unittest.TestCase):
    def test_main_checkouts_retain_pinned_comprehension_revisions(self):
        for name in ('discover.yml', 'deployment-timing.yml'):
            with self.subTest(workflow=name):
                workflow = (ROOT / '.github' / 'workflows' / name).read_text()
                self.assertTrue(
                    main_checkout_has_full_history(workflow),
                    f'{name}: main checkout needs fetch-depth: 0 for pinned kit tests')

    def test_guard_rejects_shallow_or_unrelated_fetch_depth(self):
        checkout = ('      - uses: actions/checkout@v4\n'
                    '        with:\n'
                    '          ref: main\n')
        self.assertTrue(main_checkout_has_full_history(checkout + '          fetch-depth: 0\n'))
        for suffix in ('', '          fetch-depth: 1\n',
                       '        env:\n          fetch-depth: 0\n',
                       '      - uses: example/other@v1\n'
                       '        with:\n          fetch-depth: 0\n',
                       '          # fetch-depth: 0\n'):
            with self.subTest(suffix=suffix):
                self.assertFalse(main_checkout_has_full_history(checkout + suffix))


if __name__ == '__main__':
    unittest.main()
