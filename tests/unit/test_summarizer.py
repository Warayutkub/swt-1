"""เทสต์ส่วนที่คุยกับโลกภายนอก

ฟีเจอร์ที่ใช้: 2 raises · 9 monkeypatch (setattr / setenv / delenv)

หลักการสำคัญ: เทสต์ชุดนี้ต้องไม่ยิงเน็ตจริงแม้แต่ครั้งเดียว
เพราะเทสต์ที่พึ่งเน็ตจะช้า เสียเงิน และพังเองเวลาเน็ตล่ม
"""

from __future__ import annotations

import json

import pytest

from chatlog import summarizer
from chatlog.errors import MissingApiKeyError
from chatlog.stats import build_stats

pytestmark = pytest.mark.unit


@pytest.fixture
def stats(sample_messages):
    return build_stats(sample_messages)


class FakeResponse:
    """ของปลอมที่ทำตัวเหมือนผลลัพธ์ของ urlopen พอให้โค้ดเราใช้งานได้"""

    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc_info) -> bool:
        return False


# ---------------------------------------------------------------------------
# ส่วนที่บริสุทธิ์ เทสต์ได้ตรง ๆ ไม่ต้อง mock อะไรเลย
# ---------------------------------------------------------------------------
def test_คำสั่งที่ส่งให้_ai_มีตัวเลขจริง(stats) -> None:
    prompt = summarizer.build_prompt(stats)
    assert "10" in prompt
    assert "มะลิ" in prompt


def test_คำสั่งบอกช่วงเวลา(stats) -> None:
    assert "2026-09-01" in summarizer.build_prompt(stats)


# ---------------------------------------------------------------------------
# ฟีเจอร์ที่ 9: แทนที่ฟังก์ชันที่ยิงเน็ต
# ---------------------------------------------------------------------------
def test_summarize_ใช้ผลจาก_call_ai(stats, monkeypatch: pytest.MonkeyPatch) -> None:
    """แทน call_ai ด้วยของปลอม summarize จึงเทสต์ได้โดยไม่ต้องมีเน็ตหรือคีย์

    ที่ทำแบบนี้ได้เพราะ summarize เรียก call_ai ผ่านชื่อระดับโมดูล
    Python จึงไปหาค่าตอนเรียกจริง ไม่ใช่ตอน import
    """
    received = {}

    def fake_call_ai(prompt: str, *, timeout: float = 0) -> str:
        received["prompt"] = prompt
        return "สรุปปลอมสำหรับเทสต์"

    monkeypatch.setattr(summarizer, "call_ai", fake_call_ai)

    assert summarizer.summarize(stats) == "สรุปปลอมสำหรับเทสต์"
    assert "จำนวนข้อความทั้งหมด: 10" in received["prompt"]


def test_ไม่มีคีย์ต้องโยน_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """delenv ลบตัวแปรสภาพแวดล้อมชั่วคราว

    raising=False แปลว่า ถ้าไม่มีอยู่แล้วก็ไม่ต้องบ่น
    """
    monkeypatch.delenv(summarizer.API_KEY_ENV, raising=False)

    with pytest.raises(MissingApiKeyError, match=summarizer.API_KEY_ENV):
        summarizer.call_ai("อะไรก็ได้")


def test_call_ai_ส่งคีย์ไปในหัวข้อคำขอ(monkeypatch: pytest.MonkeyPatch) -> None:
    """setenv ใส่คีย์ปลอม + setattr แทน urlopen = ไม่มีอะไรออกเน็ตเลย"""
    monkeypatch.setenv(summarizer.API_KEY_ENV, "คีย์ปลอม")
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["auth"] = request.headers.get("Authorization")
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse({"summary": "สรุปจากเซิร์ฟเวอร์ปลอม"})

    monkeypatch.setattr(summarizer.urllib.request, "urlopen", fake_urlopen)

    assert summarizer.call_ai("คำสั่งทดสอบ") == "สรุปจากเซิร์ฟเวอร์ปลอม"
    assert captured["auth"] == "Bearer คีย์ปลอม"
    assert captured["body"]["prompt"] == "คำสั่งทดสอบ"
    assert captured["url"] == summarizer.API_URL
