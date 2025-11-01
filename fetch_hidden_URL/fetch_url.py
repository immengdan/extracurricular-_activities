
"""Simple HTML fetcher

Usage (CLI):
	python fetch_url.py -u https://example.com
	python fetch_url.py --url https://example.com -o page.html

This script fetches the HTML of a given URL with retries and a timeout.
"""

from __future__ import annotations

import argparse
import sys
from typing import Dict, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def _default_headers() -> Dict[str, str]:
	return {
		"User-Agent": (
			"Mozilla/5.0 (compatible; fetch_hidden_URL/1.0; +https://example.com)"
		),
		"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
	}


def fetch_html(
	url: str,
	timeout: float = 10.0,
	retries: int = 3,
	backoff_factor: float = 0.3,
	headers: Optional[Dict[str, str]] = None,
	verify: bool = True,
) -> Tuple[int, str]:
	"""Fetch HTML content for `url`.

	Returns (status_code, text). Raises requests.RequestException on network errors.
	"""

	session = requests.Session()

	retry = Retry(
		total=retries,
		read=retries,
		connect=retries,
		backoff_factor=backoff_factor,
		status_forcelist=(429, 500, 502, 503, 504),
		allowed_methods=frozenset(["GET", "HEAD"]),
	)

	adapter = HTTPAdapter(max_retries=retry)
	session.mount("http://", adapter)
	session.mount("https://", adapter)

	use_headers = _default_headers()
	if headers:
		use_headers.update(headers)

	resp = session.get(url, headers=use_headers, timeout=timeout, verify=verify)
	resp.raise_for_status()
	return resp.status_code, resp.text


def _build_argparser() -> argparse.ArgumentParser:
	p = argparse.ArgumentParser(description="Fetch HTML for a given URL")
	p.add_argument("-u", "--url", required=True, help="URL to fetch (http/https)")
	p.add_argument(
		"-o",
		"--output",
		help="Optional output file to save HTML. If omitted, prints to stdout.",
	)
	p.add_argument("--timeout", type=float, default=10.0, help="Request timeout in seconds")
	p.add_argument("--retries", type=int, default=3, help="Number of retries on failure")
	p.add_argument("--no-verify", dest="verify", action="store_false", help="Disable TLS cert verification (not recommended)")
	return p


def main(argv: Optional[list[str]] = None) -> int:
	argv = argv if argv is not None else sys.argv[1:]
	parser = _build_argparser()
	args = parser.parse_args(argv)

	try:
		status, html = fetch_html(args.url, timeout=args.timeout, retries=args.retries, verify=args.verify)
	except requests.RequestException as e:
		print(f"Error fetching {args.url}: {e}", file=sys.stderr)
		return 2

	if args.output:
		try:
			with open(args.output, "w", encoding="utf-8") as f:
				f.write(html)
		except OSError as e:
			print(f"Error writing to {args.output}: {e}", file=sys.stderr)
			return 3
		print(f"Saved {status} HTML to {args.output}")
	else:
		# Print HTML to stdout
		print(html)

	return 0


if __name__ == "__main__":
	raise SystemExit(main())

