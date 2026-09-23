"""เทสต์ตัวแกะไฟล์

ฟีเจอร์ที่ใช้: 1 assert · 2 raises · 4 parametrize · 5 param
             · 11 caplog · 12 skip/xfail · 13 marker
"""

from __future__ import annotations

import logging
from datetime import datetime

import pytest

from chatlog.errors import EmptyChatError, ParseError
from chatlog.models import Kind
from chatlog.parser import classify, parse_text

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# กฎข้อ 1: วันที่มาจากบรรทัดหัว
# ---------------------------------------------------------------------------
def test_แกะไฟล์ตัวอย่างได้ครบทุกข้อความ(sample_messages) -> None:
    assert len(sample_messages) == 10


def test_วันที่มาจากบรรทัดหัวที่อยู่ข้างบน(sample_messages) -> None:
    """ข้อความไม่มีวันที่ในตัวเอง ต้องจำจากบรรทัด 2026/09/01 ที่อยู่เหนือขึ้นไป"""
    assert sample_messages[0].timestamp == datetime(2026, 9, 1, 9, 12)
    assert sample_messages[5].timestamp == datetime(2026, 9, 2, 0, 30)


@pytest.mark.parametrize(
    "index, sender, text_start",
    [
        pytest.param(0, "มะลิ", "กินข้าว", id="ข้อความแรก"),
        pytest.param(1, "ฉัน", "ยังเลย", id="ข้อความที่สอง"),
        pytest.param(9, "มะลิ", "คิดถึง", id="ข้อความสุดท้าย"),
    ],
)
def test_ผู้ส่งและเนื้อหาถูกต้อง(sample_messages, index, sender, text_start) -> None:
    message = sample_messages[index]
    assert message.sender == sender
    assert message.text.startswith(text_start)


# ---------------------------------------------------------------------------
# กฎข้อ 2: ข้อความหลายบรรทัด
# ---------------------------------------------------------------------------
def test_ข้อความหลายบรรทัดถูกต่อเข้าด้วยกัน(sample_messages) -> None:
    last_from_me = sample_messages[8]
    assert last_from_me.text == "ถ่ายที่ไหน\nตรงร้านกาแฟหน้าหอปะ"


# ---------------------------------------------------------------------------
# กฎข้อ 3: รูป สติกเกอร์ สาย
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "text, expected",
    [
        pytest.param("สวัสดี", Kind.TEXT, id="ข้อความธรรมดา"),
        pytest.param("[รูปภาพ]", Kind.IMAGE, id="รูปภาษาไทย"),
        pytest.param("[Photo]", Kind.IMAGE, id="รูปภาษาอังกฤษ"),
        pytest.param("[สติกเกอร์]", Kind.STICKER, id="สติกเกอร์"),
        pytest.param("☎ ไม่ได้รับสาย", Kind.CALL, id="สายที่ไม่ได้รับ"),
        pytest.param("  [รูปภาพ]  ", Kind.IMAGE, id="มีช่องว่างหน้าหลัง"),
        pytest.param("ส่ง [รูปภาพ] มาให้", Kind.TEXT, id="คำว่ารูปอยู่กลางประโยค-ยังเป็นข้อความ"),
    ],
)
def test_classify(text: str, expected: Kind) -> None:
    assert classify(text) is expected


def test_รูปภาพถูกจัดชนิดถูกต้องในไฟล์จริง(sample_messages) -> None:
    assert sample_messages[6].kind is Kind.IMAGE


# ---------------------------------------------------------------------------
# กฎข้อ 9: โครงสร้างพัง -> ParseError
# ---------------------------------------------------------------------------
def test_ข้อความก่อนบรรทัดวันที่() -> None:
    with pytest.raises(ParseError, match="ก่อนบรรทัดวันที่"):
        parse_text("09:12\tมะลิ\tสวัสดี")


@pytest.mark.parametrize(
    "bad_line, expected_word",
    [
        pytest.param("25:00\tมะลิ\tสวัสดี", "เวลา", id="ชั่วโมงเกิน24"),
        pytest.param("09:75\tมะลิ\tสวัสดี", "เวลา", id="นาทีเกิน59"),
    ],
)
def test_เวลาไม่ถูกต้อง(bad_line: str, expected_word: str) -> None:
    with pytest.raises(ParseError, match=expected_word):
        parse_text("2026/09/01 (อ)\n" + bad_line)


def test_วันที่ไม่ถูกต้อง() -> None:
    with pytest.raises(ParseError, match="วันที่ไม่ถูกต้อง"):
        parse_text("2026/13/45\n09:00\tมะลิ\tสวัสดี")


def test_ParseError_บอกเลขบรรทัดได้() -> None:
    """ข้อมูลใน exception ก็ควรเทสต์ ไม่ใช่แค่ชนิดของมัน"""
    with pytest.raises(ParseError) as exc_info:
        parse_text("2026/09/01\n09:00\tมะลิ\tปกติ\n25:00\tฉัน\tพัง")
    assert exc_info.value.line_no == 3


