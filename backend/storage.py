"""
Persistence layer for the live "products analyzed" counter and the
community product cache (the fallback for barcodes Open Food Facts
doesn't have).

Backed by Supabase's auto-generated REST API using plain `requests`
calls, or local JSON fallback.
"""
import os
import json
import time
from pathlib import Path
import requests

LOCAL_FALLBACK_PATH = Path(__file__).parent / ".local_store.json"


def _supabase_config():
    # 1. First check environment variables (FastAPI / Docker / Render / Cloud standard)
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if url and key:
        return url.rstrip("/"), key

    # 2. Fallback check for streamlit secrets if running under streamlit
    try:
        import streamlit as st
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
        if url and key:
            return url.rstrip("/"), key
    except Exception:
        pass

    return None, None


def is_using_supabase() -> bool:
    url, key = _supabase_config()
    return bool(url and key)


def _headers(key):
    return {"apikey": key, "Authorization": f"Bearer {key}"}


def _local_load():
    if LOCAL_FALLBACK_PATH.exists():
        try:
            return json.loads(LOCAL_FALLBACK_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"scan_count": 0, "cache": {}}


def _local_save(data):
    try:
        LOCAL_FALLBACK_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


# ---------------------------------------------------------------
# Live "products analyzed" counter
# ---------------------------------------------------------------
def get_scan_count() -> int:
    url, key = _supabase_config()
    if not url:
        return _local_load().get("scan_count", 0)

    try:
        resp = requests.get(
            f"{url}/rest/v1/scan_stats?select=total&id=eq.1",
            headers=_headers(key),
            timeout=8,
        )
        resp.raise_for_status()
        rows = resp.json()
        return rows[0]["total"] if rows else 0
    except Exception:
        return _local_load().get("scan_count", 0)


def increment_scan_count() -> int:
    """
    Increments via a Postgres RPC function rather than a
    read-then-write from here, so concurrent users don't race each
    other and undercount.
    """
    url, key = _supabase_config()
    if not url:
        data = _local_load()
        data["scan_count"] = data.get("scan_count", 0) + 1
        _local_save(data)
        return data["scan_count"]

    try:
        resp = requests.post(
            f"{url}/rest/v1/rpc/increment_scan_total",
            headers={**_headers(key), "Content-Type": "application/json"},
            json={},
            timeout=8,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        data = _local_load()
        data["scan_count"] = data.get("scan_count", 0) + 1
        _local_save(data)
        return data["scan_count"]


# ---------------------------------------------------------------
# Community product cache — fills gaps Open Food Facts doesn't cover.
# Every barcode someone manually resolves gets saved here, so the next
# person who scans the same code gets an instant hit instead of another
# "not found".
# ---------------------------------------------------------------
def cache_get(barcode: str):
    url, key = _supabase_config()
    if not url:
        return _local_load().get("cache", {}).get(barcode)

    try:
        resp = requests.get(
            f"{url}/rest/v1/product_cache?barcode=eq.{barcode}&select=data",
            headers=_headers(key),
            timeout=8,
        )
        resp.raise_for_status()
        rows = resp.json()
        return rows[0]["data"] if rows else None
    except Exception:
        return _local_load().get("cache", {}).get(barcode)


def cache_set(barcode: str, data: dict):
    url, key = _supabase_config()
    if not url:
        local = _local_load()
        if "cache" not in local:
            local["cache"] = {}
        local["cache"][barcode] = data
        _local_save(local)
        return

    try:
        requests.post(
            f"{url}/rest/v1/product_cache",
            headers={
                **_headers(key),
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates",
            },
            json={"barcode": barcode, "data": data, "updated_at": int(time.time())},
            timeout=8,
        )
    except Exception:
        local = _local_load()
        if "cache" not in local:
            local["cache"] = {}
        local["cache"][barcode] = data
        _local_save(local)
