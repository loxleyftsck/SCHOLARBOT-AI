"""Backend-only Supabase RPC storage for serverless instances.

Failures never fall back to local disk or a per-instance quota.
"""
import os
import httpx
from fastapi import HTTPException


def configured():
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"))


def rpc(name, payload):
    if not configured():
        raise HTTPException(503, "Penyimpanan demo belum dikonfigurasi.")
    url = os.environ["SUPABASE_URL"].rstrip("/")
    if not url.startswith("https://"):
        raise HTTPException(503, "Konfigurasi penyimpanan demo tidak valid.")
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    try:
        response = httpx.post(url + "/rest/v1/rpc/" + name,
            headers={"apikey": key, "Authorization": "Bearer " + key},
            json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError):
        # Do not expose URLs, provider responses or credentials to visitors/logs.
        raise HTTPException(503, "Penyimpanan demo sedang tidak tersedia. Coba lagi nanti.") from None


def load(session_id):
    return rpc("scholarbot_load_session", {"p_id": session_id})


def save(session_id, payload, revision):
    result = rpc("scholarbot_save_session", {
        "p_id": session_id, "p_payload": payload, "p_revision": revision})
    if result is None:
        raise HTTPException(409, "Sesi berubah di permintaan lain. Muat ulang lalu coba lagi.")
    return result


def quota(minute_limit, day_limit):
    return rpc("scholarbot_take_quota", {
        "p_minute_limit": minute_limit, "p_day_limit": day_limit})
