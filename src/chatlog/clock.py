"""นาฬิกาของระบบ

ทุกที่ที่ต้องรู้ "ตอนนี้กี่โมง" ต้องเรียกผ่านไฟล์นี้เท่านั้น
ห้ามเรียก datetime.now() ตรง ๆ ที่อื่น เพราะเทสต์จะควบคุมเวลาไม่ได้

วิธีใช้ให้ถูกในโค้ดอื่น:

    from . import clock          # ถูก   -> monkeypatch ได้
    clock.today()

    from .clock import today     # ผิด   -> ผูกฟังก์ชันตัวจริงไว้ตั้งแต่ import
    today()                      #         monkeypatch แล้วไม่มีผล
"""

from __future__ import annotations

from datetime import date, datetime


def now() -> datetime:
    return datetime.now()


def today() -> date:
    return now().date()
