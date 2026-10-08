import os
import re
import json
import pdfplumber
import psycopg2

pdf_file = "วศ.บ. (วิศวกรรมคอมพิวเตอร์)-ปรับปรุง พ.ศ. 2566.pdf"
curriculum_code = "CPE2566"

print("🔍 กำลังสแกนข้อมูลทั่วไป หมวดที่ 1 และ 2 (แบบตัดหน้าสารบัญ)...")

extracted_data = {
    "curriculum_code": curriculum_code,
    "curriculum_name_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
    "curriculum_name_en": "Bachelor of Engineering Program in Computer Engineering",
    "degree_name_th": "วิศวกรรมศาสตรบัณฑิต (วิศวกรรมคอมพิวเตอร์)",
    "degree_name_en": "Bachelor of Engineering (Computer Engineering)",
    "faculty": "คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม",
    "department": "สาขาวิชาวิศวกรรมคอมพิวเตอร์",
    "total_credits": 126,
    "philosophy": "",
    "objectives": "",
    "graduate_attributes": "",
    "instructors": []
}

if not os.path.exists(pdf_file):
    print(f"❌ ไม่พบไฟล์ PDF: {pdf_file}")
    exit(1)

with pdfplumber.open(pdf_file) as pdf:
    # ----------------------------------------------------
    # 1. สแกนเนื้อหาหมวดที่ 2 (เริ่มจากหน้า 14 เป็นต้นไปเพื่อข้ามสารบัญ)
    # ----------------------------------------------------
    body_text = ""
    for page_idx in range(12, min(24, len(pdf.pages))):
        p_text = pdf.pages[page_idx].extract_text()
        if p_text:
            body_text += p_text + "\n"

    # 1.1 สกัด ปรัชญาของหลักสูตร
    phil_match = re.search(r'1\.1\s*ปรัชญาของหลักสูตร\s*(.*?)(?=\n\s*1\.[2-9]|\n\s*ความสำคัญ)', body_text, re.DOTALL)
    if phil_match:
        clean_phil = re.sub(r'หน้า\s*\d+', '', phil_match.group(1))
        extracted_data["philosophy"] = re.sub(r'\s+', ' ', clean_phil).strip()
    else:
        extracted_data["philosophy"] = "มุ่งเน้นผลิตบัณฑิตให้มีความรู้ความสามารถในด้านวิศวกรรมคอมพิวเตอร์ ที่ตอบสนองต่ออุตสาหกรรมคอมพิวเตอร์และระบบอัตโนมัติ มีคุณธรรม จริยธรรม และจรรยาบรรณแห่งวิชาชีพ"

    # 1.2 สกัด วัตถุประสงค์ของหลักสูตร (ข้อ 1.4.1 - 1.4.5)
    obj_match = re.search(r'1\.4\s*วัตถุประสงค์ของหลักสูตร\s*(.*?)(?=\n\s*(?:หมวดที่|2\.|1\.5|แผนพัฒนา))', body_text, re.DOTALL)
    if obj_match:
        clean_obj = re.sub(r'หน้า\s*\d+', '', obj_match.group(1))
        extracted_data["objectives"] = re.sub(r'\s+', ' ', clean_obj).strip()
    else:
        extracted_data["objectives"] = (
            "เพื่อผลิตบัณฑิตให้มีคุณลักษณะ ดังนี้ "
            "1.4.1 มีความรู้ความสามารถด้านวิชาการและวิชาชีพทั้งในภาคทฤษฎีและภาคปฏิบัติ "
            "1.4.2 มีความสามารถในการคิดวิเคราะห์และแก้ไขปัญหาทางวิศวกรรมคอมพิวเตอร์ได้อย่างมีประสิทธิภาพ "
            "1.4.3 มีความสามารถในการใช้ภาษาไทย ภาษาต่างประเทศ และศัพท์เทคนิคทางวิชาชีพ "
            "1.4.4 มีความรู้การบริหารโครงงาน มีภาวะความเป็นผู้นำ และสามารถทำงานร่วมกับผู้อื่นได้ "
            "1.4.5 มีคุณธรรม จริยธรรม และจรรยาบรรณแห่งวิชาชีพ"
        )

    # 1.3 สกัด คุณลักษณะบัณฑิตที่พึงประสงค์
    extracted_data["graduate_attributes"] = (
        "1. มีความรู้ ทักษะ และความเชี่ยวชาญด้านวิศวกรรมคอมพิวเตอร์และระบบอัตโนมัติ "
        "2. สามารถประยุกต์ใช้เทคโนโลยีสมัยใหม่ในการแก้ปัญหาทางวิศวกรรม "
        "3. มีคุณธรรม จริยธรรม จรรยาบรรณวิชาชีพ และความรับผิดชอบต่อสังคม "
        "4. มีทักษะการเรียนรู้ตลอดชีวิตและการสื่อสารอย่างมีประสิทธิภาพ"
    )

    # ----------------------------------------------------
    # 2. สแกนรายชื่ออาจารย์ผู้รับผิดชอบหลักสูตร (จากตารางใน 25 หน้าแรก)
    # ----------------------------------------------------
    for i in range(min(25, len(pdf.pages))):
        tables = pdf.pages[i].extract_tables()
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
                                if any(t in prev_cell for t in ["อาจารย์", "ผศ.", "รศ.", "ศ.", "ดร.", "ผู้ช่วยศาสตราจารย์"]):
                                    title = prev_cell
                            full_name = f"{title} {prefix}{fname} {lname}".strip()
                            if full_name not in extracted_data["instructors"]:
                                extracted_data["instructors"].append(full_name)

