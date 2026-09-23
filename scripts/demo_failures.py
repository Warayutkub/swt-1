"""สาธิตว่าเทสต์จับความผิดพลาดได้จริง โดยจงใจทำให้โค้ดพังทีละแบบ

ใช้ตอนนำเสนอ เพื่อให้เห็นผลรัน "สีแดง" จริง ๆ ไม่ใช่แค่อ่านจากเอกสาร

    python scripts/demo_failures.py            รันทุกกรณี
    python scripts/demo_failures.py 2          รันเฉพาะกรณีที่ 2
    python scripts/demo_failures.py --list     ดูรายการกรณี
    python scripts/demo_failures.py --full     แสดง traceback เต็ม
    python scripts/demo_failures.py --restore   คืนสภาพฉุกเฉิน

สคริปต์นี้แก้ไฟล์ต้นฉบับชั่วคราวแล้ว **คืนสภาพให้เสมอ** แม้จะกด Ctrl-C
ระหว่างทาง เพราะใช้ try/finally ครอบไว้ทั้งหมด
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "chatlog"


@dataclass(frozen=True)
class Scenario:
    title: str
    file: str
    old: str
    new: str
    why: str
    expect: str


SCENARIOS: list[Scenario] = [
    Scenario(
        title="ขยับขอบเขต ดึก ไปหนึ่งชั่วโมง",
        file="rules.py",
        old="NIGHT_END = time(5, 0)",
        new="NIGHT_END = time(6, 0)",
        why="ความผิดพลาดแบบคลาสสิก: ตั้งค่าเส้นแบ่งผิดไปนิดเดียว",
        expect="แดง 1 เคส จาก 6 เคสของเทสต์เดียวกัน",
    ),
    Scenario(
        title="ขยายเพดานเวลาตอบกลับจาก 6 เป็น 24 ชั่วโมง",
        file="rules.py",
        old="REPLY_GAP_LIMIT = timedelta(hours=6)",
        new="REPLY_GAP_LIMIT = timedelta(hours=24)",
        why="แก้ค่าเดียวแต่ผลลามไปถึงรายงานปลายทาง",
        expect="แดง 5 เทสต์ ใน 4 ไฟล์ ข้ามทั้ง unit และ integration",
    ),
    Scenario(
        title="ลืมกรองรูปและสติกเกอร์ออกจากการนับคำ",
        file="stats.py",
        old="        if not message.is_countable_text:",
        new="        if False:",
        why="ลืมเงื่อนไขหนึ่งบรรทัด สถิติคำจะเพี้ยนทันที",
        expect="แดง 3 เคส แต่เคสข้อความปกติยังเขียว",
    ),
    Scenario(
        title="เขียน JSON เป็นรหัสแทนภาษาไทย",
        file="report.py",
        old="ensure_ascii=False",
        new="ensure_ascii=True",
        why="โปรแกรมยังทำงานได้ ไฟล์ยังถูกต้อง แต่มนุษย์อ่านไม่ออก",
        expect="แดง 1 เทสต์ เรื่องคุณภาพ ไม่ใช่เรื่องพัง",
    ),
    Scenario(
        title="โยน error ถูกชนิด แต่ข้อความไม่บอกสาเหตุ",
        file="summarizer.py",
        old='raise MissingApiKeyError(f"ไม่พบตัวแปรสภาพแวดล้อม {API_KEY_ENV}")',
        new='raise MissingApiKeyError("ไม่พบคีย์")',
        why="ถ้าเทสต์เช็คแค่ชนิดของ error จะจับไม่ได้ ต้องมี match= ด้วย",
        expect="แดง 1 เทสต์ เพราะ regex ไม่ตรง",
    ),
]

RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BOLD = "\033[1m"


def paint(text: str, color: str) -> str:
    return f"{color}{text}{RESET}"


def line(char: str = "=") -> str:
    return char * 70


def read_exact(path: Path) -> str:
    """อ่านไฟล์โดยไม่แปลงตัวขึ้นบรรทัดใหม่

    newline="" สำคัญมาก ถ้าไม่ใส่ Python จะแปลง \\r\\n เป็น \\n ตอนอ่าน
    แล้วแปลงกลับเป็น \\r\\n ตอนเขียน ทำให้ git เห็นว่าไฟล์เปลี่ยน
    ทั้งที่เนื้อหาเหมือนเดิมทุกตัวอักษร
    """
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def write_exact(path: Path, content: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def read_sources() -> dict[str, str]:
    """อ่านไฟล์ต้นฉบับทั้งหมดที่สคริปต์นี้จะไปแตะ เก็บไว้ในหน่วยความจำ"""
    names = {s.file for s in SCENARIOS}
    return {name: read_exact(SRC / name) for name in names}


def restore(backup: dict[str, str]) -> None:
    for name, content in backup.items():
        write_exact(SRC / name, content)


def run_pytest(extra: list[str] | None = None) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"]
        + (extra or []),
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode, result.stdout + result.stderr


def show_result(output: str, full: bool) -> None:
    if full:
        print(output)
        return

    for raw in output.splitlines():
        text = raw.rstrip()
        if text.startswith("FAILED"):
            print("  " + paint(text, RED))
        elif text.startswith("E "):
            print("  " + paint(text, YELLOW))
        elif " failed" in text or " passed" in text:
            color = RED if " failed" in text else GREEN
            print("  " + paint(text, color))


def play(scenario: Scenario, number: int, backup: dict[str, str], full: bool) -> bool:
    target = SRC / scenario.file
    original = backup[scenario.file]

    if scenario.old not in original:
        print(paint(f"ข้ามกรณีที่ {number}: หาข้อความที่จะแก้ไม่เจอใน {scenario.file}", YELLOW))
        return False

    print()
    print(paint(line(), BOLD))
    print(paint(f"กรณีที่ {number}: {scenario.title}", BOLD))
    print(paint(line(), BOLD))
    print(f"  ไฟล์      {scenario.file}")
    print(f"  แก้จาก    {scenario.old.strip()}")
    print(f"  เป็น      {scenario.new.strip()}")
    print(f"  ทำไม      {scenario.why}")
    print(f"  คาดว่า    {scenario.expect}")
    print()

    write_exact(target, original.replace(scenario.old, scenario.new, 1))
    code, output = run_pytest()
    show_result(output, full)

    write_exact(target, original)
    print()
    print("  " + paint("คืนสภาพไฟล์เรียบร้อย", GREEN))
    return code != 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="สาธิตผลรันตอนเทสต์จับความผิดพลาดได้")
    parser.add_argument("only", nargs="?", type=int, help="เลือกรันเฉพาะกรณีที่ระบุ")
    parser.add_argument("--list", action="store_true", help="แสดงรายการกรณีทั้งหมด")
    parser.add_argument("--full", action="store_true", help="แสดงผลรันเต็มรวม traceback")
    parser.add_argument("--restore", action="store_true", help="คืนสภาพไฟล์ฉุกเฉินจาก git")
    args = parser.parse_args(argv)

    if args.restore:
        subprocess.run(["git", "checkout", "--", "src/chatlog"], cwd=ROOT, check=False)
        print(paint("คืนสภาพจาก git เรียบร้อย", GREEN))
        return 0

    if args.list:
        for index, scenario in enumerate(SCENARIOS, start=1):
            print(f"{index}. {scenario.title}  ({scenario.file})")
        return 0

    backup = read_sources()

    print(paint(line(), BOLD))
    print(paint("ตรวจสภาพตั้งต้นก่อน", BOLD))
    print(paint(line(), BOLD))
    code, output = run_pytest()
    show_result(output, full=False)
    if code != 0:
        print()
        print(paint("โค้ดยังไม่เขียวตั้งแต่แรก หยุดก่อน", RED))
        return 1

    chosen = SCENARIOS if args.only is None else [SCENARIOS[args.only - 1]]
    offset = 1 if args.only is None else args.only

    caught = 0
    try:
        for index, scenario in enumerate(chosen, start=offset):
            if play(scenario, index, backup, args.full):
                caught += 1
    finally:
        # ต่อให้กด Ctrl-C หรือมีอะไรพังกลางทาง ไฟล์ต้องกลับมาเหมือนเดิมเสมอ
        restore(backup)

    print()
    print(paint(line(), BOLD))
    print(paint("ตรวจสภาพหลังสาธิต", BOLD))
    print(paint(line(), BOLD))
    code, output = run_pytest()
    show_result(output, full=False)

    print()
    print(paint(f"เทสต์จับความผิดพลาดได้ {caught} จาก {len(chosen)} กรณี", BOLD))
    if code != 0:
        print(paint("เตือน: ไฟล์ยังไม่กลับสู่สภาพเดิม ลองสั่ง --restore", RED))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
