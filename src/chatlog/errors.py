"""ข้อผิดพลาดทั้งหมดของระบบ

แยกไฟล์ไว้ต่างหากเพราะเทสต์ต้องอ้างถึงคลาสพวกนี้บ่อย
และการมีคลาสของตัวเองทำให้ `pytest.raises` ระบุได้แม่นกว่าการใช้ ValueError ลอยๆ
"""


class ChatLogError(Exception):
    """คลาสแม่ของทุก error ในระบบนี้"""


class ParseError(ChatLogError):
    """แกะไฟล์ไม่ได้ในระดับที่ไปต่อไม่ไหว (คนละเรื่องกับบรรทัดขยะที่ข้ามได้)"""

    def __init__(self, line_no: int, line: str, reason: str) -> None:
        self.line_no = line_no
        self.line = line
        self.reason = reason
        super().__init__(f"บรรทัดที่ {line_no}: {reason} -> {line!r}")


class EmptyChatError(ChatLogError):
    """ไฟล์อ่านได้ แต่ไม่มีข้อความสักข้อความเดียว"""


class MissingApiKeyError(ChatLogError):
    """จะเรียก AI แต่ไม่มีคีย์"""
