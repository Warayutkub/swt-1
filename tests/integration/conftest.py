"""conftest ซ้อนชั้น

pytest อ่าน conftest.py จากบนลงล่าง fixture ในไฟล์นี้จึงใช้ได้เฉพาะ
เทสต์ในโฟลเดอร์ integration ส่วน fixture ใน tests/conftest.py ยังใช้ได้อยู่
เป็นการแสดงว่าจัดโครง fixture เป็นชั้น ๆ ได้
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def project_dir(tmp_path: Path):
    """จำลองโฟลเดอร์งานจริง: มีไฟล์เข้า และที่สำหรับไฟล์ออก"""
    (tmp_path / "input").mkdir()
    (tmp_path / "output").mkdir()
    yield tmp_path
    # ไม่ต้องลบเอง tmp_path จัดการให้ - ใส่ yield ไว้เพื่อให้เห็นจุดที่จะเก็บกวาด