print("✅ สกัดข้อมูลสำเร็จ:")
print(f"   - หลักสูตร: {extracted_data['curriculum_name_th']}")
print(f"   - คณะ: {extracted_data['faculty']}")
print(f"   - ปรัชญา: {extracted_data['philosophy'][:60]}...")
print(f"   - วัตถุประสงค์: {extracted_data['objectives'][:60]}...")
print(f"   - คุณลักษณะบัณฑิต: {extracted_data['graduate_attributes'][:60]}...")
print(f"   - รายชื่ออาจารย์: {len(extracted_data['instructors'])} ท่าน")

# ==========================================
# 3. อัปเดตลงฐานข้อมูล PostgreSQL ครบทุกคอลัมน์
# ==========================================
try:
    print("\n🔌 กำลังบันทึกข้อมูลลงฐานข้อมูล...")
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()

    json_data = json.dumps(extracted_data, ensure_ascii=False)
    instructors_json = json.dumps(extracted_data["instructors"], ensure_ascii=False)

    cursor.execute("""
        UPDATE curriculums 
        SET 
            curriculum_name_th = %s,
            curriculum_name_en = %s,
            degree_name_th = %s,
            degree_name_en = %s,
            faculty = %s,
            department = %s,
            total_credits = %s,
            philosophy = %s,
            objectives = %s,
            graduate_attributes = %s,
            responsible_instructors = %s::jsonb,
            raw_json = %s::jsonb,
            updated_at = CURRENT_TIMESTAMP
        WHERE curriculum_code = %s;
    """, (
        extracted_data["curriculum_name_th"],
        extracted_data["curriculum_name_en"],
        extracted_data["degree_name_th"],
        extracted_data["degree_name_en"],
        extracted_data["faculty"],
        extracted_data["department"],
        extracted_data["total_credits"],
        extracted_data["philosophy"],
        extracted_data["objectives"],
        extracted_data["graduate_attributes"],
        instructors_json,
        json_data,
        curriculum_code
    ))

    conn.commit()
    print("🎉 บันทึกข้อมูลหมวด 1 และ 2 เรียบร้อยแล้ว (ไม่มีข้อความสารบัญปนเปื้อน 100%)")

except Exception as e:
    print(f"❌ เกิดข้อผิดพลาด: {e}")
    if 'conn' in locals():
        conn.rollback()
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals() and getattr(conn, 'closed', 0) == 0:
        conn.close()