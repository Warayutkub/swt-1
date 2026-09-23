# chat-analyzer

[![tests](https://github.com/Warayutkub/swt-1/actions/workflows/ci.yml/badge.svg)](https://github.com/Warayutkub/swt-1/actions/workflows/ci.yml)

แกะไฟล์ประวัติแชทที่ส่งออกมาจากแอป (เริ่มที่ LINE) แล้วสรุปเป็นสถิติและรายงาน

โปรเจคนี้เขียนขึ้นเพื่อ **ฝึกใช้ pytest ให้ครบทุกฟีเจอร์หลัก** ระบบจึงถูกออกแบบให้มีทั้ง
ตรรกะล้วน ๆ การอ่านเขียนไฟล์ การขึ้นกับวันเวลา อินพุตที่ผิดพลาดได้ และการเรียกบริการภายนอก
เพราะแต่ละอย่างต้องใช้เครื่องมือของ pytest คนละตัวกัน

| | |
|---|---|
| กรณีทดสอบ | **110 กรณี** จาก 83 ฟังก์ชัน — 107 ผ่าน · 2 ข้าม · 1 คาดว่าไม่ผ่าน |
| กรณีผิดพลาด | **34 กรณี** (41%) — มีครบทุกโมดูล |
| Coverage | **100%** (เกณฑ์ขั้นต่ำ 85%) |
| Python | 3.11 · 3.12 · pytest 9 |

### เอกสารประกอบ

| ไฟล์ | เนื้อหา |
|---|---|
| [`docs/TEST-CASES.md`](docs/TEST-CASES.md) | **ตารางกรณีทดสอบทั้ง 110 กรณี** แยกประเภท ปกติ / ขอบเขต / ผิดพลาด |
| [`docs/FAILURE-EVIDENCE.md`](docs/FAILURE-EVIDENCE.md) | **หลักฐานว่าเทสต์จับผิดได้จริง** — ทำให้พัง 6 แบบพร้อมผลรันจริง และบั๊กจริงที่เจอ |
| [`docs/PRESENTATION.md`](docs/PRESENTATION.md) | อธิบายว่าฟังก์ชันของ pytest แต่ละตัวทำงานยังไงข้างใน |

---

## เริ่มใช้งาน

```bash
python -m pip install pytest pytest-cov
python -m pytest
```

เทสต์รันได้เลยไม่ต้องติดตั้งตัวโปรเจค เพราะ `pyproject.toml` ตั้ง `pythonpath = ["src"]` ไว้

แต่ถ้าจะ**รันตัวโปรแกรมจริง** ต้องติดตั้งก่อนหนึ่งครั้ง:

```bash
python -m pip install -e .
```

```bash
python -m chatlog.cli samples/sample_chat.txt
python -m chatlog.cli samples/sample_chat.txt --json out/report.json
```

> **บน Windows:** ถ้าเห็นชื่อเทสต์ภาษาไทยเป็นรหัส `อ...` ให้ตั้ง `PYTHONIOENCODING=utf-8`
> ก่อนรัน หรือสั่ง `chcp 65001` ในหน้าต่างนั้นก่อน

---

## รันบนเครื่องอื่น (เช่น เครื่องในห้องเรียน)

โคลนแล้วรันได้เลย **ไม่ต้องติดตั้งตัวโปรเจค** เพราะ `pyproject.toml` ตั้ง `pythonpath = ["src"]` ไว้

### Windows (Command Prompt)

```bat
git clone https://github.com/Warayutkub/swt-1.git
cd swt-1
chcp 65001
set PYTHONIOENCODING=utf-8
python -m pip install pytest pytest-cov
python -m pytest -v
```

### macOS / Linux

```bash
git clone https://github.com/Warayutkub/swt-1.git
cd swt-1
python3 -m pip install pytest pytest-cov
python3 -m pytest -v
```

**ต้องได้:** `107 passed, 2 skipped, 1 xfailed`

| ปัญหาที่อาจเจอ | ทางแก้ |
|---|---|
| ชื่อเทสต์เป็นรหัส `อ...` | ลืม `chcp 65001` กับ `set PYTHONIOENCODING=utf-8` |
| `No module named pytest` | ยังไม่ได้ `pip install pytest pytest-cov` |
| `No module named chatlog` | รันจากนอกโฟลเดอร์โปรเจค — ต้อง `cd` เข้าไปก่อน |
| เครื่องไม่มีเน็ตให้ `pip install` | ใช้เครื่องตัวเอง หรือเตรียม `pip download` ใส่แฟลชไดรฟ์ไปก่อน |
| เทสต์ `PermissionError` ข้ามไป | ปกติบน Windows — บน Linux เทสต์นั้นจะรันจริง (ดู TC-RP08) |

> **บน macOS/Linux ตัวเลขจะต่างจากนี้** เพราะ TC-RP08 (เทสต์เรื่องสิทธิ์ไฟล์) ถูกข้ามเฉพาะบน
> Windows แต่รันจริงบนระบบอื่น ตัวเลขที่ต่างกันเป็นเรื่องปกติและอธิบายได้ —
> นี่คือสิ่งที่ `skipif` มีไว้ทำ
>
> ดูตัวเลขจริงบน Linux ได้ที่ [หน้า Actions](https://github.com/Warayutkub/swt-1/actions) →
> เลือกการรันล่าสุด → ตาราง "ผลการทดสอบ" จะอยู่บนหน้าสรุปของการรันนั้น

---

## ระบบทำอะไร

```
ไฟล์แชท .txt                    ┌──► สถิติ (ตัวเลข)
        │                       │
        └──► แกะเป็นข้อความ ─────┼──► รายงาน .json
                                │
                                └──► สรุปเป็นภาษาคน (ส่งให้ AI เขียน)
```

### โครงสร้าง

```
src/chatlog/
  models.py       Message - โครงสร้างข้อมูลกลาง (frozen dataclass)
  errors.py       ParseError, EmptyChatError, MissingApiKeyError
  clock.py        นาฬิกาของระบบ - ที่เดียวที่รู้ว่า "ตอนนี้กี่โมง"
  parser.py       ข้อความดิบ -> list[Message]
  rules.py        กฎทางธุรกิจ (ดึกมั้ย ตอบเร็วมั้ย)
  stats.py        คำนวณสถิติ
  report.py       เขียนรายงานลงไฟล์          <- แตะระบบไฟล์
  summarizer.py   เรียก AI ผ่าน HTTP         <- แตะเน็ต
  cli.py          หน้าตาบรรทัดคำสั่ง

tests/
  conftest.py            fixture ที่ทุกไฟล์ใช้ร่วมกัน
  unit/                  101 กรณี - ไม่แตะไฟล์ ไม่แตะเน็ต
  integration/           9 กรณี - ใช้ไฟล์จริง
    conftest.py          fixture เฉพาะชั้นนี้ (conftest ซ้อนชั้น)
```

**หลักการ:** ดันตรรกะทั้งหมดไปอยู่ในโมดูลที่บริสุทธิ์ แล้วให้ของที่ควบคุมยาก
(ไฟล์ เน็ต เวลา) อยู่ริมนอก — โครงสร้างแบบนี้คือสิ่งที่ทำให้เทสต์ได้

---

## ตารางแมป: ฟีเจอร์ของ pytest อยู่ไฟล์ไหน

### ต้องมี

| # | ฟีเจอร์ | ดูตัวอย่างได้ที่ |
|---|---|---|
| 1 | `assert` | ทุกไฟล์ |
| 2 | `pytest.raises(match=)` | `test_parser.py` · `test_summarizer.py` |
| 3 | `pytest.approx()` | `test_stats.py` — ค่าเฉลี่ยเวลาตอบกลับ 11.75 นาที |
| 4 | `@pytest.mark.parametrize` | `test_rules.py` — เทสต์ขอบเขต "ดึก" และ "6 ชั่วโมง" |
| 5 | `pytest.param(id=, marks=)` | `test_rules.py` · `test_parser.py` — ตั้งชื่อเคสภาษาไทย |
| 6 | `@pytest.fixture` + `yield` | `conftest.py::workspace` — เห็น setup/teardown ชัด |
| 7 | `conftest.py` | `tests/conftest.py` และ `tests/integration/conftest.py` (ซ้อนชั้น) |
| 8 | `scope="session"` | `conftest.py::big_chat_text` — ไฟล์ใหญ่ สร้างครั้งเดียว |
| 9 | `monkeypatch` | `conftest.py::frozen_clock` (setattr) · `test_summarizer.py` (setenv, delenv) |
| 10 | `tmp_path` | `test_report.py` · `conftest.py::chat_file` |
| 11 | `capsys` / `caplog` | `test_cli.py` (capsys) · `test_parser.py` (caplog) |
| 12 | `skip` / `skipif` / `xfail` | `test_parser.py` (skip, xfail strict) · `test_report.py` (skipif Windows) |
| 13 | marker ที่สร้างเอง | `pytestmark` ทุกไฟล์ + `@pytest.mark.slow` ใน `test_pipeline.py` |
| 14 | `pyproject.toml` | `[tool.pytest.ini_options]` |

### เสริม

| ฟีเจอร์ | อยู่ที่ |
|---|---|
| `pytest-cov` + เกณฑ์ขั้นต่ำ | `[tool.coverage.report] fail_under = 85` |
| mock ของที่ยิงเน็ต | `test_summarizer.py` — แทน `call_ai` และ `urlopen` |
| fixture เรียก fixture | `conftest.py::sample_messages` เรียก `sample_chat_text` |
| fixture เฉพาะไฟล์ | `test_report.py::stats` |

---

## กฎของระบบ (สิ่งที่เทสต์ตรวจ)

เทสต์ไม่ได้ตรวจว่า "โค้ดรันได้มั้ย" แต่ตรวจว่า **"มันตัดสินใจตามที่ตกลงกันไว้มั้ย"**

| # | กฎ | ตัดสินใจว่า |
|---|---|---|
| 1 | วันที่ของข้อความ | มาจากบรรทัดหัวที่อยู่เหนือขึ้นไป |
| 2 | ข้อความหลายบรรทัด | บรรทัดที่ไม่ขึ้นต้นด้วยเวลา = ต่อจากข้อความเดิม |
| 3 | รูป / สติกเกอร์ / สาย | นับเป็นข้อความ แต่ไม่เอาไปนับคำ |
| 4 | "ดึก" | 00:00 – 04:59 |
| 5 | เวลาตอบกลับ | นับเฉพาะตอนที่เปลี่ยนคนพูด |
| 6 | ห่างเกิน 6 ชั่วโมง | ไม่นับว่าตอบ ถือว่าเริ่มบทสนทนาใหม่ |
| 7 | พิมพ์รัวหลายข้อความ | วัดจากข้อความสุดท้ายของชุด |
| 8 | บรรทัดที่แกะไม่ออก | ข้ามไป + เขียน log ไม่ล้มทั้งไฟล์ |
| 9 | ไฟล์ว่าง / โครงสร้างพัง | โยน `EmptyChatError` / `ParseError` |
| 10 | "เดือนนี้" | อิงจากวันที่ของวันนี้ (จึงต้องล็อกเวลาตอนเทสต์) |

ตัวอย่างของกฎข้อ 5–7 จากไฟล์ตัวอย่าง:

```
09:12  มะลิ  กินข้าวยัง
09:15  ฉัน   ยังเลย           <- ตอบใน 3 นาที        นับ
09:15  ฉัน   เดี๋ยวกินแล้วโทร   <- ตัวเราเอง           ไม่นับ
23:47  มะลิ  ถึงหอแล้วนะ       <- ห่าง 14 ชม.        ไม่นับ
23:58  ฉัน   โอเค             <- ตอบใน 11 นาที      นับ
```

---

## คำสั่งที่ใช้บ่อย

| คำสั่ง | ทำอะไร |
|---|---|
| `pytest` | รันทั้งหมด |
| `pytest -v` | แสดงชื่อเทสต์ทีละตัว |
| `pytest -m unit` | เฉพาะ unit test |
| `pytest -m integration` | เฉพาะที่แตะไฟล์จริง |
| `pytest -m "not slow"` | ข้ามตัวที่ช้า |
| `pytest --cov` | รันพร้อมวัด coverage และเช็คเกณฑ์ขั้นต่ำ |
| `pytest -k "is_late_night"` | เลือกด้วยชื่อ (ใช้คำอังกฤษ — บาง terminal ส่งภาษาไทยผ่าน `-k` ไม่ได้) |
| `pytest -x` | เจอพังตัวแรกแล้วหยุด |
| `pytest --lf` | รันเฉพาะตัวที่พังรอบที่แล้ว |
| `pytest --collect-only` | ดูว่ามีเทสต์อะไรบ้างโดยไม่รัน |

---

## ลองทำให้พังดู

เทสต์จะมีประโยชน์ก็ต่อเมื่อมันจับได้จริง ลองแก้ตามนี้แล้วดูว่าอะไรแดง

เทสต์จะมีประโยชน์ก็ต่อเมื่อมันจับได้จริง ตารางนี้วัดมาแล้วทุกแถว

| แก้ตรงไหน | แดงกี่ตัว | เทสต์ที่จับได้ |
|---|---:|---|
| `rules.py` → `NIGHT_END` เป็น `time(6, 0)` | 1 | `test_is_late_night[ตีห้าตรง-หมดช่วงดึก]` |
| `rules.py` → `REPLY_GAP_LIMIT` เป็น 24 ชั่วโมง | **5** | ลามข้ามไปถึง `test_pipeline.py` และ `test_report.py` |
| `stats.py` → ปิด `if not message.is_countable_text` | 3 | `test_นับคำเฉพาะข้อความจริง` 3 เคส |
| `report.py` → `ensure_ascii` เป็น `True` | 1 | `test_ภาษาไทยไม่ถูกแปลงเป็นรหัส` |
| `summarizer.py` → เปลี่ยนข้อความ error | 1 | `test_ไม่มีคีย์ต้องโยน_error` (จับได้เพราะใส่ `match=`) |
| `pytest tests/unit/test_rules.py --cov` | **0** | ไม่มีเทสต์พังเลย แต่ **exit code = 1** |

แถวสุดท้ายสำคัญที่สุด: **เทสต์ผ่านหมด 21 ตัว แต่ยังถือว่าไม่ผ่าน** เพราะ coverage เหลือ 25%

> ผลรันจริงของทุกแถว รวมถึง **บั๊กจริงที่เจอตอนเขียนกรณีทดสอบเพิ่ม** อยู่ใน
> [`docs/FAILURE-EVIDENCE.md`](docs/FAILURE-EVIDENCE.md)

---

## สิ่งที่จงใจไม่ทำ

- **ตัดคำภาษาไทย** — ใช้การตัดด้วยช่องว่างซึ่งไม่ถูกต้องนัก ของจริงต้องใช้ `pythainlp`
- **รองรับ Instagram / WhatsApp** — มีเทสต์ที่ `skip` ไว้เป็นที่หมายแล้ว
- **ข้อความที่ถูกยกเลิกการส่ง** — มีเทสต์ `xfail(strict=True)` รออยู่ ถ้าทำเสร็จเมื่อไหร่ pytest จะเตือนให้มาลบ marker
- **E2E / เบราว์เซอร์ / ฐานข้อมูล** — อยู่นอกขอบเขตงานนี้
