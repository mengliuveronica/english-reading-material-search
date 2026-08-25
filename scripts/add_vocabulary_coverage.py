#!/usr/bin/env python3
"""Add compact, versioned curriculum-vocabulary coverage to a Material Pack."""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from material_pack_validation import is_http_url, load_pack, validate_pack
from vocabulary_coverage_api import CoverageContractError, coverage_from_api
from vocabulary_coverage_contract import PACK_SCHEMA_VERSION

DEFAULT_API_URL = "https://vocabprofiler.netlify.app/api/analyze"
API_URL_ENV = "VOCAB_PROFILE_API_URL"
DEFAULT_TIMEOUT = 10.0
DEFAULT_MAX_RESPONSE_BYTES = 1024 * 1024
HEADER_NAME_RE = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
PROTECTED_HEADERS = {"content-length", "content-type", "host", "transfer-encoding"}


class AdapterError(RuntimeError):
    """A safe, user-facing adapter failure."""


def resolve_api_url(cli_url: str | None) -> str:
    """Use CLI override, then environment override, then the owned service."""
    return cli_url or os.environ.get(API_URL_ENV) or DEFAULT_API_URL


def material_text(material: dict[str, Any]) -> str:
    """Join every original block in source order without changing its text."""
    return "\n\n".join(block["text"] for block in material["original_text"]["blocks"])


def parse_header(raw: str) -> tuple[str, str]:
    if "=" not in raw:
        raise AdapterError("--header must use NAME=VALUE")
    name, value = raw.split("=", 1)
    if not HEADER_NAME_RE.fullmatch(name) or name.lower() in PROTECTED_HEADERS:
        raise AdapterError(f"unsafe or protected header name: {name!r}")
    if "\r" in value or "\n" in value:
        raise AdapterError(f"header {name!r} contains a newline")
    return name, value


def build_headers(raw_headers: list[str], api_key_env: str | None, api_key_header: str) -> dict[str, str]:
    headers = {"Accept": "application/json", "Content-Type": "application/json; charset=utf-8"}
    for raw in raw_headers:
        name, value = parse_header(raw)
        headers[name] = value
    if api_key_env:
        if not ENV_NAME_RE.fullmatch(api_key_env):
            raise AdapterError("--api-key-env must be an environment-variable name")
        if not HEADER_NAME_RE.fullmatch(api_key_header) or api_key_header.lower() in PROTECTED_HEADERS:
            raise AdapterError("--api-key-header is unsafe or protected")
        value = os.environ.get(api_key_env)
        if not value:
            raise AdapterError(f"API credential environment variable {api_key_env!r} is not set")
        if "\r" in value or "\n" in value:
            raise AdapterError("API credential contains a newline")
        headers[api_key_header] = value
    return headers


def _read_limited(response: Any, limit: int) -> bytes:
    length = response.headers.get("Content-Length")
    if length:
        try:
            if int(length) > limit:
                raise AdapterError(f"API response exceeds {limit} bytes")
        except ValueError as exc:
            raise AdapterError("API returned an invalid Content-Length") from exc
    body = response.read(limit + 1)
    if len(body) > limit:
        raise AdapterError(f"API response exceeds {limit} bytes")
    return body


def request_coverage(
    api_url: str,
    material: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
    max_response_bytes: int,
) -> dict[str, Any]:
    payload = {
        "text": material_text(material),
        "title": material["source_metadata"]["title"],
        "mode": "compact",
    }
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = Request(api_url, data=data, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            if not is_http_url(response.geturl()):
                raise AdapterError("API redirected to a non-http(s) URL")
            body = _read_limited(response, max_response_bytes)
        decoded = json.loads(body.decode("utf-8"))
        return coverage_from_api(decoded)
    except AdapterError:
        raise
    except HTTPError as exc:
        raise AdapterError(f"API returned HTTP {exc.code}") from exc
    except (TimeoutError, socket.timeout) as exc:
        raise AdapterError(f"API timed out after {timeout:g} seconds") from exc
    except URLError as exc:
        reason = "timeout" if isinstance(exc.reason, (TimeoutError, socket.timeout)) else "connection error"
        raise AdapterError(f"API {reason}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterError("API response is not valid UTF-8 JSON") from exc
    except CoverageContractError as exc:
        raise AdapterError(f"API response contract error: {exc}") from exc
    except OSError as exc:
        raise AdapterError(f"API I/O error: {exc}") from exc


def enrich_pack(
    pack: dict[str, Any],
    api_url: str,
    headers: dict[str, str],
    timeout: float,
    max_response_bytes: int,
) -> int:
    coverages: list[dict[str, Any]] = []
    for material in pack["materials"]:
        try:
            coverage = request_coverage(api_url, material, headers, timeout, max_response_bytes)
        except AdapterError as exc:
            raise AdapterError(f"{material['id']}: {exc}") from exc
        coverages.append(coverage)
    for material, coverage in zip(pack["materials"], coverages):
        material["curriculum_vocabulary_coverage"] = coverage
    pack["schema_version"] = PACK_SCHEMA_VERSION
    return len(coverages)


def write_json_atomic(path: Path, pack: dict[str, Any]) -> None:
    parent = path.parent
    if not parent.is_dir():
        raise AdapterError(f"output directory does not exist: {parent}")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=parent, prefix=f".{path.name}.", delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(pack, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except (OSError, UnicodeError) as exc:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise AdapterError(f"cannot write output atomically: {exc}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="validated material-pack.json")
    parser.add_argument(
        "--api-url", help=f"optional endpoint override (env: {API_URL_ENV}; default: owned production service)"
    )
    parser.add_argument("--output", required=True, type=Path, help="destination JSON; may equal input")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="per-request seconds (default: 10)")
    parser.add_argument(
        "--max-response-bytes", type=int, default=DEFAULT_MAX_RESPONSE_BYTES,
        help="maximum response body per Material (default: 1048576)",
    )
    parser.add_argument("--header", action="append", default=[], metavar="NAME=VALUE", help="repeatable non-secret request header")
    parser.add_argument("--api-key-env", help="environment variable containing the complete credential header value")
    parser.add_argument("--api-key-header", default="Authorization", help="credential header name (default: Authorization)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        api_url = resolve_api_url(args.api_url)
        if not is_http_url(api_url):
            raise AdapterError("API URL must be a valid http:// or https:// URL without credentials")
        if not 0 < args.timeout <= 300:
            raise AdapterError("--timeout must be greater than 0 and at most 300 seconds")
        if not 0 < args.max_response_bytes <= 10 * 1024 * 1024:
            raise AdapterError("--max-response-bytes must be between 1 and 10485760")
        headers = build_headers(args.header, args.api_key_env, args.api_key_header)
        pack, read_errors = load_pack(args.input)
        errors = read_errors or validate_pack(pack)
        if errors:
            raise AdapterError("input validation failed:\n- " + "\n- ".join(errors))
        analyzed = enrich_pack(pack, api_url, headers, args.timeout, args.max_response_bytes)
        final_errors = validate_pack(pack)
        if final_errors:
            raise AdapterError("enriched output validation failed:\n- " + "\n- ".join(final_errors))
        write_json_atomic(args.output, pack)
    except AdapterError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: wrote schema {PACK_SCHEMA_VERSION} to {args.output} ({analyzed} analyzed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
