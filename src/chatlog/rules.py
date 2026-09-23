"""กฎทางธุรกิจ - ฟังก์ชันบริสุทธิ์ล้วน

ทุกฟังก์ชันในไฟล์นี้รับค่าเข้า คืนค่าออก ไม่มีผลข้างเคียง
จึงเทสต์ได้ง่ายที่สุดในโปรเจค และเป็นที่อยู่ของ parametrize ส่วนใหญ่
"""

from __future__ import annotations

from datetime import datetime, time, timedelta

from .models import Message

#: ช่วงที่นับว่า "ดึก" (กฎข้อ 4) - ครอบคลุม 00:00 ถึง 04:59
NIGHT_START = time(0, 0)
NIGHT_END = time(5, 0)

#: ห่างเกินนี้ถือว่าเริ่มบทสนทนาใหม่ ไม่ใช่การตอบกลับ (กฎข้อ 6)
REPLY_GAP_LIMIT = timedelta(hours=6)


def is_late_night(moment: datetime) -> bool:
    """00:00-04:59 = ดึก | 05:00 เป็นต้นไป = ไม่ดึก"""
    return NIGHT_START <= moment.time() < NIGHT_END


def reply_delays(messages: list[Message]) -> list[timedelta]:
    """ระยะเวลาตอบกลับทั้งหมดในบทสนทนา (กฎข้อ 5, 6, 7)

    นับเฉพาะตอนที่ "ผู้พูดเปลี่ยนคน" และวัดจากข้อความสุดท้าย
    ของชุดก่อนหน้า ไม่ใช่ข้อความแรก
    """
    delays: list[timedelta] = []
    previous_sender: str | None = None
    previous_time: datetime | None = None

    for message in messages:
        if previous_sender is not None and message.sender != previous_sender:
            gap = message.timestamp - previous_time
            if timedelta(0) <= gap <= REPLY_GAP_LIMIT:
                delays.append(gap)
        previous_sender = message.sender
        previous_time = message.timestamp

    return delays


def is_same_month(moment: datetime, year: int, month: int) -> bool:
    return moment.year == year and moment.month == month
