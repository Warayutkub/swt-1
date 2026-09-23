"""ฟีเจอร์ที่ 7: conftest.py

ทุก fixture ในไฟล์นี้ใช้ได้จากทุกไฟล์เทสต์ในโฟลเดอร์นี้และโฟลเดอร์ย่อย
โดยไม่ต้อง import - pytest หาให้เอง
"""

from __future__ import annotations

import shutil
from datetime import date, datetime
from pathlib import Path

import pytest

from chatlog import clock
from chatlog.parser import parse_text

# ---------------------------------------------------------------------------
# ข้อมูลตัวอย่าง - เขียน \t ชัดเจนเพราะไฟล์ LINE ใช้ tab คั่น
# ---------------------------------------------------------------------------
SAMPLE_CHAT = "\n".join(
    [
        "[LINE] ประวัติแชทกับ มะลิ",
        "บันทึกเมื่อ: 2026/09/20 14:30",
        "",
        "2026/09/01 (อ)",
        "09:12\tมะลิ\tกินข้าวยัง",
        "09:15\tฉัน\tยังเลย กำลังจะไป",
        "09:15\tฉัน\tเดี๋ยวกินแล้วโทรหา",
        "23:47\tมะลิ\tถึงหอแล้วนะ",
        "23:58\tฉัน\tโอเค ฝันดี",
        "",
        "2026/09/02 (จ)",
        "00:30\tมะลิ\tยังไม่นอนอีก คิดถึง",
        "08:30\tมะลิ\t[รูปภาพ]",
        "08:31\tฉัน\tสวยจัง คิดถึง",
        "08:32\tฉัน\tถ่ายที่ไหน",
        "ตรงร้านกาแฟหน้าหอปะ",
        "22:10\tมะลิ\tคิดถึง เหมือนกัน",
    ]
)

#: วันที่ที่เราจะแกล้งบอกระบบว่าเป็น "วันนี้"
FROZEN_TODAY = date(2026, 9, 15)


@pytest.fixture
def sample_chat_text() -> str:
    """ข้อความดิบของไฟล์แชทตัวอย่าง"""
    return SAMPLE_CHAT


@pytest.fixture
def sample_messages(sample_chat_text: str):
    """ฟีเจอร์: fixture เรียกใช้ fixture ตัวอื่นได้ (ประกอบกันเป็นชั้น)"""
    return parse_text(sample_chat_text)


@pytest.fixture
def chat_file(tmp_path: Path, sample_chat_text: str) -> Path:
    """ฟีเจอร์ที่ 10: tmp_path - เขียนไฟล์จริงในที่ที่ pytest ลบให้เอง"""
    path = tmp_path / "chat.txt"
    path.write_text(sample_chat_text, encoding="utf-8")
    return path


@pytest.fixture
def workspace(tmp_path: Path):
    """ฟีเจอร์ที่ 6: fixture + yield - เห็น setup กับ teardown ชัด ๆ

    ก่อน yield = เตรียมของ | หลัง yield = เก็บกวาด (ทำงานแม้เทสต์จะพัง)
    """
    folder = tmp_path / "workspace"
    (folder / "out").mkdir(parents=True)
    yield folder
    shutil.rmtree(folder)


@pytest.fixture
def frozen_clock(monkeypatch: pytest.MonkeyPatch) -> date:
    """ฟีเจอร์ที่ 9: monkeypatch - ล็อกเวลาให้ผลเทสต์เหมือนเดิมทุกครั้ง

    ถ้าไม่ล็อก เทสต์เรื่อง "เดือนนี้" จะพังเองเมื่อเดือนเปลี่ยน
    """
    monkeypatch.setattr(clock, "today", lambda: FROZEN_TODAY)
    monkeypatch.setattr(clock, "now", lambda: datetime(2026, 9, 15, 12, 0))
    return FROZEN_TODAY


@pytest.fixture(scope="session")
def big_chat_text() -> str:
    """ฟีเจอร์ที่ 8: scope="session" - ของก้อนใหญ่ สร้างครั้งเดียวใช้ทั้งการรัน

    ระวัง: fixture แบบนี้ถูกแชร์ระหว่างเทสต์ ห้ามให้ใครแก้ค่ามัน
    """
    lines = ["2026/08/01 (ส)"]
    for day in range(1, 29):
        lines.append(f"2026/08/{day:02d} (x)")
        for hour in range(0, 24, 2):
            speaker = "มะลิ" if hour % 4 == 0 else "ฉัน"
            lines.append(f"{hour:02d}:00\t{speaker}\tข้อความที่ {day}-{hour}")
    return "\n".join(lines)
