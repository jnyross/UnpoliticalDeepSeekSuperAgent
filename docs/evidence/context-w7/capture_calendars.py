#!/usr/bin/env python3
"""Bounded public-calendar capture; no release-date inference or source refresh.

Standard library only. Default: eight named GETs, no retries, 25-second socket
 timeout, 4 MiB body limit, at most four workers. Re-runs create a new UTC run
 directory, never overwrite previous captures. HTTP errors retain their bodies;
 transport failures retain the actual exception, with no invented body/hash.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

TARGETS = {
    'hmt-announcements': 'https://www.gov.uk/government/statistics/announcements?organisations%5B%5D=hm-treasury',
    'hmt-announcements-api': 'https://www.gov.uk/api/search.json?filter_format=statistics_announcement&filter_organisations=hm-treasury&count=100',
    'pesa-announcements-api': 'https://www.gov.uk/api/search.json?filter_format=statistics_announcement&q=public%20expenditure%20statistical%20analyses&count=100',
    'hmt-spending-collection': 'https://www.gov.uk/api/content/government/collections/national-statistics-release',
    'hmt-pesa-collection': 'https://www.gov.uk/api/content/government/collections/public-expenditure-statistical-analyses-pesa',
    'obr-data': 'https://obr.uk/data/',
    'obr-home': 'https://obr.uk/',
    # The first ONS request intentionally remains recorded: inspection showed
    # query= is ignored; the calendar form uses keywords= instead.
    'ons-psf-calendar': 'https://www.ons.gov.uk/releasecalendar?query=public%20sector%20finances&release-type=type-upcoming',
    'ons-psf-keywords': 'https://www.ons.gov.uk/releasecalendar?keywords=public%20sector%20finances&release-type=type-upcoming',
    'obr-databanks-year': 'https://obr.uk/public-finances-databank-2026-27/',
    'obr-monthly-listing': 'https://obr.uk/monthly-public-finances-briefing/',
}
DEFAULT_TARGETS = list(TARGETS)[:8]


def now():
    return datetime.now(timezone.utc).isoformat()


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.hidden += 1
        if tag == 'a':
            href = dict(attrs).get('href')
            if href:
                self.links.append(href)

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, text):
        if not self.hidden and text.strip():
            self.parts.append(' '.join(text.split()))


class Redirects(urllib.request.HTTPRedirectHandler):
    def __init__(self, records):
        self.records = records

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.records.append({'observed_at': now(), 'url': req.full_url,
                             'status': code, 'location': newurl,
                             'headers': list(headers.items())})
        if urllib.parse.urlparse(newurl).hostname not in (
                'www.gov.uk', 'gov.uk', 'obr.uk', 'www.obr.uk',
                'www.ons.gov.uk', 'ons.gov.uk'):
            raise ValueError('Refused redirect outside bounded official hosts')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def capture(item, output):
    name, url = item
    record = {'id': name, 'requested_url': url, 'started_at': now(),
              'method': 'GET', 'redirects': [], 'status': None, 'body_file': None,
              'sha256': None, 'error': None}
    request = urllib.request.Request(url, headers={
        'User-Agent': 'UnpoliticalAF-bounded-calendar-evidence/1.0',
        'Accept-Encoding': 'identity',
    })
    record['request_headers'] = dict(request.header_items())
    opener = urllib.request.build_opener(Redirects(record['redirects']))
    response = None
    try:
        try:
            response = opener.open(request, timeout=25)
        except urllib.error.HTTPError as exc:
            response = exc
            record['error'] = {'type': type(exc).__name__, 'message': str(exc)}
        with response:
            record['status'] = response.status
            record['final_url'] = response.geturl()
            record['response_headers'] = list(response.headers.items())
            body = response.read(4 * 1024 * 1024 + 1)
            record['truncated'] = len(body) > 4 * 1024 * 1024
            body_path = output / (name + '.body')
            body_path.write_bytes(body)
            record.update(body_file=body_path.name, bytes=len(body),
                          sha256=hashlib.sha256(body).hexdigest())
            decoded = body.decode(response.headers.get_content_charset() or 'utf-8', errors='replace')
            if 'json' in response.headers.get('Content-Type', ''):
                try:
                    parsed = json.loads(decoded)
                    (output / (name + '.view.txt')).write_text(json.dumps(parsed, indent=2, ensure_ascii=False) + '\n')
                except ValueError as exc:
                    record['parse_error'] = str(exc)
            else:
                text = Text()
                text.feed(decoded)
                (output / (name + '.view.txt')).write_text('\n'.join(text.parts) + '\n')
                (output / (name + '.links.json')).write_text(json.dumps(sorted(set(text.links)), indent=2) + '\n')
    except Exception as exc:
        record['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    record['finished_at'] = now()
    (output / (name + '.metadata.json')).write_text(json.dumps(record, indent=2) + '\n')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', nargs='+', choices=TARGETS, default=DEFAULT_TARGETS)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent / 'calendars')
    args = parser.parse_args()
    run = args.output / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    run.mkdir(parents=True, exist_ok=False)
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(lambda item: capture(item, run), [(key, TARGETS[key]) for key in args.only]))
    report = {'captured_at': now(), 'scope': 'bounded official calendar alternatives, not source audit',
              'request_count': len(records), 'records': records}
    (run / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    for record in records:
        print(record['id'], record['status'], record['sha256'], record['error'])
    print('Report:', run / 'report.json')
    # Persist every result before signalling a failed/incomplete capture to CLI.
    if any(record['error'] is not None or record.get('truncated')
           or record.get('parse_error') for record in records):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
