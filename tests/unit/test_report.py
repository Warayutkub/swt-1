"""เทสต์การประกอบรายงานและการเขียนไฟล์

ฟีเจอร์ที่ใช้: 6 fixture+yield (workspace) · 10 tmp_path · 12 skipif
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from chatlog.report import build_report, write_report
from chatlog.stats import build_stats

pytestmark = pytest.mark.unit


@pytest.fixture
def stats(sample_messages):
    """fixture เล็ก ๆ เฉพาะไฟล์นี้ - ไม่ต้องยัดลง conftest ถ้าที่อื่นไม่ได้ใช้"""
    return build_stats(sample_messages)


def test_รายงานมีหัวข้อครบ(stats) -> None:
    report = build_report(stats)
    assert set(report) == {
        "ช่วงเวลา",
        "จำนวนข้อความ",
        "แยกตามคน",
        "วันที่คุยเยอะสุด",
        "ข้อความดึก",
        "ตอบกลับเฉลี่ยนาที",
        "คำที่ใช้บ่อย",
    }


def test_ปัดทศนิยมสองตำแหน่ง(stats) -> None:
    assert build_report(stats)["ตอบกลับเฉลี่ยนาที"] == 11.75


# ---------------------------------------------------------------------------
# ฟีเจอร์ที่ 10: tmp_path
# ---------------------------------------------------------------------------
def test_เขียนไฟล์แล้วอ่านกลับมาได้(stats, tmp_path: Path) -> None:
    target = write_report(stats, tmp_path / "report.json")

    assert target.exists()
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["จำนวนข้อความ"] == 10


def test_ภาษาไทยไม่ถูกแปลงเป็นรหัส(stats, tmp_path: Path) -> None:
    """ensure_ascii=False ต้องทำงาน ไม่งั้นไฟล์จะเต็มไปด้วยรหัส u0e04..."""
    target = write_report(stats, tmp_path / "report.json")
    assert "มะลิ" in target.read_text(encoding="utf-8")


def test_สร้างโฟลเดอร์ให้เองถ้ายังไม่มี(stats, tmp_path: Path) -> None:
    target = write_report(stats, tmp_path / "ยังไม่มี" / "ลึกอีกชั้น" / "report.json")
    assert target.exists()


# ---------------------------------------------------------------------------
# ฟีเจอร์ที่ 6: ใช้ fixture ที่มี yield
# ---------------------------------------------------------------------------
def test_เขียนลง_workspace_ได้(stats, workspace: Path) -> None:
    target = write_report(stats, workspace / "out" / "report.json")
    assert target.parent.name == "out"


# ---------------------------------------------------------------------------
# ฟีเจอร์ที่ 12: skipif - เทสต์ที่ใช้ได้เฉพาะบางระบบปฏิบัติการ
# ---------------------------------------------------------------------------
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows ไม่ได้บังคับสิทธิ์ไฟล์แบบ POSIX เทสต์นี้จึงไม่มีความหมาย",
)
def test_เขียนลงโฟลเดอร์ที่ไม่มีสิทธิ์(stats, tmp_path: Path) -> None:
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0o500)
    with pytest.raises(PermissionError):
        write_report(stats, locked / "report.json")
