import pdfplumber
import psycopg2
import re

pdf_file = "วศ.บ. (วิศวกรรมคอมพิวเตอร์)-ปรับปรุง พ.ศ. 2566.pdf"

print("🔍 กำลังสแกนหาคำอธิบายผลการเรียนรู้ (PLO และ Sub PLO) จากไฟล์ PDF...")

plos_dict = {}
current_main_code = None
current_sub_code = None

with pdfplumber.open(pdf_file) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
            
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            
            # 1. ดักจับหมวดหลัก เช่น "PLO 1 : สามารถใช้หลักการ..."
            main_match = re.match(r'^PLO\s*(\d+)\s*:?\s*(.+)', line)
            if main_match:
                main_code = main_match.group(1)
                if main_code not in plos_dict:
                    plos_dict[main_code] = {
                        "code": main_code,
                        "description": main_match.group(2).strip(),
                        "subs": {}
                    }
                current_main_code = main_code
                current_sub_code = None
                continue
            
            # 2. ดักจับข้อย่อย เช่น "Sub PLO 1A : อธิบายหลักการ..." หรือ "Sub PLO 2D ประยุกต์ใช้..."
            sub_match = re.match(r'^Sub\s*PLO\s*([1-9][A-Z])\s*:?\s*(.+)', line)
            if sub_match:
                plo_code = sub_match.group(1)
                description = sub_match.group(2).strip()
                
                # สกัดเอาเลขหมวดหลักจากรหัสข้อย่อย (เช่น "1A" -> "1")
                parent_code = plo_code[0]
                
                if parent_code in plos_dict:
                    plos_dict[parent_code]["subs"][plo_code] = description
                    current_main_code = parent_code
                    current_sub_code = plo_code
                continue
                
            # 3. เก็บตกข้อความบรรทัดถัดไปกรณีที่คำอธิบายยาวจนถูกตัดขึ้นบรรทัดใหม่
            if current_main_code and current_sub_code and len(line) > 2:
                # ป้องกันไม่ให้กวาดเอาคำว่า PLO หรือหัวข้ออื่นๆ มารวม
                if not re.match(r'^(PLO|Sub|ระดับ|ปีที่|ชั้นปี)', line):
                    plos_dict[current_main_code]["subs"][current_sub_code] += " " + line

total_mains = len(plos_dict)
total_subs = sum(len(m["subs"]) for m in plos_dict.values())
print(f"✅ สแกนเสร็จสิ้น! พบหมวดหลัก {total_mains} หมวด และข้อย่อย {total_subs} ข้อ กำลังบันทึกลง PostgreSQL...")

try:
    conn = psycopg2.connect(dbname="postgres", user="postgres", password="1234", host="localhost", port="5432")
    cursor = conn.cursor()
    
    # เคลียร์ข้อมูลเก่าเพื่อสร้างใหม่แบบสมบูรณ์
    cursor.execute("TRUNCATE TABLE plos CASCADE;")
    
    cursor.execute("SELECT id FROM curriculums LIMIT 1;")
    curriculum_result = cursor.fetchone()
    curriculum_id = curriculum_result[0] if curriculum_result else None

    if not curriculum_id:
        print("❌ ไม่พบข้อมูลหลักสูตรในตาราง curriculums")
    elif total_mains > 0:
        insert_count = 0
        for m_code, main in plos_dict.items():
            # บันทึกหมวดหลัก
            cursor.execute("""
                INSERT INTO plos (curriculum_id, plo_code, plo_description, parent_plo_id)
                VALUES (%s, %s, %s, NULL) RETURNING id
            """, (curriculum_id, main['code'], main['description']))
            parent_id = cursor.fetchone()[0]
            
            # บันทึกข้อย่อย
            for s_code, s_desc in main['subs'].items():
                cursor.execute("""
                    INSERT INTO plos (curriculum_id, plo_code, plo_description, parent_plo_id)
                    VALUES (%s, %s, %s, %s)
                """, (curriculum_id, s_code, s_desc, parent_id))
                insert_count += 1

        conn.commit()
        print(f"🎉 บันทึกข้อมูล PLO สำเร็จ! เพิ่มข้อย่อยทั้งหมด {insert_count} ข้อลงฐานข้อมูลเรียบร้อยแล้ว")
    else:
        print("⚠️ ไม่พบข้อมูล PLO (ลองตรวจสอบความถูกต้องของไฟล์อีกครั้ง)")

except Exception as e:
    print(f"❌ เกิดข้อผิดพลาดกับฐานข้อมูล: {e}")
    if 'conn' in locals(): conn.rollback()
finally:
    if 'cursor' in locals(): cursor.close()
    if 'conn' in locals(): conn.close()