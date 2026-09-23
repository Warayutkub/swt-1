"""อ่านรายงาน JUnit XML ที่ pytest สร้าง แล้วพิมพ์เป็นตาราง Markdown

ใช้ใน GitHub Actions เพื่อให้เห็นผลสรุปบนหน้ารันได้เลย โดยไม่ต้องเปิด log

    python scripts/summarize_junit.py reports/junit.xml
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def summarize(path: Path) -> str:
    if not path.exists():
        return "_ไม่พบรายงานผลการทดสอบ_"

    root = ET.parse(path).getroot()
    # pytest ห่อไว้ใน <testsuites> ตั้งแต่เวอร์ชันใหม่ ๆ แต่รุ่นเก่าไม่ห่อ
    suite = root if root.tag == "testsuite" else root[0]

    total = int(suite.get("tests", 0))
    failures = int(suite.get("failures", 0))
    errors = int(suite.get("errors", 0))
    skipped = int(suite.get("skipped", 0))
    passed = total - failures - errors - skipped
    seconds = float(suite.get("time", 0))

    lines = [
        "| รายการ | จำนวน |",
        "| --- | ---: |",
        f"| ทั้งหมด | {total} |",
        f"| ผ่าน | {passed} |",
        f"| ไม่ผ่าน | {failures} |",
        f"| ข้อผิดพลาด | {errors} |",
        f"| ข้าม / คาดว่าไม่ผ่าน | {skipped} |",
        f"| เวลาที่ใช้ | {seconds:.2f} วินาที |",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    target = Path(args[0]) if args else Path("reports/junit.xml")
    print(summarize(target))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
