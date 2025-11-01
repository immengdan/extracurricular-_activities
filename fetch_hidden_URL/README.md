# fetch_hidden_URL

Small utility to fetch the HTML of a URL.

Usage

From the `fetch_hidden_URL` directory:

```bash
python fetch_url.py -u https://example.com
python fetch_url.py -u https://example.com -o example.html
```

Options

- `-u/--url` : URL to fetch (required)
- `-o/--output` : optional output file to save HTML. If omitted, HTML is printed to stdout.
- `--timeout` : request timeout in seconds (default 10.0)
- `--retries` : number of retries (default 3)
- `--no-verify` : disable TLS certificate verification (not recommended)

Notes

- This script uses `requests` and `urllib3` Retry. Install dependencies if needed:

```bash
pip install requests urllib3
```
