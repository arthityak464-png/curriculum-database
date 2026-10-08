import pdfplumber
import psycopg2
import re

pdf_file = "วศ.บ. (วิศวกรรมคอมพิวเตอร์)-ปรับปรุง พ.ศ. 2566.pdf"

print("🔍 กำลังสแกนหา 'วิชาบังคับก่อน' จากคำอธิบายรายวิชาในไฟล์ PDF...")

prerequisites_data = []
current_course_code = None

with pdfplumber.open(pdf_file) as pdf:
    # สแกนตั้งแต่หน้า 42 ถึง 78 ซึ่งเป็นหมวดคำอธิบายรายวิชา
    for i in range(41, 78):
        page = pdf.pages[i]
        text = page.extract_text()
        if not text: continue
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            
            # 1. ดักจับรหัสวิชาหลักที่กำลังอธิบาย (เช่น "SC-061-104 แคลคูลัสสำหรับวิศวกรรม 2")
            course_match = re.match(r'^([A-Z]{2}-\d{3}-\d{3})\s+', line)
            if course_match:
                current_course_code = course_match.group(1)
                
            # 2. ดักจับคำว่า "รายวิชาบังคับก่อน:" หรือ "Prerequisite:"
            prereq_match = re.search(r'รายวิชาบังคับก่อน\s*:\s*([A-Z]{2}-\d{3}-\d{3})', line)
            if not prereq_match:
                prereq_match = re.search(r'Prerequisite\s*:\s*([A-Z]{2}-\d{3}-\d{3})', line)
                
            if prereq_match and current_course_code:
                prereq_code = prereq_match.group(1)
                prerequisites_data.append({
                    "course_code": current_course_code,
                    "prereq_code": prereq_code
                })
                # เคลียร์ค่าเพื่อรอจับวิชาถัดไป
                current_course_code = None

print(f"✅ สแกนพบวิชาที่มีเงื่อนไขบังคับก่อนทั้งหมด {len(prerequisites_data)} คู่")

try:
    # เชื่อมต่อฐานข้อมูลที่พอร์ต 5432 ตามที่คุณตั้งค่าไว้
    conn = psycopg2.connect(dbname="postgres", user="postgres", password="1234", host="localhost", port="5432")
    cursor = conn.cursor()
    
    # เคลียร์ข้อมูลเก่า
    cursor.execute("TRUNCATE TABLE course_prerequisites CASCADE;")
    
    insert_count = 0
    missing_courses = 0
    
    for data in prerequisites_data:
        # หา course_id ของวิชาหลักจากตาราง courses
        cursor.execute("SELECT id FROM courses WHERE course_code = %s", (data['course_code'],))
        course_result = cursor.fetchone()
        
        # หา course_id ของวิชาบังคับก่อนจากตาราง courses
        cursor.execute("SELECT id FROM courses WHERE course_code = %s", (data['prereq_code'],))
        prereq_result = cursor.fetchone()
        
        if course_result:
            course_id = course_result[0]
            prereq_id = prereq_result[0] if prereq_result else None
            
            cursor.execute("""
                INSERT INTO course_prerequisites (course_id, prerequisite_course_code, prerequisite_course_id)
                VALUES (%s, %s, %s)
            """, (course_id, data['prereq_code'], prereq_id))
            insert_count += 1
        else:
            missing_courses += 1
            
    conn.commit()
    print(f"🎉 บันทึกข้อมูลสำเร็จ! เพิ่มเงื่อนไขลงฐานข้อมูล {insert_count} รายการ")
    if missing_courses > 0:
        print(f"⚠️ ข้ามการบันทึกไป {missing_courses} รายการ เนื่องจากยังไม่ได้ดึงรายวิชาหลักเข้าตาราง courses")

except Exception as e:
    print(f"❌ เกิดข้อผิดพลาดกับฐานข้อมูล: {e}")
    if 'conn' in locals(): conn.rollback()
finally:
    if 'cursor' in locals(): cursor.close()
    if 'conn' in locals(): conn.close()