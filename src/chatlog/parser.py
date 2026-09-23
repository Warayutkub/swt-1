"""แกะไฟล์ประวัติแชทเป็น list[Message]

รูปแบบไฟล์ที่รองรับ (อิงจากไฟล์ที่ LINE ส่งออก)::

    [LINE] ประวัติแชทกับ มะลิ
    บันทึกเมื่อ: 2026/09/20 14:30

    2026/09/01 (อ)
    09:12<TAB>มะลิ<TAB>กินข้าวยัง
    09:15<TAB>ฉัน<TAB>ยังเลย

สิ่งที่ต้องรู้: บรรทัดข้อความ "ไม่มีวันที่อยู่ในตัวเอง"
ต้องจำวันที่จากบรรทัดหัวที่อยู่ข้างบนขึ้นไป

การจัดการบรรทัดที่ผิดรูปแบบ แบ่งเป็นสองระดับ:

* ขยะที่ข้ามได้      -> เขียน log แล้วไปต่อ (กฎข้อ 8)
* โครงสร้างพัง       -> โยน ParseError (กฎข้อ 9)
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, time
from pathlib import Path

from .errors import EmptyChatError, ParseError
from .models import Kind, Message

log = logging.getLogger(__name__)

# 2026/09/01 (อ)   หรือ   2026/9/1
DATE_RE = re.compile(r"^(\d{4})/(\d{1,2})/(\d{1,2})\s*(?:\(.*\))?$")

# 09:12<TAB>ชื่อ<TAB>ข้อความ
MESSAGE_RE = re.compile(r"^(\d{1,2}):(\d{2})\t([^\t]*)\t(.*)$")

# ขึ้นต้นเหมือนข้อความ แต่อาจไม่ครบรูปแบบ - ใช้แยกขยะออกจากบรรทัดต่อเนื่อง
LOOKS_LIKE_MESSAGE_RE = re.compile(r"^\d{1,2}:\d{2}\b")

HEADER_PREFIXES = ("[LINE]", "บันทึกเมื่อ:", "Saved on:")

IMAGE_TOKENS = frozenset({"[รูปภาพ]", "[Photo]", "[photo]"})
STICKER_TOKENS = frozenset({"[สติกเกอร์]", "[Sticker]", "[sticker]"})
CALL_PREFIXES = ("☎",)


def classify(text: str) -> Kind:
    """ดูว่าข้อความนี้เป็นข้อความจริง หรือรูป/สติกเกอร์/สาย (กฎข้อ 3)"""
    stripped = text.strip()
    if stripped in IMAGE_TOKENS:
        return Kind.IMAGE
    if stripped in STICKER_TOKENS:
        return Kind.STICKER
    if stripped.startswith(CALL_PREFIXES):
        return Kind.CALL
    return Kind.TEXT


def parse_text(text: str) -> list[Message]:
    """ฟังก์ชันหลัก - บริสุทธิ์ ไม่แตะไฟล์ ไม่แตะเน็ต ไม่แตะเวลาจริง

    เทสต์ระดับ unit ทั้งหมดยิงเข้าฟังก์ชันนี้
    """
    # เก็บเป็น list ที่แก้ได้ก่อน เพราะข้อความหลายบรรทัดต้องต่อท้ายทีหลัง
    rows: list[tuple[datetime, str, list[str]]] = []
    current_date: date | None = None

    for line_no, raw in enumerate(text.splitlines(), start=1):
        # ตัดเฉพาะอักขระขึ้นบรรทัดใหม่ ห้ามตัดช่องว่างทิ้งตรงนี้
        # ไม่งั้นข้อความที่มีแต่ช่องว่าง ("09:00<tab>ชื่อ<tab>   ") จะเหลือ
        # "09:00<tab>ชื่อ" ซึ่งไม่ตรงรูปแบบ แล้วข้อความจะหายไปเงียบ ๆ
        # ช่องว่างส่วนเกินถูกตัดทีหลังตอนประกอบเนื้อความแทน
        line = raw.rstrip("\r\n")

        if not line.strip():
            continue

        if line.startswith(HEADER_PREFIXES):
            continue

        date_match = DATE_RE.match(line.strip())
        if date_match:
            year, month, day = (int(g) for g in date_match.groups())
            try:
                current_date = date(year, month, day)
            except ValueError as exc:
                raise ParseError(line_no, line, f"วันที่ไม่ถูกต้อง ({exc})") from exc
            continue

        message_match = MESSAGE_RE.match(line)
        if message_match:
            hour, minute, sender, body = message_match.groups()
            if current_date is None:
                raise ParseError(line_no, line, "พบข้อความก่อนบรรทัดวันที่")
            try:
                clock_time = time(int(hour), int(minute))
            except ValueError as exc:
                raise ParseError(line_no, line, f"เวลาไม่ถูกต้อง ({exc})") from exc
            rows.append((datetime.combine(current_date, clock_time), sender.strip(), [body]))
            continue

        # หน้าตาเหมือนข้อความแต่รูปแบบไม่ครบ (เช่น ใช้ช่องว่างแทน tab) = ขยะ
        if LOOKS_LIKE_MESSAGE_RE.match(line):
            log.warning("ข้ามบรรทัดที่ %d เพราะรูปแบบไม่ถูกต้อง: %s", line_no, line)
            continue

        # บรรทัดธรรมดาที่ตามหลังข้อความ = ข้อความเดิมที่ขึ้นบรรทัดใหม่ (กฎข้อ 2)
        if rows:
            rows[-1][2].append(line)
            continue

        log.warning("ข้ามบรรทัดที่ %d เพราะไม่รู้ว่าคืออะไร: %s", line_no, line)

    if not rows:
        raise EmptyChatError("ไม่พบข้อความในไฟล์")

    messages = []
    for timestamp, sender, parts in rows:
        body = "\n".join(parts).strip()
        messages.append(Message(timestamp, sender, body, classify(body)))
    return messages


def parse_file(path: str | Path, encoding: str = "utf-8") -> list[Message]:
    """ตัวห่อบาง ๆ ที่แตะระบบไฟล์ - เทสต์ระดับ integration ยิงเข้าตัวนี้"""
    return parse_text(Path(path).read_text(encoding=encoding))
