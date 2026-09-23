"""หน้าตาบรรทัดคำสั่ง

มีไว้เพื่อให้ระบบใช้งานได้จริง และเพื่อให้เทสต์ได้ลองใช้ capsys
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .errors import ChatLogError
from .parser import parse_file
from .report import write_report
from .stats import build_stats, filter_current_month


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chatlog", description="สรุปไฟล์ประวัติแชท")
    parser.add_argument("path", help="ไฟล์ .txt ที่ส่งออกมาจากแอปแชท")
    parser.add_argument("--json", dest="json_out", help="เขียนรายงานเป็นไฟล์ JSON")
    parser.add_argument("--month", action="store_true", help="เอาเฉพาะเดือนนี้")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        messages = parse_file(args.path)
        if args.month:
            messages = filter_current_month(messages)
            if not messages:
                print("ไม่มีข้อความในเดือนนี้")
                return 1
        stats = build_stats(messages)
    except ChatLogError as exc:
        print(f"ผิดพลาด: {exc}")
        return 1
    except FileNotFoundError:
        print(f"ไม่พบไฟล์: {args.path}")
        return 1

    print(f"ช่วงเวลา        {stats.period_start} ถึง {stats.period_end}")
    print(f"จำนวนข้อความ    {stats.total_messages}")
    for name, count in stats.by_sender.items():
        print(f"  {name:<12} {count}")
    print(f"วันที่คุยเยอะสุด  {stats.busiest_day}")
    print(f"ข้อความดึก      {stats.late_night_count}")
    print(f"ตอบกลับเฉลี่ย    {stats.average_reply_minutes:.1f} นาที")

    if args.json_out:
        written = write_report(stats, Path(args.json_out))
        print(f"เขียนรายงานแล้ว  {written}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
