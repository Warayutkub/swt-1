"""ส่งสถิติไปให้ AI เขียนสรุปเป็นภาษาคน

โมดูลนี้คือ "ของข้างนอก" ของโปรเจค - เทสต์ห้ามยิงเน็ตจริงเด็ดขาด
เพราะช้า เสียเงิน ต้องใช้คีย์ และผลไม่เหมือนเดิมทุกครั้ง
เทสต์จึงใช้ monkeypatch แทนที่ call_ai ด้วยของปลอม

ข้อสำคัญ: summarize() เรียก call_ai() แบบชื่อโมดูลระดับบนสุด
Python จะไปหาค่าตอนเรียกจริง ไม่ใช่ตอน import - monkeypatch จึงมีผล
"""

from __future__ import annotations

import json
import os
import urllib.request

from .errors import MissingApiKeyError
from .stats import ChatStats

API_URL = "https://api.example.com/v1/summarize"
API_KEY_ENV = "CHATLOG_API_KEY"
DEFAULT_TIMEOUT = 30.0


def build_prompt(stats: ChatStats) -> str:
    """สร้างคำสั่งที่จะส่งให้ AI (ฟังก์ชันบริสุทธิ์ เทสต์ได้ตรง ๆ)"""
    people = ", ".join(f"{name} {count} ข้อความ" for name, count in stats.by_sender.items())
    return (
        "ช่วยสรุปบทสนทนานี้เป็นภาษาไทยแบบอบอุ่น ความยาวไม่เกินสามประโยค\n"
        f"ช่วงเวลา: {stats.period_start} ถึง {stats.period_end}\n"
        f"จำนวนข้อความทั้งหมด: {stats.total_messages}\n"
        f"แยกตามคน: {people}\n"
        f"ข้อความช่วงดึก: {stats.late_night_count}\n"
        f"ตอบกลับเฉลี่ย: {stats.average_reply_minutes:.1f} นาที"
    )


def call_ai(prompt: str, *, timeout: float = DEFAULT_TIMEOUT) -> str:
    """ยิง HTTP จริง - ในเทสต์ตัวนี้จะถูกแทนที่เสมอ"""
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        raise MissingApiKeyError(f"ไม่พบตัวแปรสภาพแวดล้อม {API_KEY_ENV}")

    request = urllib.request.Request(
        API_URL,
        data=json.dumps({"prompt": prompt}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["summary"]


def summarize(stats: ChatStats) -> str:
    return call_ai(build_prompt(stats))
