#!/usr/bin/env python3
"""Check a compatible vocabulary service without sending teacher material."""

from __future__ import annotations

import argparse
import sys
from urllib.parse import urlsplit, urlunsplit

from add_vocabulary_coverage import (
    API_URL_ENV,
    DEFAULT_MAX_RESPONSE_BYTES,
    AdapterError,
    build_headers,
    request_coverage,
    resolve_api_url,
)
from material_pack_validation import is_http_url

CHECK_MATERIAL = {
    "source_metadata": {"title": "VocabProfiler connectivity check"},
    "original_text": {
        "blocks": [
            {"type": "title", "text": "VocabProfiler connectivity check"},
            {"type": "paragraph", "text": "Students read a short public article and discuss its main idea in class."},
        ]
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", help=f"optional endpoint override (env: {API_URL_ENV})")
    parser.add_argument("--timeout", type=float, default=5.0, help="request seconds (default: 5)")
    parser.add_argument("--max-response-bytes", type=int, default=DEFAULT_MAX_RESPONSE_BYTES)
    parser.add_argument("--header", action="append", default=[], metavar="NAME=VALUE")
    parser.add_argument("--api-key-env")
    parser.add_argument("--api-key-header", default="Authorization")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_url = resolve_api_url(args.api_url)
    parts = urlsplit(api_url)
    display_url = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    try:
        if not is_http_url(api_url):
            raise AdapterError("API URL must be a valid http:// or https:// URL without credentials")
        if not 0 < args.timeout <= 60:
            raise AdapterError("--timeout must be greater than 0 and at most 60 seconds")
        if not 0 < args.max_response_bytes <= 10 * 1024 * 1024:
            raise AdapterError("--max-response-bytes must be between 1 and 10485760")
        headers = build_headers(args.header, args.api_key_env, args.api_key_header)
        request_coverage(api_url, CHECK_MATERIAL, headers, args.timeout, args.max_response_bytes)
    except AdapterError as exc:
        print(f"FAIL: vocabulary service is unavailable at {display_url}: {exc}", file=sys.stderr)
        print(
            f"NEXT: configure {API_URL_ENV} or --api-url; if no compatible service is reachable, "
            "ask the user whether to create a basic delivery without vocabulary coverage.",
            file=sys.stderr,
        )
        return 1
    print(f"PASS: vocabulary service is reachable: {display_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
