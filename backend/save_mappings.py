import pdfplumber
import psycopg2
import re

pdf_file = "วศ.บ. (วิศวกรรมคอมพิวเตอร์)-ปรับปรุง พ.ศ. 2566.pdf"
# กำหนดช่วงหน้าตารางเมทริกซ์จุดดำจุดขาว (Multi-page)
target_pages = [112, 113, 114, 115]

PRIMARY_SYMBOL = '⚫'
SECONDARY_SYMBOL = '\uf0a1'
plo_headers = ['1A', '1B', '1C', '1D', '1E', '2A', '2B', '2C', '2D', '2E', '3A', '3B', '3C', '4A', '4B', '4C', '5A', '5B', '5C', '5D']

print("🔍 กำลังสแกนตาราง Curriculum Mapping Matrix ข้ามหน้า...")

course_mappings = []

with pdfplumber.open(pdf_file) as pdf:
    for page_num in target_pages:
        if page_num - 1 >= len(pdf.pages):
            continue
        page = pdf.pages[page_num - 1]
        words = page.extract_words()
        
        # 1. ระบุพิกัดแนวนอนของคอลัมน์ Sub-PLO
        plo_positions = [
            {'plo': w['text'], 'x_center': (w['x0'] + w['x1']) / 2}
            for w in words if w['text'] in plo_headers
        ]
        
        # 2. จัดกลุ่มข้อความในแนวนอน (แถวเดียวกัน)
        rows = []
        for w in words:
            y_center = (w['top'] + w['bottom']) / 2
            matched_row = next((r for r in rows if abs(r['y_center'] - y_center) < 15), None)
            if matched_row:
                matched_row['words'].append(w)
            else:
                rows.append({'y_center': y_center, 'words': [w]})
                
        # 3. ตรวจจับจุดและจับคู่กับ Sub-PLO
        for row in rows:
            row['words'] = sorted(row['words'], key=lambda x: x['x0'])
            subject_name_parts = []
            dots = []
            
            for w in row['words']:
                text = w['text']
                if PRIMARY_SYMBOL in text or SECONDARY_SYMBOL in text:
                    sym_x = (w['x0'] + w['x1']) / 2
                    res_type = "ความรับผิดชอบหลัก" if PRIMARY_SYMBOL in text else "ความรับผิดชอบรอง"
                    for plo in plo_positions:
                        if abs(sym_x - plo['x_center']) < 15:
                            dots.append({'plo': plo['plo'], 'type': res_type})
                            break
                else:
                    subject_name_parts.append(text)
            
            if dots:
                raw_name = "".join(subject_name_parts).strip()
                clean_name = re.sub(r'\s+', '', raw_name)
                if clean_name and "ความรับผิดชอบ" not in clean_name:
                    course_mappings.append({
                        'course_name': clean_name,
                        'mappings': dots
                    })

print(f"✅ สกัดพบข้อมูล Mapping {len(course_mappings)} รายการ กำลังบันทึกลง PostgreSQL...")

try:
    conn = psycopg2.connect(dbname="postgres", user="postgres", password="1234", host="localhost", port="5432")
    cursor = conn.cursor()
    
    # เคลียร์ข้อมูลเดิมโดยไม่ DROP ตาราง เพื่อรักษา Trigger modtime ไว้
    cursor.execute("TRUNCATE TABLE curriculum_mappings CASCADE;")
    
    # สร้าง Lookup ดึง UUID ของ PLO ทั้งหมด
    cursor.execute("SELECT plo_code, id FROM plos;")
    plo_lookup = {code: p_id for code, p_id in cursor.fetchall()}
    
    insert_count = 0
    missing_courses = 0
    
    for item in course_mappings:
        c_name = item['course_name']
        
        # ค้นหา Course UUID
        cursor.execute("SELECT id FROM courses WHERE REPLACE(course_name_th, ' ', '') = %s LIMIT 1;", (c_name,))
        course_row = cursor.fetchone()
        
        if course_row:
            course_id = course_row[0]
            for m in item['mappings']:
                plo_id = plo_lookup.get(m['plo'])
                if plo_id:
                    # บันทึกด้วยคอลัมน์ responsibility_type ตาม init.sql
                    cursor.execute("""
                        INSERT INTO curriculum_mappings (course_id, plo_id, responsibility_type)
                        VALUES (%s, %s, %s);
                    """, (course_id, plo_id, m['type']))
                    insert_count += 1
        else:
            missing_courses += 1
            
    conn.commit()
    print(f"🎉 บันทึกจุด Mapping ลงตาราง curriculum_mappings สำเร็จ {insert_count} จุด")
    if missing_courses > 0:
        print(f"⚠️ ข้ามไป {missing_courses} รายวิชาที่ชื่อใน Mapping ไม่ตรงกับตาราง courses")

except Exception as e:
    print(f"❌ เกิดข้อผิดพลาด: {e}")
    if 'conn' in locals(): conn.rollback()
finally:
    if 'cursor' in locals(): cursor.close()
    if 'conn' in locals() and getattr(conn, 'closed', 0) == 0: conn.close()