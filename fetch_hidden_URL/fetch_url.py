"""Simple HTML fetcher (no argparse)

Usage (env/interactive):
 - Set FETCH_URL environment variable to the URL to fetch, and optionally FETCH_OUTPUT to save to a file.
   Example:
     FETCH_URL="https://example.com" FETCH_OUTPUT=page.html python fetch_html.py
 - If FETCH_URL is not set, the script will prompt you to type or paste the URL on stdin.
 - If FETCH_OUTPUT is not set, the HTML will be written to stdout.

This variant removes argparse entirely and uses environment variables (or an interactive prompt)
so there are no CLI argument parsers.
"""

from __future__ import annotations

import os
import sys
from typing import Dict, Optional, Tuple, Iterator

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


def fetch_html_stream(
	url: str,
	timeout: float = 10.0,
	retries: int = 3,
	backoff_factor: float = 0.3,
	headers: Optional[Dict[str, str]] = None,
	verify: bool = True,
	stream: bool = True,
) -> Tuple[int, Iterator[bytes]]:
	"""Fetch response as a byte stream for `url`.

	Returns (status_code, iterator_of_bytes). Raises requests.RequestException on network errors.
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

	resp = session.get(url, headers=use_headers, timeout=timeout, verify=verify, stream=stream)
	resp.raise_for_status()

	return resp.status_code, resp.iter_content(chunk_size=8192)


def _get_inputs_from_env_or_stdin() -> Tuple[str, Optional[str]]:
	"""
	Return (url, output_path).
	- URL preference order:
	  1) FETCH_URL env var
	  2) prompt the user on stdin
	- Output path:
	  - FETCH_OUTPUT env var or None (stdout)
	"""
	url = os.environ.get("FETCH_URL")
	if not url:
		# Prompt the user for a URL. If stdin is not interactive, read one line.
		if sys.stdin.isatty():
			try:
				url = input("Enter URL to fetch: ").strip()
			except EOFError:
				url = ""
		else:
			# Non-interactive stdin (e.g., piped). Read first non-empty line.
			lines = sys.stdin.read().splitlines()
			url = next((ln.strip() for ln in lines if ln.strip()), "")
	# Normalize empty to None to handle error below
	if not url:
		print("No URL provided. Set FETCH_URL environment variable or provide via stdin.", file=sys.stderr)
		raise SystemExit(2)

	output = os.environ.get("FETCH_OUTPUT")  # None => write to stdout
	return url, output


def main() -> int:
	# Configurable defaults (can be adjusted or made environment-driven if desired)
	timeout = float(os.environ.get("FETCH_TIMEOUT", "10.0"))
	retries = int(os.environ.get("FETCH_RETRIES", "3"))
	verify_env = os.environ.get("FETCH_VERIFY")
	# If FETCH_VERIFY is explicitly set to "0" or "false" (case-insensitive), disable verify.
	if verify_env is None:
		verify = True
	else:
		verify = not (verify_env.strip().lower() in ("0", "false", "no"))

	try:
		url, output = _get_inputs_from_env_or_stdin()
	except SystemExit as e:
		return int(e.code or 1)

	try:
		status, byte_iter = fetch_html_stream(url, timeout=timeout, retries=retries, verify=verify)
	except requests.RequestException as e:
		print(f"Error fetching {url}: {e}", file=sys.stderr)
		return 2

	if output:
		try:
			with open(output, "wb") as f:
				for chunk in byte_iter:
					if chunk:
						f.write(chunk)
		except OSError as e:
			print(f"Error writing to {output}: {e}", file=sys.stderr)
			return 3
		print(f"Saved {status} HTML to {output}")
	else:
		out = getattr(sys.stdout, "buffer", None)
		if out is None:
			# Fallback: decode using utf-8 with replacement for errors.
			for chunk in byte_iter:
				if chunk:
					sys.stdout.write(chunk.decode("utf-8", errors="replace"))
		else:
			for chunk in byte_iter:
				if chunk:
					out.write(chunk)
			out.flush()

	return 0


if __name__ == "__main__":
	raise SystemExit(main())