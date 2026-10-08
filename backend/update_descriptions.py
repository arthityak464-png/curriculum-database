import pdfplumber
import psycopg2
import re

# ในอนาคตตัวแปรนี้จะรับค่าจากการอัปโหลดไฟล์ผ่าน API
pdf_file = "วศ.บ. (วิศวกรรมคอมพิวเตอร์)-ปรับปรุง พ.ศ. 2566.pdf"

print("🔍 กำลังสแกนหา 'คำอธิบายรายวิชา' จากทุกหน้าในเอกสาร PDF...")

course_descriptions = {}
current_course = None
current_desc = []

with pdfplumber.open(pdf_file) as pdf:
    # สแกนทุกหน้าในเอกสาร (Dynamic Page Scanning)
    for page in pdf.pages:
        text = page.extract_text()
        if not text: continue
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # ตรวจจับรูปแบบรหัสวิชาที่ขึ้นต้นบรรทัด (เช่น "SC-061-104 แคลคูลัส...")
            course_match = re.match(r'^([A-Z]{2}-\d{3}-\d{3})\s+', line)
            
            if course_match:
                # บันทึกคำอธิบายของวิชาก่อนหน้าเมื่อเจอวิชาใหม่
                if current_course:
                    course_descriptions[current_course] = " ".join(current_desc).strip()
                
                current_course = course_match.group(1)
                current_desc = []
            elif current_course:
                # ตัวกรอง (Filter) เพื่อตัดข้อความขยะ เช่น เลขหน้า หรือคำว่าวิชาบังคับก่อน
                if not re.search(r'^(วิชาบังคับก่อน|Prerequisite|หน้า\s*\d+|หลักสูตรวิศวกรรมศาสตรบัณฑิต|ภาคผนวก)', line):
                    current_desc.append(line)
                    
    # บันทึกข้อมูลของวิชาสุดท้ายเมื่ออ่านจบเล่ม
    if current_course:
        course_descriptions[current_course] = " ".join(current_desc).strip()

print(f"✅ สแกนจบทั้งเล่ม พบคำอธิบายที่เข้าข่าย {len(course_descriptions)} รายการ กำลังอัปเดตลงฐานข้อมูล...")

try:
    conn = psycopg2.connect(dbname="postgres", user="postgres", password="1234", host="localhost", port="5432")
    cursor = conn.cursor()
    update_count = 0
    
    for code, desc in course_descriptions.items():
        cursor.execute("""
            UPDATE courses 
            SET description_th = %s, updated_at = CURRENT_TIMESTAMP
            WHERE course_code = %s
        """, (desc, code))
        
        if cursor.rowcount > 0:
            update_count += 1

    conn.commit()
    print(f"🎉 อัปเดตคำอธิบายรายวิชาลงตาราง courses สำเร็จ {update_count} รายวิชา!")

except Exception as e:
    print(f"❌ เกิดข้อผิดพลาดกับฐานข้อมูล: {e}")
    if 'conn' in locals(): conn.rollback()
finally:
    if 'cursor' in locals(): cursor.close()
    if 'conn' in locals(): conn.close()