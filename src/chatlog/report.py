"""ประกอบรายงานและเขียนลงไฟล์

นี่คือโมดูลแรกที่ "แตะโลกภายนอก" - เทสต์จึงต้องใช้ tmp_path
"""

from __future__ import annotations

import json
from pathlib import Path

from .stats import ChatStats


def build_report(stats: ChatStats) -> dict:
    """แปลง ChatStats เป็น dict ที่พร้อมเขียนเป็น JSON (ยังบริสุทธิ์)"""
    return {
        "ช่วงเวลา": f"{stats.period_start.isoformat()} ถึง {stats.period_end.isoformat()}",
        "จำนวนข้อความ": stats.total_messages,
        "แยกตามคน": stats.by_sender,
        "วันที่คุยเยอะสุด": stats.busiest_day.isoformat(),
        "ข้อความดึก": stats.late_night_count,
        "ตอบกลับเฉลี่ยนาที": round(stats.average_reply_minutes, 2),
        "คำที่ใช้บ่อย": [{"คำ": w, "จำนวน": c} for w, c in stats.top_words],
    }


def write_report(stats: ChatStats, path: str | Path) -> Path:
    """เขียนรายงานเป็น JSON แล้วคืน path ที่เขียนไป"""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(build_report(stats), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target
