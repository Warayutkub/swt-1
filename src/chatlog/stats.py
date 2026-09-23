"""คำนวณสถิติจากรายการข้อความ

ยังบริสุทธิ์อยู่ ยกเว้น filter_current_month ที่ต้องรู้ว่า "วันนี้" คือวันไหน
จึงเรียกผ่าน clock เพื่อให้เทสต์ล็อกเวลาได้
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date

from . import clock
from .models import Message
from .rules import is_late_night, reply_delays

#: คำที่พบบ่อยจนไม่มีความหมายในการสรุป
STOP_WORDS = frozenset({"ครับ", "ค่ะ", "คะ", "นะ", "อะ", "จ้า", "ก็", "ที่", "แล้ว", "ไม่"})

#: เครื่องหมายที่ตัดทิ้งก่อนนับคำ
PUNCTUATION_RE = re.compile(r"[!-/:-@\[-`{-~‘’“”]+")


@dataclass(frozen=True)
class ChatStats:
    period_start: date
    period_end: date
    total_messages: int
    by_sender: dict[str, int]
    busiest_day: date
    late_night_count: int
    average_reply_minutes: float
    top_words: list[tuple[str, int]] = field(default_factory=list)


def count_words(messages: list[Message], top_n: int = 5) -> list[tuple[str, int]]:
    """นับคำที่ใช้บ่อย - ข้ามรูป สติกเกอร์ สาย และคำที่ไม่มีความหมาย

    หมายเหตุ: ตัดคำด้วยช่องว่าง ซึ่งใช้กับภาษาไทยได้ไม่สมบูรณ์
    (ภาษาไทยไม่เว้นวรรคระหว่างคำ) ถ้าจะทำจริงต้องใช้ pythainlp
    ในบริบทของงานนี้เราจงใจทำให้ง่ายไว้ก่อน
    """
    counter: Counter[str] = Counter()
    for message in messages:
        if not message.is_countable_text:
            continue
        for token in message.text.split():
            word = PUNCTUATION_RE.sub("", token).strip()
            if len(word) < 2 or word in STOP_WORDS:
                continue
            counter[word] += 1
    return counter.most_common(top_n)


def build_stats(messages: list[Message], top_n: int = 5) -> ChatStats:
    if not messages:
        raise ValueError("ต้องมีข้อความอย่างน้อยหนึ่งข้อความ")

    ordered = sorted(messages, key=lambda m: m.timestamp)
    per_day = Counter(m.timestamp.date() for m in ordered)
    # เรียงตามจำนวนมากไปน้อย ถ้าเท่ากันเอาวันที่มาก่อน
    busiest_day = min(per_day, key=lambda d: (-per_day[d], d))

    delays = reply_delays(ordered)
    average_minutes = (
        sum(d.total_seconds() for d in delays) / len(delays) / 60 if delays else 0.0
    )

    return ChatStats(
        period_start=ordered[0].timestamp.date(),
        period_end=ordered[-1].timestamp.date(),
        total_messages=len(ordered),
        by_sender=dict(Counter(m.sender for m in ordered)),
        busiest_day=busiest_day,
        late_night_count=sum(1 for m in ordered if is_late_night(m.timestamp)),
        average_reply_minutes=average_minutes,
        top_words=count_words(ordered, top_n),
    )


def filter_current_month(messages: list[Message]) -> list[Message]:
    """เลือกเฉพาะข้อความของ "เดือนนี้" (กฎข้อ 10)

    เรียก clock.today() ผ่านโมดูล ไม่ใช่ import ฟังก์ชันมาตรง ๆ
    เพื่อให้ monkeypatch ในเทสต์มีผลจริง
    """
    today = clock.today()
    return [
        m
        for m in messages
        if m.timestamp.year == today.year and m.timestamp.month == today.month
    ]
