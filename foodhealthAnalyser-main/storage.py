"""
Persistence layer for the live "products analyzed" counter and the
community product cache (the fallback for barcodes Open Food Facts
doesn't have).

Backed by Supabase's auto-generated REST API using plain `requests`
calls, deliberately not the full supabase-py SDK — that pulls in
several extra packages (postgrest, gotrue, realtime, storage3...) that
add import weight for no benefit here, and this app cares about
keeping cold starts light.

If SUPABASE_URL / SUPABASE_KEY aren't set in st.secrets, everything
falls back to a local JSON file so the app still runs out of the box
for local development. That local file is NOT reliable once deployed
on Streamlit Community Cloud — it can be wiped on redeploy — so the UI
flags fallback mode instead of silently pretending the counter is
permanent. See SETUP.md for the ~10 minute Supabase setup.
"""
import json
import time
from pathlib import Path

import requests
import streamlit as st

LOCAL_FALLBACK_PATH = Path(__file__).parent / ".local_store.json"


def _supabase_config():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
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
            return json.loads(LOCAL_FALLBACK_PATH.read_text())
        except Exception:
            pass
    return {"scan_count": 0, "cache": {}}


def _local_save(data):
    LOCAL_FALLBACK_PATH.write_text(json.dumps(data))


# ---------------------------------------------------------------
# Live "products analyzed" counter
# ---------------------------------------------------------------
def get_scan_count() -> int:
    url, key = _supabase_config()
    if not url:
        return _local_load()["scan_count"]

    resp = requests.get(
        f"{url}/rest/v1/scan_stats?select=total&id=eq.1",
        headers=_headers(key),
        timeout=8,
    )
    resp.raise_for_status()
    rows = resp.json()
    return rows[0]["total"] if rows else 0


def increment_scan_count() -> int:
    """
    Increments via a Postgres RPC function (see SETUP.md) rather than a
    read-then-write from here, so concurrent users don't race each
    other and undercount.
    """
    url, key = _supabase_config()
    if not url:
        data = _local_load()
        data["scan_count"] += 1
        _local_save(data)
        return data["scan_count"]

    resp = requests.post(
        f"{url}/rest/v1/rpc/increment_scan_total",
        headers={**_headers(key), "Content-Type": "application/json"},
        json={},
        timeout=8,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------
# Community product cache — fills gaps Open Food Facts doesn't cover.
# Every barcode someone manually resolves gets saved here, so the next
# person who scans the same code gets an instant hit instead of another
# "not found".
# ---------------------------------------------------------------
def cache_get(barcode: str):
    url, key = _supabase_config()
    if not url:
        return _local_load()["cache"].get(barcode)

    resp = requests.get(
        f"{url}/rest/v1/product_cache?barcode=eq.{barcode}&select=data",
        headers=_headers(key),
        timeout=8,
    )
    resp.raise_for_status()
    rows = resp.json()
    return rows[0]["data"] if rows else None


def cache_set(barcode: str, data: dict):
    url, key = _supabase_config()
    if not url:
        local = _local_load()
        local["cache"][barcode] = data
        _local_save(local)
        return

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
