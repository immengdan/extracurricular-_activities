"""recursive_scanner.py

Renamed entry point: this file contains the recursive, rate-limited URL
responsiveness checker. It was previously named `index.py`.

See README.md for usage examples and safety notes.
"""

import argparse
import csv
import logging
import threading
import time
import sys
from datetime import datetime
from typing import List, Optional, Tuple

import requests
from pathlib import Path

SUFFIX = ".onrender.com"

def recursive_check(prefix: str,
                    index: int,
                    max_index: int,
                    step: int,
                    timeout: float,
                    delay: float,
                    results: List[Tuple[str, Optional[int]]],
                    dry_run: bool,
                    valid_codes: Optional[List[int]],
                    stop_event: threading.Event):
    if stop_event.is_set():
        return
    if index > max_index:
        return

    url = f"{prefix}{index:04d}{SUFFIX}"

    if dry_run:
        print(f"[dry-run] would check: {url}")
    else:
        try:
            resp = requests.head(url, timeout=timeout, allow_redirects=True)
            status = resp.status_code
        except requests.RequestException:
            status = None

        if status is not None:
            if (valid_codes is None) or (status in valid_codes):
                print(f"Responsive: {url} status={status}")
                results.append((url, status))

    if delay > 0:
        try:
            time.sleep(delay)
        except KeyboardInterrupt:
            stop_event.set()
            return

    recursive_check(prefix, index + step, max_index, step, timeout, delay, results, dry_run, valid_codes, stop_event)


def scan_prefix(prefix: str,
                max_index: int,
                concurrency: int,
                timeout: float,
                delay: float,
                dry_run: bool,
                valid_codes: Optional[List[int]]):
    results: List[Tuple[str, Optional[int]]] = []
    stop_event = threading.Event()
    threads: List[threading.Thread] = []

    for shard_start in range(concurrency):
        t = threading.Thread(
            target=recursive_check,
            args=(prefix, shard_start, max_index, concurrency, timeout, delay, results, dry_run, valid_codes, stop_event),
            daemon=True,
        )
        threads.append(t)
        t.start()

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        stop_event.set()
        print("Interrupted, stopping...")

    return results


def parse_args():
    p = argparse.ArgumentParser(description="Recursive, rate-limited URL responsiveness checker")
    p.add_argument("--max-per-prefix", type=int, default=10000, help="max index to check per prefix (inclusive). Default: 10000")
    p.add_argument("--concurrency", type=int, default=4, help="number of concurrent recursive shards (threads). Default: 4")
    p.add_argument("--timeout", type=float, default=1.0, help="request timeout in seconds. Default: 1.0")
    p.add_argument("--delay", type=float, default=0.05, help="delay between requests per shard in seconds. Default: 0.05")
    p.add_argument("--dry-run", action="store_true", help="do not make network requests; print planned checks")
    p.add_argument("--valid-codes", type=str, default=None, help="comma-separated HTTP status codes considered valid (e.g. 200,302). If omitted, any response counts as responsive")
    p.add_argument("--prefixes", type=str, default=None, help="optional comma-separated list of prefixes to scan (overrides built-in list)")
    p.add_argument("--confirm-authorized", action="store_true", help="confirm you have permission to scan these targets; required to perform network requests")
    p.add_argument("--log-file", type=str, default="scan.log", help="path to the log file")
    p.add_argument("--csv-file", type=str, default="scan_results.csv", help="path to the CSV summary output")
    return p.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(args.log_file), logging.StreamHandler(sys.stdout)],
    )

    if args.dry_run:
        logging.info("Dry run: no network requests will be made")

    if (not args.dry_run) and (not args.confirm_authorized):
        logging.error("Network operations are disabled unless you pass --confirm-authorized. Use --dry-run to preview.")
        sys.exit(1)

    # Determine prefixes (order of preference):
    # 1) --prefixes CLI argument (comma-separated)
    # 2) prefixes.txt file in repo root (one prefix per line)
    prefixes: List[str] = []
    if args.prefixes:
        prefixes = [p.strip() for p in args.prefixes.split(",") if p.strip()]
    else:
        prefixes_path = Path("prefixes.txt")
        if prefixes_path.exists():
            try:
                with prefixes_path.open("r", encoding="utf-8") as f:
                    file_prefixes = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
                if file_prefixes:
                    prefixes = file_prefixes
                    logging.info("Loaded %d prefixes from %s", len(prefixes), prefixes_path)
            except Exception:
                logging.exception("Failed to read prefixes from %s", prefixes_path)

    if not prefixes:
        logging.error("No prefixes provided. Create a prefixes.txt file or pass --prefixes.")
        sys.exit(1)

    valid_codes = None
    if args.valid_codes:
        try:
            valid_codes = [int(x) for x in args.valid_codes.split(",")]
        except ValueError:
            print("Invalid --valid-codes value; use comma-separated integers like 200,302")
            sys.exit(1)

    all_results: List[Tuple[str, Optional[int]]] = []

    for prefix in prefixes:
        print(f"Scanning prefix: {prefix} (0..{args.max_per_prefix}) with concurrency={args.concurrency}")
        results = scan_prefix(prefix, args.max_per_prefix, args.concurrency, args.timeout, args.delay, args.dry_run, valid_codes)
        all_results.extend(results)

    if all_results:
        logging.info("Responsive links found: %d", len(all_results))
        for url, status in all_results:
            logging.info("%s -> %s", url, status)
    else:
        logging.info("No responsive links found (or dry-run).")

    try:
        with open(args.csv_file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["timestamp", "prefix", "url", "status"])
            for url, status in all_results:
                # find which prefix this url belongs to (from the loaded prefixes)
                prefix = next((p for p in prefixes if url.startswith(p)), "" )
                writer.writerow([datetime.utcnow().isoformat(), prefix, url, status])
        logging.info("Wrote CSV summary to %s", args.csv_file)
    except Exception as e:
        logging.exception("Failed to write CSV file: %s", e)


if __name__ == "__main__":
    try:
        sys.setrecursionlimit(30000)
    except Exception:
        pass
    main()
