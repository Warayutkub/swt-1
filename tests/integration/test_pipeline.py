"""เทสต์ระดับ integration - ต่อทุกชิ้นเข้าด้วยกันโดยใช้ไฟล์จริง

ต่างจาก unit test ตรงที่ตัวนี้ "แตะระบบไฟล์จริง" จึงช้ากว่า
แต่เป็นชั้นเดียวที่จับบั๊กแบบ "แต่ละชิ้นถูกหมด พอต่อกันแล้วพัง" ได้

ฟีเจอร์ที่ใช้: 6 fixture · 7 conftest ซ้อนชั้น · 8 scope=session · 13 marker
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from chatlog.errors import EmptyChatError
from chatlog.parser import parse_file, parse_text
from chatlog.report import write_report
from chatlog.stats import build_stats

pytestmark = pytest.mark.integration


def test_ไฟล์เข้าออกครบวงจร(project_dir: Path, sample_chat_text: str) -> None:
    """เส้นทางหลักของระบบทั้งเส้น: ไฟล์ .txt เข้า -> ไฟล์ .json ออก"""
    source = project_dir / "input" / "chat.txt"
    source.write_text(sample_chat_text, encoding="utf-8")

    messages = parse_file(source)
    stats = build_stats(messages)
    target = write_report(stats, project_dir / "output" / "report.json")

    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["จำนวนข้อความ"] == 10
    assert data["แยกตามคน"] == {"มะลิ": 5, "ฉัน": 5}
    assert data["ตอบกลับเฉลี่ยนาที"] == 11.75


def test_อ่านไฟล์ที่ไม่มีอยู่จริง(project_dir: Path) -> None:
    with pytest.raises(FileNotFoundError):
        parse_file(project_dir / "input" / "ไม่มีไฟล์นี้.txt")


def test_ไฟล์ว่างเปล่า(project_dir: Path) -> None:
    empty = project_dir / "input" / "empty.txt"
    empty.write_text("", encoding="utf-8")

    with pytest.raises(EmptyChatError):
        parse_file(empty)


def test_รองรับชื่อไฟล์ภาษาไทย(project_dir: Path, sample_chat_text: str) -> None:
    """ไฟล์จริงจากมือถือมักมีชื่อเป็นภาษาไทย"""
    source = project_dir / "input" / "แชทกับมะลิ.txt"
    source.write_text(sample_chat_text, encoding="utf-8")

    assert len(parse_file(source)) == 10


def test_เขียนทับไฟล์เดิมได้(project_dir: Path, sample_chat_text: str) -> None:
    stats = build_stats(parse_text(sample_chat_text))
    target = project_dir / "output" / "report.json"

    write_report(stats, target)
    first = target.read_text(encoding="utf-8")
    write_report(stats, target)

    assert target.read_text(encoding="utf-8") == first


# ---------------------------------------------------------------------------
# ฟีเจอร์ที่ 8: fixture แบบ session - ไฟล์ก้อนใหญ่ สร้างครั้งเดียวใช้ทั้งการรัน
# ---------------------------------------------------------------------------
@pytest.mark.slow
def test_ไฟล์ขนาดใหญ่(project_dir: Path, big_chat_text: str) -> None:
    """ข้อความ 336 ข้อความ - ช้ากว่าเทสต์อื่นจึงติด marker slow ไว้

    ข้ามได้ด้วย  pytest -m "not slow"
    """
    source = project_dir / "input" / "big.txt"
    source.write_text(big_chat_text, encoding="utf-8")

    stats = build_stats(parse_file(source))

    assert stats.total_messages == 28 * 12
    assert stats.period_start.month == 8
    assert set(stats.by_sender) == {"มะลิ", "ฉัน"}
