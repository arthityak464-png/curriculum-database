import pdfplumber

def search_mapping_page(pdf_path):
    # คำค้นหาที่มักจะอยู่บนหัวตารางจุดดำจุดขาว
    keywords = ["แผนที่แสดงการกระจายความรับผิดชอบ", "ความรับผิดชอบหลัก", "ความรับผิดชอบรอง"]
    
    print("🔍 กำลังสแกนหาหน้าที่มีตาราง Curriculum Mapping...")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    # ถ้าเจอคำใดคำหนึ่งใน keywords ให้ถือว่าเจอหน้าที่ต้องการ
                    if any(keyword in text for keyword in keywords):
                        print(f"✅ เจอแล้ว! ตารางน่าจะเริ่มต้นที่หน้า {i + 1}")
                        return i + 1
        print("❌ สแกนจนจบเล่มแล้ว แต่ไม่พบคำค้นหาที่ต้องการ")
    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {e}")

pdf_file = "วศ.บ. (วิศวกรรมคอมพิวเตอร์)-ปรับปรุง พ.ศ. 2566.pdf"
search_mapping_page(pdf_file)