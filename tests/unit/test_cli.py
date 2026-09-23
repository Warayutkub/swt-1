"""เทสต์หน้าตาบรรทัดคำสั่ง

ฟีเจอร์ที่ใช้: 11 capsys - จับสิ่งที่โปรแกรมพิมพ์ออกจอ
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from chatlog.cli import main

pytestmark = pytest.mark.unit


def test_พิมพ์สรุปออกจอ(chat_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([str(chat_file)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "จำนวนข้อความ" in output
    assert "10" in output
    assert "มะลิ" in output


def test_ไฟล์ไม่มีอยู่จริง(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([str(tmp_path / "ไม่มีไฟล์นี้.txt")])

    assert exit_code == 1
    assert "ไม่พบไฟล์" in capsys.readouterr().out


def test_ไฟล์ว่างรายงานเป็นข้อผิดพลาด(tmp_path: Path, capsys) -> None:
    empty = tmp_path / "ว่าง.txt"
    empty.write_text("", encoding="utf-8")

    assert main([str(empty)]) == 1
    assert "ผิดพลาด" in capsys.readouterr().out


def test_เขียนไฟล์_json_ด้วยได้(chat_file: Path, tmp_path: Path, capsys) -> None:
    out = tmp_path / "out" / "report.json"

    assert main([str(chat_file), "--json", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["จำนวนข้อความ"] == 10
    assert "เขียนรายงานแล้ว" in capsys.readouterr().out


def test_เลือกเฉพาะเดือนนี้(chat_file: Path, frozen_clock, capsys) -> None:
    """frozen_clock ล็อกวันนี้ไว้ 15 ก.ย. 2569 ข้อความตัวอย่างอยู่เดือนนั้นพอดี"""
    assert main([str(chat_file), "--month"]) == 0
    assert "10" in capsys.readouterr().out


def test_เดือนนี้ไม่มีข้อความ(tmp_path: Path, frozen_clock, capsys) -> None:
    old = tmp_path / "เก่า.txt"
    old.write_text("2025/01/01 (พ)\n09:00\tมะลิ\tสวัสดี\n", encoding="utf-8")

    assert main([str(old), "--month"]) == 1
    assert "ไม่มีข้อความในเดือนนี้" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# กรณีเรียกใช้ผิดวิธี
# ---------------------------------------------------------------------------
def test_ไม่ใส่อาร์กิวเมนต์เลย(capsys) -> None:
    """argparse จะจบโปรแกรมด้วย SystemExit(2) ไม่ได้ return ค่าออกมา

    ต้องดักด้วย pytest.raises ไม่งั้นเทสต์จะถูกฆ่ากลางคัน
    """
    with pytest.raises(SystemExit) as exc_info:
        main([])

    assert exc_info.value.code == 2
    assert "the following arguments are required" in capsys.readouterr().err


def test_ไฟล์พังกลางคัน(tmp_path: Path, capsys) -> None:
    """ไฟล์ที่มีข้อความปกติแล้วมีบรรทัดโครงสร้างพังอยู่ข้างใน"""
    broken = tmp_path / "พัง.txt"
    broken.write_text(
        "2026/09/01 (อ)\n09:00\tมะลิ\tปกติ\n25:00\tฉัน\tเวลาผิด\n",
        encoding="utf-8",
    )

    assert main([str(broken)]) == 1
    assert "ผิดพลาด" in capsys.readouterr().out
