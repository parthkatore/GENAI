"""
ArduinoMate - Day 3: Documentation Fetcher (app/fetch.py)
----------------------------------------------------------
Student  : Parth Dasharath Katore
Enroll   : 2124UCEM2079
Roll No  : 53

Downloads official Arduino reference .adoc files from
  https://github.com/arduino/reference-en
and saves them under  data/raw/

Includes:
  - Request timeouts (20 seconds)
  - HTTP error handling (raise_for_status)
  - Connection error handling
  - Retry logic (up to 3 attempts)
  - Downloads at least 3 real Arduino documentation files
"""

import time
import requests
from pathlib import Path

# ── Target directory ──────────────────────────────────────────────────────────
_ROOT    = Path(__file__).resolve().parent.parent
RAW_DIR  = _ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# ── Documents to download ─────────────────────────────────────────────────────
# Format: (local_filename, raw_githubusercontent_url)
DOCUMENTS = [
    (
        "digitalRead.adoc",
        "https://raw.githubusercontent.com/arduino/reference-en/master/"
        "Language/Functions/Digital%20IO/digitalRead.adoc"
    ),
    (
        "digitalWrite.adoc",
        "https://raw.githubusercontent.com/arduino/reference-en/master/"
        "Language/Functions/Digital%20IO/digitalWrite.adoc"
    ),
    (
        "pinMode.adoc",
        "https://raw.githubusercontent.com/arduino/reference-en/master/"
        "Language/Functions/Digital%20IO/pinMode.adoc"
    ),
    (
        "analogRead.adoc",
        "https://raw.githubusercontent.com/arduino/reference-en/master/"
        "Language/Functions/Analog%20IO/analogRead.adoc"
    ),
    (
        "analogWrite.adoc",
        "https://raw.githubusercontent.com/arduino/reference-en/master/"
        "Language/Functions/Analog%20IO/analogWrite.adoc"
    ),
    (
        "delay.adoc",
        "https://raw.githubusercontent.com/arduino/reference-en/master/"
        "Language/Functions/Time/delay.adoc"
    ),
    (
        "millis.adoc",
        "https://raw.githubusercontent.com/arduino/reference-en/master/"
        "Language/Functions/Time/millis.adoc"
    ),
    (
        "Serial_begin.adoc",
        "https://raw.githubusercontent.com/arduino/reference-en/master/"
        "Language/Functions/Communication/Serial/begin.adoc"
    ),
    (
        "Serial_print.adoc",
        "https://raw.githubusercontent.com/arduino/reference-en/master/"
        "Language/Functions/Communication/Serial/print.adoc"
    ),
    (
        "attachInterrupt.adoc",
        "https://raw.githubusercontent.com/arduino/reference-en/master/"
        "Language/Functions/External%20Interrupts/attachInterrupt.adoc"
    ),
]

TIMEOUT_SECONDS  = 20
MAX_RETRIES      = 3
RETRY_DELAY_SECS = 2


# ── Core download function ────────────────────────────────────────────────────

def download_file(url: str, dest: Path, retries: int = MAX_RETRIES) -> bool:
    """
    Download a single URL to dest.

    Parameters
    ----------
    url     : Full https URL of the .adoc file.
    dest    : Local Path where the file should be saved.
    retries : Number of retry attempts on transient errors.

    Returns
    -------
    bool  True on success, False on failure.
    """
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()          # raises on 4xx / 5xx

            dest.write_text(response.text, encoding="utf-8")
            print(f"  ✓  Saved  {dest.name}")
            return True

        except requests.exceptions.ConnectionError as e:
            print(f"  ✗  Connection error (attempt {attempt}/{retries}): {e}")
        except requests.exceptions.Timeout:
            print(f"  ✗  Timeout after {TIMEOUT_SECONDS}s (attempt {attempt}/{retries})")
        except requests.exceptions.HTTPError as e:
            print(f"  ✗  HTTP error: {e} — skipping {dest.name}")
            return False          # HTTP errors are not retryable
        except Exception as e:
            print(f"  ✗  Unexpected error (attempt {attempt}/{retries}): {e}")

        if attempt < retries:
            print(f"     Retrying in {RETRY_DELAY_SECS}s …")
            time.sleep(RETRY_DELAY_SECS)

    print(f"  ✗  Failed after {retries} attempts: {dest.name}")
    return False


def fetch_all_documents(documents: list = None, raw_dir: Path = None) -> dict:
    """
    Download all documents in the DOCUMENTS list.

    Parameters
    ----------
    documents : list of (filename, url) tuples.
                Defaults to the module-level DOCUMENTS list.
    raw_dir   : Destination directory. Defaults to data/raw/.

    Returns
    -------
    dict  { filename: True/False }  success map.
    """
    docs    = documents or DOCUMENTS
    dst_dir = raw_dir   or RAW_DIR

    print(f"\nFetching {len(docs)} Arduino documentation files …")
    print(f"Destination: {dst_dir}\n")

    results: dict = {}
    for filename, url in docs:
        dest = dst_dir / filename
        if dest.exists():
            print(f"  ↷  Already exists, skipping: {filename}")
            results[filename] = True
            continue
        results[filename] = download_file(url, dest)

    successful = sum(1 for v in results.values() if v)
    print(f"\nDownload complete: {successful}/{len(docs)} files saved.\n")
    return results


# ── Convenience re-download (force overwrite) ─────────────────────────────────

def force_refresh_all(raw_dir: Path = None) -> dict:
    """Delete cached files and re-download everything."""
    dst_dir = raw_dir or RAW_DIR
    for filename, _ in DOCUMENTS:
        path = dst_dir / filename
        if path.exists():
            path.unlink()
    return fetch_all_documents(raw_dir=dst_dir)


# ── Standalone execution ──────────────────────────────────────────────────────

if __name__ == "__main__":
    fetch_all_documents()
