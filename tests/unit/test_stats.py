"""เทสต์การคำนวณสถิติ

ฟีเจอร์ที่ใช้: 3 approx · 4 parametrize · 9 monkeypatch (ผ่าน frozen_clock)
"""

from __future__ import annotations

from datetime import datetime

import pytest

from chatlog.models import Kind, Message
from chatlog.stats import build_stats, count_words, filter_current_month

pytestmark = pytest.mark.unit


def test_นับจำนวนข้อความทั้งหมด(sample_messages) -> None:
    assert build_stats(sample_messages).total_messages == 10


def test_แยกตามคนพูด(sample_messages) -> None:
    assert build_stats(sample_messages).by_sender == {"มะลิ": 5, "ฉัน": 5}


def test_ช่วงเวลาครอบคลุมตั้งแต่ข้อความแรกถึงสุดท้าย(sample_messages) -> None:
    stats = build_stats(sample_messages)
    assert stats.period_start == datetime(2026, 9, 1).date()
    assert stats.period_end == datetime(2026, 9, 2).date()


def test_วันที่คุยเยอะสุดเมื่อเท่ากันให้เอาวันแรก(sample_messages) -> None:
    """ทั้งสองวันมี 5 ข้อความเท่ากัน - กฎของเราคือเอาวันที่มาก่อน"""
    assert build_stats(sample_messages).busiest_day == datetime(2026, 9, 1).date()


def test_นับข้อความช่วงดึก(sample_messages) -> None:
    assert build_stats(sample_messages).late_night_count == 1


# ---------------------------------------------------------------------------
# ฟีเจอร์ที่ 3: approx - ค่าเฉลี่ยเป็นทศนิยม เทียบตรง ๆ ไม่ปลอดภัย
# ---------------------------------------------------------------------------
def test_เวลาตอบกลับเฉลี่ย(sample_messages) -> None:
    """การตอบที่นับได้คือ 3, 11, 32, 1 นาที -> เฉลี่ย 11.75"""
    stats = build_stats(sample_messages)
    assert stats.average_reply_minutes == pytest.approx(11.75)


def test_ไม่มีการตอบกลับเลยให้เป็นศูนย์() -> None:
    messages = [Message(datetime(2026, 9, 1, 9, 0), "มะลิ", "สวัสดี", Kind.TEXT)]
    assert build_stats(messages).average_reply_minutes == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# กฎข้อ 3: รูปและสติกเกอร์ต้องไม่ถูกนับเป็นคำ
# ---------------------------------------------------------------------------
def test_คำที่ใช้บ่อย(sample_messages) -> None:
    words = dict(count_words(sample_messages))
    assert words["คิดถึง"] == 3


def test_รูปภาพไม่ถูกนับเป็นคำ(sample_messages) -> None:
    words = dict(count_words(sample_messages))
    assert "รูปภาพ" not in words


@pytest.mark.parametrize(
    "text, kind, should_count",
    [
        pytest.param("คิดถึงมาก", Kind.TEXT, True, id="ข้อความปกติ-นับ"),
        pytest.param("[รูปภาพ]", Kind.IMAGE, False, id="รูป-ไม่นับ"),
        pytest.param("[สติกเกอร์]", Kind.STICKER, False, id="สติกเกอร์-ไม่นับ"),
        pytest.param("☎ ไม่ได้รับสาย", Kind.CALL, False, id="สาย-ไม่นับ"),
    ],
)
def test_นับคำเฉพาะข้อความจริง(text: str, kind: Kind, should_count: bool) -> None:
    messages = [Message(datetime(2026, 9, 1, 9, 0), "มะลิ", text, kind)]
    assert bool(count_words(messages)) is should_count


@pytest.mark.parametrize(
    "text, expected_absent",
    [
        pytest.param("ก", "ก", id="คำสั้นเกินไปถูกตัด"),
        pytest.param("ครับ", "ครับ", id="คำที่ไม่มีความหมายถูกตัด"),
    ],
)
def test_คำที่ไม่ควรนับ(text: str, expected_absent: str) -> None:
    messages = [Message(datetime(2026, 9, 1, 9, 0), "มะลิ", text, Kind.TEXT)]
    assert expected_absent not in dict(count_words(messages))


def test_ไม่มีข้อความเลยต้องโยน_error() -> None:
    with pytest.raises(ValueError, match="อย่างน้อยหนึ่ง"):
        build_stats([])


# ---------------------------------------------------------------------------
# กฎข้อ 10 + ฟีเจอร์ที่ 9: "เดือนนี้" ขึ้นกับว่าวันนี้คือวันไหน
# ---------------------------------------------------------------------------
def test_กรองเฉพาะเดือนนี้(frozen_clock) -> None:
    """ล็อกวันนี้ไว้ที่ 15 ก.ย. 2569 เทสต์นี้จึงให้ผลเดิมตลอดไป

    ถ้าไม่ล็อก เทสต์จะผ่านเดือนกันยายน แล้วพังเองในเดือนตุลาคม
    """
    messages = [
        Message(datetime(2026, 8, 31, 23, 59), "มะลิ", "เดือนที่แล้ว", Kind.TEXT),
        Message(datetime(2026, 9, 1, 0, 0), "มะลิ", "ต้นเดือนนี้", Kind.TEXT),
        Message(datetime(2026, 9, 30, 23, 59), "ฉัน", "ปลายเดือนนี้", Kind.TEXT),
        Message(datetime(2026, 10, 1, 0, 0), "ฉัน", "เดือนหน้า", Kind.TEXT),
    ]
    selected = filter_current_month(messages)
    assert [m.text for m in selected] == ["ต้นเดือนนี้", "ปลายเดือนนี้"]


def test_เดือนนี้ไม่มีข้อความเลย(frozen_clock) -> None:
    messages = [Message(datetime(2025, 1, 1, 9, 0), "มะลิ", "ปีที่แล้ว", Kind.TEXT)]
    assert filter_current_month(messages) == []


# ---------------------------------------------------------------------------
# กรณีข้อมูลผิดปกติ
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "top_n",
    [
        pytest.param(0, id="ขอศูนย์คำ"),
        pytest.param(-1, id="ขอจำนวนติดลบ"),
    ],
)
def test_ขอจำนวนคำผิดปกติต้องไม่พัง(sample_messages, top_n: int) -> None:
    """ต้องรู้ว่ามันคืนอะไร ไม่ใช่เดาเอา"""
    assert count_words(sample_messages, top_n=top_n) == []


def test_ข้อความที่มีแต่ช่องว่างไม่ถูกนับเป็นคำ() -> None:
    messages = [Message(datetime(2026, 9, 1, 9, 0), "มะลิ", "   ", Kind.TEXT)]
    assert count_words(messages) == []


def test_เครื่องหมายวรรคตอนล้วนไม่ถูกนับเป็นคำ() -> None:
    messages = [Message(datetime(2026, 9, 1, 9, 0), "มะลิ", "!!! ??? ...", Kind.TEXT)]
    assert count_words(messages) == []