# ---------------------------------------------------------------------------
# กฎข้อ 9: ไฟล์ว่าง
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "text",
    [
        pytest.param("", id="สตริงว่าง"),
        pytest.param("   \n\n  \n", id="มีแต่ช่องว่าง"),
        pytest.param("[LINE] ประวัติแชทกับ มะลิ\n2026/09/01 (อ)\n", id="มีหัวไฟล์แต่ไม่มีข้อความ"),
    ],
)
def test_ไฟล์ที่ไม่มีข้อความ(text: str) -> None:
    with pytest.raises(EmptyChatError):
        parse_text(text)


# ---------------------------------------------------------------------------
# กฎข้อ 8: ขยะข้ามได้ แต่ต้องบอก  (ฟีเจอร์ที่ 11: caplog)
# ---------------------------------------------------------------------------
def test_บรรทัดผิดรูปแบบถูกข้ามและมี_log(caplog: pytest.LogCaptureFixture) -> None:
    """ไฟล์จากโลกจริงมีบรรทัดเพี้ยนเสมอ

    ระบบต้องไม่ล้มทั้งไฟล์ แต่ต้องบอกให้รู้ว่าข้ามอะไรไป
    """
    text = "\n".join(
        [
            "2026/09/01 (อ)",
            "09:00\tมะลิ\tปกติ",
            "10:00 มะลิ ใช้ช่องว่างแทนแท็บ",
            "11:00\tฉัน\tปกติอีกที",
        ]
    )
    with caplog.at_level(logging.WARNING):
        messages = parse_text(text)

    assert len(messages) == 2
    assert "ข้ามบรรทัดที่ 3" in caplog.text


def test_บรรทัดแปลกปลอมก่อนข้อความแรกถูกข้าม(caplog: pytest.LogCaptureFixture) -> None:
    """บรรทัดที่ไม่เข้าพวกอะไรเลย และยังไม่มีข้อความให้ต่อท้าย"""
    text = "\n".join(
        [
            "ข้อความแปลกปลอมที่ไม่รู้ว่าคืออะไร",
            "2026/09/01 (อ)",
            "09:00\tมะลิ\tสวัสดี",
        ]
    )
    with caplog.at_level(logging.WARNING):
        messages = parse_text(text)

    assert len(messages) == 1
    assert "ไม่รู้ว่าคืออะไร" in caplog.text


def test_รองรับไฟล์ที่ขึ้นบรรทัดใหม่แบบ_windows() -> None:
    text = "2026/09/01 (อ)\r\n09:00\tมะลิ\tสวัสดี\r\n"
    assert parse_text(text)[0].text == "สวัสดี"


def test_ข้อความที่มีแต่ช่องว่างยังนับเป็นข้อความ(caplog: pytest.LogCaptureFixture) -> None:
    """เทสต์นี้เคยแดง และทำให้เจอบั๊กจริง

    เดิม parser ตัดช่องว่างท้ายบรรทัดทิ้งก่อนตรวจรูปแบบ
    บรรทัด "09:00<tab>มะลิ<tab>   " จึงเหลือ "09:00<tab>มะลิ"
    ซึ่งไม่ตรงรูปแบบ -> ข้อความหายไปเงียบ ๆ และยัง log ผิดสาเหตุว่า "รูปแบบไม่ถูกต้อง"

    ข้อความว่างไม่ใช่ข้อความผิดรูปแบบ ต้องนับเป็นข้อความที่มีเนื้อหาว่าง
    """
    text = "2026/09/01 (อ)\n09:00\tมะลิ\t   \n09:05\tฉัน\tสวัสดี"

    with caplog.at_level(logging.WARNING):
        messages = parse_text(text)

    assert len(messages) == 2
    assert messages[0].text == ""
    assert messages[0].sender == "มะลิ"
    assert "รูปแบบไม่ถูกต้อง" not in caplog.text


def test_ช่องว่างท้ายข้อความถูกตัดทิ้ง() -> None:
    """ตัดช่องว่างส่วนเกิน แต่ต้องไม่ทำให้ทั้งข้อความหายไป"""
    messages = parse_text("2026/09/01 (อ)\n09:00\tมะลิ\tสวัสดี   ")
    assert messages[0].text == "สวัสดี"


# ---------------------------------------------------------------------------
# ฟีเจอร์ที่ 12: skip / xfail
# ---------------------------------------------------------------------------
@pytest.mark.xfail(strict=True, reason="ยังไม่รองรับข้อความที่ถูกยกเลิกการส่ง")
def test_ข้อความที่ถูกยกเลิก() -> None:
    """เทสต์ที่เขียนไว้ล่วงหน้าสำหรับฟีเจอร์ที่ยังไม่ได้ทำ

    strict=True แปลว่า ถ้าวันไหนทำเสร็จแล้วเทสต์นี้ผ่านขึ้นมา
    pytest จะเตือนให้มาลบ marker ออก - กันไม่ให้ลืม
    """
    messages = parse_text("2026/09/01\n09:00\tมะลิ\tยกเลิกการส่งข้อความแล้ว")
    assert messages[0].kind == "unsent"


@pytest.mark.skip(reason="อยู่นอกขอบเขตงานนี้ - จะทำตอนรองรับ Instagram")
def test_แกะไฟล์_json_ของ_instagram() -> None:
    raise AssertionError("ยังไม่ได้เขียน")
