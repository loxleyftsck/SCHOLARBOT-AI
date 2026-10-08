from collections import deque
from unittest.mock import patch
import time
import pytest
from fastapi.testclient import TestClient
import api

@pytest.fixture
def quota_client(monkeypatch):
    monkeypatch.setattr(api,"DEMO_REQUEST_TIMES",deque())
    monkeypatch.setattr(api,"DEMO_DAILY_REQUEST_TIMES",deque())
    monkeypatch.setattr(api,"DEMO_REQUESTS_PER_MINUTE",1)
    monkeypatch.setattr(api,"DEMO_REQUESTS_PER_DAY",100)
    with patch("api.chat",return_value='{"question":"Soal contoh","options":["A","B"],"answer":"A"}'),patch("api.persist_session"):
        yield TestClient(api.app)

@pytest.mark.parametrize("path",["/api/quiz","/api/quiz/"])
def test_get_quiz_is_limited_without_calling_provider_again(quota_client,path):
    first=quota_client.get(path)
    assert first.status_code==200
    with patch("api.chat") as provider:
        blocked=quota_client.get(path)
        assert blocked.status_code==429
        provider.assert_not_called()
    assert int(blocked.headers["retry-after"])>=1
    assert quota_client.get("/api/health").status_code==200

def test_daily_limit_cannot_be_bypassed_by_waiting_a_minute(quota_client,monkeypatch):
    monkeypatch.setattr(api,"DEMO_REQUESTS_PER_DAY",1)
    api.DEMO_DAILY_REQUEST_TIMES.append(time.monotonic()-61)
    assert quota_client.get("/api/quiz").status_code==429
    assert quota_client.get("/api/health").status_code==200

def test_expired_daily_requests_release_quota(quota_client):
    api.DEMO_DAILY_REQUEST_TIMES.append(time.monotonic()-86401)
    assert quota_client.get("/api/quiz").status_code==200
