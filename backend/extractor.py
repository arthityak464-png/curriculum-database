import pdfplumber
import re
import psycopg2
from pydantic import BaseModel, ValidationError

# 1. Pydantic Schema
class CourseSchema(BaseModel):
    course_code: str
    course_name_th: str
    course_name_en: str
    total_credits: int
    credit_lecture: int
    credit_lab: int
    credit_self: int

# 2. ฟังก์ชันหั่นหน่วยกิต
def parse_credit_string(credit_str):
    match = re.search(r'(\d+)\s*\(\s*(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s*\)', credit_str)
    if match:
        return {
            "total_credits": int(match.group(1)),
            "credit_lecture": int(match.group(2)),
            "credit_lab": int(match.group(3)),
            "credit_self": int(match.group(4))
        }
    return {"total_credits": 0, "credit_lecture": 0, "credit_lab": 0, "credit_self": 0}

# 3. ฟังก์ชันสกัดและตรวจสอบข้อความ
def extract_and_validate_courses(pdf_path, start_page, end_page):
    valid_courses = []
    course_codes_seen = set()

    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(start_page - 1, end_page):
            page = pdf.pages[page_num]
            text = page.extract_text()
            if not text:
                continue
            
            # ลบเครื่องหมายขีดคั่นที่มักเกิดจากการดึงตาราง
            text = text.replace('|', '')
            lines = text.split('\n')
            
            for i in range(len(lines)):
                # นำ 4 บรรทัดมาต่อกันเพื่อป้องกันข้อมูลถูกตัดบรรทัด
                chunk = " ".join([line.strip() for line in lines[i:i+4] if line.strip()])
                
                # ค้นหารหัสวิชา ชื่อวิชา และหน่วยกิต ในก้อนข้อความ
                match = re.search(r'([A-Z]{2}-\d{3}-\d{3})\s+(.+?)\s+(\d\s*\(\s*\d+\s*-\s*\d+\s*-\s*\d+\s*\))', chunk)
                
                if match:
                    course_code = match.group(1).strip()
                    
                    if course_code in course_codes_seen:
                        continue
                    course_codes_seen.add(course_code)
                    
                    course_name_th = match.group(2).strip()
                    credit_raw = match.group(3).strip()
                    course_name_en = ""
                    
                    # แยกชื่อภาษาอังกฤษออกถ้ามีปนมา
                    en_match = re.search(r'[A-Za-z]', course_name_th)
                    if en_match:
                        idx = en_match.start()
                        course_name_en = course_name_th[idx:].strip()
                        course_name_th = course_name_th[:idx].strip()
                    else:
                        # ถ้าไม่ปนกัน ให้ลองหาภาษาอังกฤษในบรรทัดถัดไป
                        if i + 1 < len(lines):
                            next_line = lines[i+1].strip()
                            if re.search(r'^[A-Za-z]', next_line):
                                course_name_en = next_line

                    credit_data = parse_credit_string(credit_raw)
                    
                    try:
                        prefix = course_code[:2]
                        if prefix == 'GE': course_group = 'หมวดวิชาศึกษาทั่วไป'
                        elif prefix == 'SC': course_group = 'หมวดวิชาวิทยาศาสตร์'
                        elif prefix == 'EN': course_group = 'หมวดวิชาวิศวกรรมศาสตร์'
                        else: course_group = 'อื่นๆ'

                        course_obj = CourseSchema(
                            course_code=course_code,
                            course_name_th=course_name_th,
                            course_name_en=course_name_en,
                            **credit_data
                        )
                        
                        course_dict = course_obj.model_dump()
                        course_dict['course_group'] = course_group
                        valid_courses.append(course_dict)
                        
                    except ValidationError as e:
                        print(f"❌ พบข้อมูลผิดรูปแบบที่รหัสวิชา {course_code}: {e}")

    return valid_courses

# 4. ฟังก์ชันบันทึกลงฐานข้อมูล
def save_to_database(courses_list):
    if not courses_list:
        print("ไม่มีข้อมูลสำหรับบันทึก")
        return

    print("\nกำลังเชื่อมต่อและบันทึกข้อมูลลง PostgreSQL...")
    try:
        conn = psycopg2.connect(
            dbname="postgres", user="postgres", password="1234", host="localhost", port="5432"
        )
        cursor = conn.cursor()
        
        cursor.execute("TRUNCATE TABLE courses CASCADE;")
        
        cursor.execute("SELECT id FROM curriculums LIMIT 1;")
        curriculum_result = cursor.fetchone()
        
        if not curriculum_result:
            cursor.execute("""
                INSERT INTO curriculums (
                    curriculum_code, curriculum_name_th, curriculum_name_en, degree_name_th, degree_name_en, faculty, department, total_credits, raw_json, file_path, file_hash_sha256
                ) VALUES (
                    'CPE2566', 'วิศวกรรมคอมพิวเตอร์', 'Computer Engineering', 'วศ.บ.', 'B.Eng.', 'มหาวิทยาลัยกาฬสินธุ์', 'วิศวกรรมคอมพิวเตอร์', 126, '{}', 'test.pdf', 'hash123'
                ) RETURNING id;
            """)
            curriculum_id = cursor.fetchone()[0]
        else:
            curriculum_id = curriculum_result[0]
        
        insert_count = 0
        for course in courses_list:
            cursor.execute("""
                INSERT INTO courses (
                    curriculum_id, course_code, course_name_th, course_name_en, 
                    total_credits, credit_lecture, credit_lab, credit_self, course_group
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                curriculum_id, course['course_code'], course['course_name_th'], course['course_name_en'], 
                course['total_credits'], course['credit_lecture'], course['credit_lab'], course['credit_self'], course['course_group']
            ))
            insert_count += 1
            
        conn.commit()
        print(f"✅ สำเร็จ! บันทึกข้อมูล {insert_count} รายวิชา ลงตาราง courses เรียบร้อยแล้ว")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการบันทึกฐานข้อมูล: {e}")
        if 'conn' in locals(): conn.rollback()
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

# --- เริ่มรันการทำงาน ---
pdf_file = "วศ.บ. (วิศวกรรมคอมพิวเตอร์)-ปรับปรุง พ.ศ. 2566.pdf"
start_page = 25
end_page = 78 

print(f"กำลังสกัดรายวิชาตั้งแต่หน้า {start_page} ถึง {end_page}...")
result = extract_and_validate_courses(pdf_file, start_page, end_page)

save_to_database(result)