"""HTTP utilities: caching, rate limiting, retries."""
from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from norwegian_pipeline.config import CACHE_DIR, RATE_LIMIT_SECONDS, REQUEST_TIMEOUT, USER_AGENT

logger = logging.getLogger(__name__)

_last_request_at = 0.0


def _rate_limit() -> None:
    global _last_request_at
    elapsed = time.monotonic() - _last_request_at
    if elapsed < RATE_LIMIT_SECONDS:
        time.sleep(RATE_LIMIT_SECONDS - elapsed)
    _last_request_at = time.monotonic()


def cache_key(url: str, params: dict[str, Any] | None = None) -> str:
    payload = json.dumps({"url": url, "params": params or {}}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def cache_path(key: str, suffix: str = ".json") -> Path:
    return CACHE_DIR / f"{key}{suffix}"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    use_cache: bool = True,
    method: str = "GET",
    json_body: dict[str, Any] | None = None,
) -> Any:
    key = cache_key(url, {"params": params, "body": json_body, "method": method})
    path = cache_path(key)
    if use_cache and path.exists():
        logger.debug("Cache hit: %s", url)
        return json.loads(path.read_text(encoding="utf-8"))

    _rate_limit()
    req_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        req_headers.update(headers)

    logger.info("%s %s", method, url)
    response = requests.request(
        method,
        url,
        params=params,
        json=json_body,
        headers=req_headers,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    if use_cache:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_text(url: str, *, use_cache: bool = True) -> str:
    key = cache_key(url)
    path = cache_path(key, ".html")
    if use_cache and path.exists():
        return path.read_text(encoding="utf-8")

    _rate_limit()
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    text = response.text
    if use_cache:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return text


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def download_file(url: str, dest: Path, *, use_cache: bool = True) -> Path | None:
    if use_cache and dest.exists() and dest.stat().st_size > 0:
        return dest

    _rate_limit()
    dest.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading %s -> %s", url, dest)
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
            stream=True,
        )
        if response.status_code in (401, 403):
            logger.warning("Login wall at %s (%s)", url, response.status_code)
            return None
        response.raise_for_status()
        with dest.open("wb") as fh:
            for chunk in response.iter_content(chunk_size=8192):
                fh.write(chunk)
        if dest.stat().st_size == 0:
            dest.unlink(missing_ok=True)
            return None
        return dest
    except requests.RequestException as exc:
        logger.warning("Download failed for %s: %s", url, exc)
        return None
