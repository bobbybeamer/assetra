#!/usr/bin/env python3
import argparse
import json
import sys
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


@dataclass
class ApiResult:
    status: int
    body: Any


def call_api(base_url: str, method: str, path: str, payload: dict | None = None, token: str | None = None, tenant_id: str | None = None) -> ApiResult:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id

    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(f"{base_url}{path}", data=body, method=method, headers=headers)

    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return ApiResult(status=response.status, body=json.loads(raw) if raw else {})
    except HTTPError as error:
        raw = error.read().decode("utf-8")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"raw": raw}
        return ApiResult(status=error.code, body=parsed)
    except URLError as error:
        return ApiResult(status=0, body={"error": str(error)})


def assert_status(step: str, result: ApiResult, allowed: set[int]) -> None:
    if result.status not in allowed:
        raise RuntimeError(f"{step} failed: HTTP {result.status} body={result.body}")


def run_smoke(base_url: str, username: str, password: str, tenant_id: str) -> list[dict[str, Any]]:
    report: list[dict[str, Any]] = []

    auth = call_api(base_url, "POST", "/api/v1/auth/token/", {"username": username, "password": password})
    assert_status("auth", auth, {200})
    token = auth.body["access"]
    report.append({"step": "auth", "status": auth.status})

    asset_tag = f"SMK-{str(uuid.uuid4())[:8].upper()}"
    barcode = f"QR-{asset_tag}"

    asset = call_api(
        base_url,
        "POST",
        "/api/v1/assets/",
        {"asset_tag": asset_tag, "name": "Smoke Asset", "barcode_value": barcode, "barcode_type": "qr"},
        token=token,
        tenant_id=tenant_id,
    )
    assert_status("asset_create", asset, {201})
    asset_id = asset.body["id"]
    report.append({"step": "asset_create", "status": asset.status, "asset_id": asset_id, "asset_tag": asset_tag})

    scan = call_api(
        base_url,
        "POST",
        "/api/v1/scan-events/",
        {"asset": asset_id, "symbology": "qr", "raw_value": barcode, "source_type": "camera"},
        token=token,
        tenant_id=tenant_id,
    )
    assert_status("scan_create", scan, {201})
    report.append({"step": "scan_create", "status": scan.status, "scan_id": scan.body.get("id")})

    sync = call_api(base_url, "POST", "/api/v1/sync/", {"scan_events": []}, token=token, tenant_id=tenant_id)
    assert_status("sync", sync, {200})
    report.append({"step": "sync", "status": sync.status, "asset_changes": len(sync.body.get("asset_changes", []))})

    webhook = call_api(
        base_url,
        "POST",
        "/api/v1/webhooks/",
        {"name": "Smoke Inbound", "direction": "inbound", "url": "https://example.com/inbound", "events": ["scan.created"]},
        token=token,
        tenant_id=tenant_id,
    )
    assert_status("webhook_create", webhook, {201})
    endpoint_id = webhook.body["id"]
    report.append({"step": "webhook_create", "status": webhook.status, "endpoint_id": endpoint_id})

    inbound = call_api(
        base_url,
        "POST",
        "/api/v1/webhooks/inbound/",
        {"endpoint_id": endpoint_id, "event_name": "scan.created", "payload": {"asset_id": asset_id}},
        token=token,
        tenant_id=tenant_id,
    )
    assert_status("webhook_inbound", inbound, {202})
    report.append({"step": "webhook_inbound", "status": inbound.status, "delivery_id": inbound.body.get("delivery_id")})

    validate = call_api(
        base_url,
        "POST",
        "/api/v1/barcodes/validate/",
        {"symbology": "qr", "raw_value": barcode},
        token=token,
        tenant_id=tenant_id,
    )
    assert_status("barcode_validate", validate, {200})
    report.append({"step": "barcode_validate", "status": validate.status, "valid": validate.body.get("valid")})

    lookup = call_api(base_url, "GET", f"/api/v1/lookups/assets/?barcode={quote(barcode)}", token=token, tenant_id=tenant_id)
    assert_status("lookup", lookup, {200})
    report.append({"step": "lookup", "status": lookup.status, "lookup_asset_id": lookup.body.get("id")})

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Assetra end-to-end smoke test")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--username", default="smoke_admin")
    parser.add_argument("--password", default="SmokePass123!")
    parser.add_argument("--tenant-id", default="1")
    args = parser.parse_args()

    try:
        report = run_smoke(args.base_url.rstrip("/"), args.username, args.password, args.tenant_id)
        print(json.dumps({"ok": True, "report": report}, indent=2))
        return 0
    except Exception as error:
        print(json.dumps({"ok": False, "error": str(error)}, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
