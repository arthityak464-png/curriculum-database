import pdfplumber
import re

pdf_file = "วศ.บ. (วิศวกรรมคอมพิวเตอร์)-ปรับปรุง พ.ศ. 2566.pdf"
valid_domains = ["คุณธรรม", "จริยธรรม", "ความรู้", "ปัญญา", "สัมพันธ์", "รับผิดชอบ", "ตัวเลข", "สื่อสาร", "เทคโนโลยี", "ปฏิบัติ"]

print("🔍 โหมดตรวจสอบ (Debug): กำลังแอบดูข้อความดิบจาก PDF...\n")

with pdfplumber.open(pdf_file) as pdf:
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()
        if not text:
            continue
            
        lines = text.split('\n')
        found_main = False
        lines_to_print = 0
        
        for line in lines:
            line = line.strip()
            
            # ดักจับหมวดหลัก
            main_match = re.match(r'^([1-6])\.\s*(?:ด้าน)?\s*(.+)', line)
            if main_match:
                domain_text = main_match.group(2)
                if any(kw in domain_text for kw in valid_domains):
                    print(f"=====================================")
                    print(f"[เจอหมวดหลักที่หน้า {page_num + 1}]: {line}")
                    found_main = True
                    lines_to_print = 6  # สั่งให้ปริ้นท์ 6 บรรทัดถัดไป
                    continue
            
            # ปริ้นท์บรรทัดย่อยให้เห็นชัดๆ ว่ามีตัวอักษรอะไรซ่อนอยู่
            if found_main and lines_to_print > 0:
                print(f"ข้อความที่โปรแกรมเห็น -> '{line}'")
                lines_to_print -= 1
                if lines_to_print == 0:
                    found_main = False