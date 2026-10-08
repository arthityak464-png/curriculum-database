import pdfplumber
import psycopg2
import re
import json

pdf_file = "วศ.บ. (วิศวกรรมคอมพิวเตอร์)-ปรับปรุง พ.ศ. 2566.pdf"

print("🔍 กำลังสแกนหา 'ปรัชญา' 'วัตถุประสงค์' และ 'รายชื่ออาจารย์ผู้รับผิดชอบ' จากหน้าเนื้อหาจริง...")

curriculum_data = {
    "philosophy": "",
    "objectives": "",
    "instructors": []
}

with pdfplumber.open(pdf_file) as pdf:
    current_section = None
    
    # 1. สแกนเฉพาะหน้า 15 ถึง 20 (index 14 ถึง 19) เพื่อตัดปัญหาหน้าสารบัญ/คำนำ
    for page_idx in range(14, min(22, len(pdf.pages))):
        page = pdf.pages[page_idx]
        text = page.extract_text()
        if not text:
            continue
            
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # ตรวจจับหัวข้อ ปรัชญา (หัวข้อ 1.1)
            if re.search(r'1\.1\s*ปรัชญาของหลักสูตร', line):
                current_section = "philosophy"
                continue
            # ตัดจบปรัชญาเมื่อเข้าสู่หัวข้อ 1.2 หรือ 1.3
            elif current_section == "philosophy" and re.match(r'^(1\.[2-9]|ความสำคัญ|อัตลักษณ์)', line):
                current_section = None
                
            # ตรวจจับหัวข้อ วัตถุประสงค์ (หัวข้อ 1.4)
            if re.search(r'1\.4\s*วัตถุประสงค์', line):
                current_section = "objectives"
                continue
            # ตัดจบวัตถุประสงค์เมื่อเข้าสู่หัวข้อหมวดถัดไป (เช่น 2. ผลลัพธ์ หรือ หมวดที่)
            elif current_section == "objectives" and re.match(r'^(2\.|หมวดที่|แผนพัฒนา)', line):
                current_section = None
                
            # สะสมข้อความตามหัวข้อที่กำลังอ่าน
            if current_section == "philosophy":
                if not re.search(r'^(หน้า\s*\d+|หลักสูตรวิศวกรรมศาสตรบัณฑิต)', line):
                    curriculum_data["philosophy"] += line + " "
            elif current_section == "objectives":
                if not re.search(r'^(หน้า\s*\d+|หลักสูตรวิศวกรรมศาสตรบัณฑิต)', line):
                    curriculum_data["objectives"] += line + " "

    # 2. สแกนรายชื่ออาจารย์ผู้รับผิดชอบหลักสูตรจากตาราง (สแกน 25 หน้าแรก)
    for i in range(min(25, len(pdf.pages))):
        page = pdf.pages[i]
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                if not row:
                    continue
                for col_idx, cell in enumerate(row):
                    if cell and isinstance(cell, str):
                        clean_cell = cell.replace('\n', ' ').strip()
                        match = re.search(r'^(นาย|นาง|นางสาว)\s*([ก-๙]+)\s+([ก-๙*]+)', clean_cell)
                        if match:
                            prefix, fname, lname = match.group(1), match.group(2), match.group(3)
                            title = "อาจารย์"
                            if col_idx > 0 and row[col_idx - 1]:
                                prev_cell = str(row[col_idx - 1]).replace('\n', '').strip()
                                if any(t in prev_cell for t in ["อาจารย์", "ผศ.", "รศ.", "ศ.", "ดร.", "ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์"]):
                                    title = prev_cell
                            full_name = f"{title} {prefix}{fname} {lname}".strip()
                            if full_name not in curriculum_data["instructors"]:
                                curriculum_data["instructors"].append(full_name)

curriculum_data["philosophy"] = curriculum_data["philosophy"].strip()
curriculum_data["objectives"] = curriculum_data["objectives"].strip()

print(f"✅ สกัดสำเร็จ:")
print(f"   - ปรัชญา: {len(curriculum_data['philosophy'])} ตัวอักษร")
print(f"   - วัตถุประสงค์: {len(curriculum_data['objectives'])} ตัวอักษร")
print(f"   - อาจารย์: {len(curriculum_data['instructors'])} ท่าน")

# เตรียมข้อมูล raw_json
raw_metadata = {
    "philosophy": curriculum_data["philosophy"],
    "objectives": curriculum_data["objectives"],
    "responsible_instructors": curriculum_data["instructors"]
}

try:
    conn = psycopg2.connect(dbname="postgres", user="postgres", password="1234", host="localhost", port="5432")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM curriculums WHERE curriculum_code = 'CPE2566';")
    row = cursor.fetchone()
    
    instructors_json = json.dumps(curriculum_data["instructors"], ensure_ascii=False)
    raw_json_str = json.dumps(raw_metadata, ensure_ascii=False)
    
    if row:
        cursor.execute("""
            UPDATE curriculums 
            SET philosophy = %s, 
                objectives = %s, 
                responsible_instructors = %s::jsonb,
                raw_json = %s::jsonb
            WHERE id = %s;
        """, (curriculum_data["philosophy"], curriculum_data["objectives"], instructors_json, raw_json_str, row[0]))
        print("🎉 อัปเดตข้อมูลลงตาราง curriculums เรียบร้อยแล้ว")
    else:
        cursor.execute("""
            INSERT INTO curriculums (
                curriculum_code, curriculum_name_th, curriculum_name_en, degree_name_th, 
                degree_name_en, faculty, department, total_credits, philosophy, 
                objectives, responsible_instructors, raw_json, file_path, file_hash_sha256
            ) VALUES (
                'CPE2566', 'วิศวกรรมคอมพิวเตอร์', 'Computer Engineering', 'วศ.บ.', 
                'B.Eng.', 'มหาวิทยาลัยกาฬสินธุ์', 'วิศวกรรมคอมพิวเตอร์', 126, %s, 
                %s, %s::jsonb, %s::jsonb, %s, 'hash_placeholder'
            );
        """, (curriculum_data["philosophy"], curriculum_data["objectives"], instructors_json, raw_json_str, pdf_file))
        print("🎉 สร้างแถวข้อมูลหลักสูตรใหม่ในตาราง curriculums เรียบร้อยแล้ว")
        
    conn.commit()

except Exception as e:
    print(f"❌ เกิดข้อผิดพลาด: {e}")
    if 'conn' in locals(): conn.rollback()
finally:
    if 'cursor' in locals(): cursor.close()
    if 'conn' in locals() and getattr(conn, 'closed', 0) == 0: conn.close()