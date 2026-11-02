"""Local write-ahead receipts for non-atomic GitHub issue list/create delivery.

A successful create or an uncertain create is never blindly repeated in this workspace.
Receipts do not claim cross-workspace atomicity or replace the remote all-state markers.
"""
from contextlib import AbstractContextManager
import fcntl
import json
import os
from pathlib import Path


class IssueReceipts(AbstractContextManager):
    def __init__(self, path, repo):
        self.path = Path(path)
        # GitHub repository identity is case-insensitive, unlike JSON object keys.
        self.repo = repo.casefold()

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = self.path.with_suffix(self.path.suffix + '.lock').open('a')
        fcntl.flock(self.lock, fcntl.LOCK_EX)
        try:
            self.state = json.loads(self.path.read_text()) if self.path.exists() else {
                'schema_version': 1, 'repositories': {}}
            if (not isinstance(self.state, dict) or self.state.get('schema_version') != 1 or
                    not isinstance(self.state.get('repositories'), dict)):
                raise ValueError('Invalid issue delivery receipts')
            for repo, entries in self.state['repositories'].items():
                if not isinstance(repo, str) or not isinstance(entries, dict):
                    raise ValueError('Invalid issue delivery repository')
                for key, value in entries.items():
                    if (not isinstance(key, str) or not isinstance(value, dict) or
                            value.get('status') not in ('pending', 'created', 'reported')):
                        raise ValueError('Invalid issue delivery receipt')
                    if value['status'] == 'created' and not isinstance(value.get('url'), str):
                        raise ValueError('Missing created issue URL')
            # Preserve receipts written with older/mixed-case OWNER/REPO spellings.
            normalized = {}
            rank = {'pending': 0, 'reported': 1, 'created': 2}
            for repo, entries in self.state['repositories'].items():
                target = normalized.setdefault(repo.casefold(), {})
                for key, value in entries.items():
                    if key not in target or rank[value['status']] > rank[target[key]['status']]:
                        target[key] = value
            self.state['repositories'] = normalized
            self.entries = normalized.setdefault(self.repo, {})
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *args):
        fcntl.flock(self.lock, fcntl.LOCK_UN)
        self.lock.close()

    def save(self):
        pending = self.path.with_suffix(self.path.suffix + '.tmp')
        with pending.open('w') as out:
            json.dump(self.state, out, indent=2, sort_keys=True)
            out.write('\n')
            out.flush()
            os.fsync(out.fileno())
        pending.replace(self.path)
        directory = os.open(self.path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

    def reported(self, key):
        if self.entries.get(key, {}).get('status') not in ('created', 'reported'):
            self.entries[key] = {'status': 'reported'}
            self.save()

    def reserve(self, key):
        # Persist BEFORE asking GitHub: timeout/crash cannot authorize a blind retry.
        self.entries[key] = {'status': 'pending'}
        self.save()

    def created(self, key, url):
        self.entries[key] = {'status': 'created', 'url': url}
        self.save()
