"""เทสต์กฎทางธุรกิจ - ที่ที่ parametrize เปล่งประกายที่สุด

ฟีเจอร์ที่ใช้ในไฟล์นี้: 1 assert · 4 parametrize · 5 pytest.param · 13 marker
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from chatlog.models import Kind, Message
from chatlog.rules import is_late_night, is_same_month, reply_delays

# ติด marker ให้ทุกเทสต์ในไฟล์นี้ทีเดียว
pytestmark = pytest.mark.unit


def msg(hour: int, minute: int, sender: str, day: int = 1) -> Message:
    """ตัวช่วยสร้างข้อความ ทำให้เทสต์อ่านง่ายขึ้นมาก"""
    return Message(datetime(2026, 9, day, hour, minute), sender, "ข้อความ", Kind.TEXT)


# ---------------------------------------------------------------------------
# กฎข้อ 4: "ดึก" คือ 00:00-04:59
# เทสต์ขอบเขต - ค่าที่ผิดพลาดง่ายที่สุดคือค่าที่อยู่ติดเส้นแบ่งพอดี
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "hour, minute, expected",
    [
        pytest.param(23, 59, False, id="ก่อนเที่ยงคืนหนึ่งนาที-ยังไม่ดึก"),
        pytest.param(0, 0, True, id="เที่ยงคืนตรง-เริ่มดึก"),
        pytest.param(2, 30, True, id="ตีสองครึ่ง-ดึกแน่นอน"),
        pytest.param(4, 59, True, id="นาทีสุดท้ายของช่วงดึก"),
        pytest.param(5, 0, False, id="ตีห้าตรง-หมดช่วงดึก"),
        pytest.param(12, 0, False, id="เที่ยงวัน-ไม่ดึก"),
    ],
)
def test_is_late_night(hour: int, minute: int, expected: bool) -> None:
    assert is_late_night(datetime(2026, 9, 1, hour, minute)) is expected


# ---------------------------------------------------------------------------
# กฎข้อ 5, 6, 7: การตอบกลับ
# ---------------------------------------------------------------------------
def test_นับเฉพาะตอนที่เปลี่ยนคนพูด() -> None:
    """กฎข้อ 5: พิมพ์ต่อเองไม่ใช่การตอบ"""
    messages = [
        msg(9, 12, "มะลิ"),
        msg(9, 15, "ฉัน"),  # ตอบใน 3 นาที
        msg(9, 20, "ฉัน"),  # ตัวเราเอง ไม่นับ
    ]
    assert reply_delays(messages) == [timedelta(minutes=3)]


def test_วัดจากข้อความสุดท้ายของชุด() -> None:
    """กฎข้อ 7: พิมพ์รัว 3 ที แล้วอีกฝ่ายตอบ ต้องวัดจากข้อความสุดท้าย"""
    messages = [
        msg(9, 0, "มะลิ"),
        msg(9, 1, "มะลิ"),
        msg(9, 5, "มะลิ"),  # ข้อความสุดท้ายของชุด
        msg(9, 8, "ฉัน"),  # ห่าง 3 นาที ไม่ใช่ 8
    ]
    assert reply_delays(messages) == [timedelta(minutes=3)]


def test_ห่างเกินหกชั่วโมงไม่นับว่าตอบ() -> None:
    """กฎข้อ 6: ตอบเช้าวันรุ่งขึ้น = เริ่มบทสนทนาใหม่"""
    messages = [
        msg(23, 0, "มะลิ", day=1),
        msg(8, 0, "ฉัน", day=2),  # ห่าง 9 ชั่วโมง
    ]
    assert reply_delays(messages) == []


@pytest.mark.parametrize(
    "gap_minutes, should_count",
    [
        pytest.param(0, True, id="ตอบทันทีวินาทีเดียวกัน"),
        pytest.param(359, True, id="5ชม59นาที-ยังนับ"),
        pytest.param(360, True, id="6ชม-ยังนับ-ขอบพอดี"),
        pytest.param(361, False, id="6ชม1นาที-เกินแล้ว"),
    ],
)
def test_ขอบเขตหกชั่วโมง(gap_minutes: int, should_count: bool) -> None:
    start = datetime(2026, 9, 1, 0, 0)
    messages = [
        Message(start, "มะลิ", "ก", Kind.TEXT),
        Message(start + timedelta(minutes=gap_minutes), "ฉัน", "ข", Kind.TEXT),
    ]
    assert bool(reply_delays(messages)) is should_count


def test_ข้อความเดียวไม่มีการตอบ() -> None:
    assert reply_delays([msg(9, 0, "มะลิ")]) == []


def test_ไม่มีข้อความเลย() -> None:
    assert reply_delays([]) == []


@pytest.mark.parametrize(
    "moment, year, month, expected",
    [
        (datetime(2026, 9, 1), 2026, 9, True),
        (datetime(2026, 9, 30, 23, 59), 2026, 9, True),
        (datetime(2026, 10, 1), 2026, 9, False),
        (datetime(2025, 9, 1), 2026, 9, False),
    ],
)
def test_is_same_month(moment, year, month, expected) -> None:
    assert is_same_month(moment, year, month) is expected


# ---------------------------------------------------------------------------
# กรณีข้อมูลผิดปกติ
# ---------------------------------------------------------------------------
def test_ข้อความเรียงเวลาผิดลำดับไม่ให้ค่าติดลบ() -> None:
    """ถ้ามีข้อมูลที่เรียงเวลาผิดหลุดเข้ามา ต้องไม่ได้ "เวลาตอบกลับ" ติดลบ

    เวลาติดลบจะทำให้ค่าเฉลี่ยทั้งรายงานเพี้ยนโดยไม่มีใครสังเกต
    """
    out_of_order = [
        msg(10, 0, "มะลิ"),
        msg(9, 0, "ฉัน"),  # ย้อนเวลากลับไปหนึ่งชั่วโมง
    ]
    delays = reply_delays(out_of_order)

    assert delays == []
    assert all(d >= timedelta(0) for d in delays)


def test_ตอบกลับพร้อมกันเป๊ะนับเป็นศูนย์นาที() -> None:
    """เวลาเดียวกันเป๊ะต้องนับ ไม่ใช่ตัดทิ้ง"""
    same_moment = [msg(9, 0, "มะลิ"), msg(9, 0, "ฉัน")]
    assert reply_delays(same_moment) == [timedelta(0)]
