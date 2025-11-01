# Extracurricular Activities — Python project

## 1. recursive_scanner
when u know partial of the url link and try to get the useful ones
remember to create and add base_url in prefixes.txt at first

### change info here to do whatever u want
url = f"{prefix}{index:04d}{SUFFIX}"

Prerequisites
- macOS / Linux / Windows with WSL
- Python 3.8+ (this workspace uses a virtualenv created with the workspace Python)
- Optional: Git and the GitHub CLI (`gh`) for convenient repo creation

Setup (recommended)
Open a terminal in the repository root and run:

```bash
# create a virtualenv (if you don't have one already)
python -m venv .venv
# activate it (macOS / Linux)
source .venv/bin/activate
# (Windows PowerShell)
# .\.venv\Scripts\Activate.ps1

# install dependencies
pip install -r requirements.txt
```

Important: this tool performs network requests. You must either:
- run in `--dry-run` mode to preview the checks (recommended), or
- pass `--confirm-authorized` to acknowledge you have permission to scan the targets.

Before running real scans, add your base prefixes to `prefixes.txt` (one prefix per line), can see from prefixes.example.txt

Run the project (safe examples)

Preview the checks (no network requests):

```bash
python recursive_scanner.py --max-per-prefix 10 --concurrency 2 --dry-run
```

Run an authorized small test (only if you have permission):

```bash
python recursive_scanner.py --max-per-prefix 100 --concurrency 4 --timeout 1.0 --delay 0.1 --confirm-authorized --log-file scan.log --csv-file scan_results.csv
```

Notes: scanning large ranges (e.g. 0..10000 across many prefixes) may issue tens of thousands of requests — tune `--concurrency` and `--delay` appropriately and ensure you have authorization.

License

This project is licensed under the MIT License — see the included `LICENSE` file for the full text.

If you'd like a different copyright holder or year in the `LICENSE` file, tell me and I can update it (currently: 2025, iimengdan).

