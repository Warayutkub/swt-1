"""โครงสร้างข้อมูลกลางของระบบ

Message เป็น frozen dataclass โดยตั้งใจ - แก้ค่าไม่ได้หลังสร้าง
ทำให้เทสต์มั่นใจได้ว่าไม่มีใครแอบแก้ข้อมูลระหว่างทาง
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Kind(str, Enum):
    """ชนิดของข้อความ - ใช้แยกว่าอันไหนเอาไปนับคำได้บ้าง"""

    TEXT = "text"
    IMAGE = "image"
    STICKER = "sticker"
    CALL = "call"


@dataclass(frozen=True, slots=True)
class Message:
    timestamp: datetime
    sender: str
    text: str
    kind: Kind = Kind.TEXT

    @property
    def is_countable_text(self) -> bool:
        """เอาไปนับคำได้มั้ย - รูป/สติกเกอร์/สาย ไม่นับ (กฎข้อ 3)"""
        return self.kind is Kind.TEXT
