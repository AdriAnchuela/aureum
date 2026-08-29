"""One HTTP door for every connector: retries, timeouts, honest User-Agent.

FRED's WAF fingerprints clients and silently drops some requests-from-python
traffic (documented in the MarketLens paper, §5.8), so `fetch_text` can fall
back to a `curl` subprocess before giving up.
"""

from __future__ import annotations

import logging
import subprocess

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "aureum/0.1 (+github.com/AdriAnchuela/aureum)"
)
TIMEOUT = 30


def _session() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=1.0, status_forcelist=[429, 500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    s.headers["User-Agent"] = USER_AGENT
    return s


SESSION = _session()


def fetch_bytes(url: str) -> bytes:
    resp = SESSION.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.content


def fetch_text(url: str, curl_fallback: bool = False) -> str:
    try:
        resp = SESSION.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException:
        if not curl_fallback:
            raise
        log.warning("requests failed for %s, retrying via curl", url)
        out = subprocess.run(
            ["curl", "-sL", "--fail", "--max-time", str(TIMEOUT), "-A", USER_AGENT, url],
            capture_output=True,
            check=True,
        )
        return out.stdout.decode("utf-8", errors="replace")
