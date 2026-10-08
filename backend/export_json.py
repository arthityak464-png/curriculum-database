import psycopg2
import json

print("🔄 กำลังรวบรวมข้อมูลทั้งหมดเพื่อสร้าง Tree-structured JSON (AI-Ready)...")

try:
    conn = psycopg2.connect(dbname="postgres", user="postgres", password="1234", host="localhost", port="5432")
    cursor = conn.cursor()

    # 1. ดึงข้อมูลหลักสูตร
    cursor.execute("""
        SELECT id, curriculum_code, curriculum_name_th, curriculum_name_en, degree_name_th, 
               degree_name_en, faculty, department, total_credits, philosophy, objectives, 
               graduate_attributes, responsible_instructors, raw_json
        FROM curriculums LIMIT 1;
    """)
    curr = cursor.fetchone()
    if not curr:
        print("❌ ไม่พบข้อมูลหลักสูตรในระบบ")
        exit()

    curr_id = curr[0]

    # 2. ดึงข้อมูล PLO และ Sub-PLO จัดเป็น Hierarchical Tree
    cursor.execute("SELECT id, plo_code, plo_description FROM plos WHERE parent_plo_id IS NULL AND curriculum_id = %s ORDER BY plo_code;", (curr_id,))
    parent_plos = cursor.fetchall()
    
    plos_tree = []
    for p_id, p_code, p_desc in parent_plos:
        cursor.execute("SELECT plo_code, plo_description FROM plos WHERE parent_plo_id = %s ORDER BY plo_code;", (p_id,))
        sub_plos = cursor.fetchall()
        plos_tree.append({
            "code": p_code,
            "description": p_desc,
            "sub_plos": [{"code": s[0], "description": s[1]} for s in sub_plos]
        })

    # 3. ดึงข้อมูลรายวิชา พร้อม Prerequisites และ Mappings
    cursor.execute("""
        SELECT id, course_code, course_name_th, course_name_en, total_credits, 
               credit_lecture, credit_lab, credit_self, course_group, description_th
        FROM courses WHERE curriculum_id = %s ORDER BY course_code;
    """, (curr_id,))
    courses = cursor.fetchall()

    courses_tree = []
    for c in courses:
        c_id, code, name_th, name_en, cred_total, c_lec, c_lab, c_self, group, desc = c

        # ดึงวิชาบังคับก่อน
        cursor.execute("SELECT prerequisite_course_code FROM course_prerequisites WHERE course_id = %s;", (c_id,))
        prereqs = [row[0] for row in cursor.fetchall()]

        # ดึง PLO ที่วิชานี้ตอบโจทย์ (พร้อมความรับผิดชอบหลัก/รอง)
        cursor.execute("""
            SELECT p.plo_code, m.responsibility_type 
            FROM curriculum_mappings m
            JOIN plos p ON m.plo_id = p.id
            WHERE m.course_id = %s;
        """, (c_id,))
        mappings = [{"plo_code": m[0], "responsibility": m[1]} for m in cursor.fetchall()]

        courses_tree.append({
            "course_code": code,
            "course_name_th": name_th,
            "course_name_en": name_en,
            "credits": {
                "total": cred_total,
                "lecture": c_lec,
                "lab": c_lab,
                "self_study": c_self
            },
            "course_group": group,
            "description_th": desc,
            "prerequisites": prereqs,
            "mapped_plos": mappings
        })

    # 4. ประกอบ Tree-structured JSON
    instructors = curr[12] if isinstance(curr[12], list) else (json.loads(curr[12]) if curr[12] else [])
    raw_info = curr[13] if isinstance(curr[13], dict) else (json.loads(curr[13]) if curr[13] else {})

    export_payload = {
        "curriculum_code": curr[1],
        "curriculum_name": {
            "th": curr[2],
            "en": curr[3]
        },
        "degree": {
            "th": curr[4],
            "en": curr[5]
        },
        "faculty": curr[6],
        "department": curr[7],
        "total_credits": curr[8],
        "curriculum_overview": {
            "philosophy": curr[9],
            "objectives": curr[10],
            "graduate_attributes": curr[11],
            "responsible_instructors": instructors,
            "raw_metadata": raw_info
        },
        "program_learning_outcomes": plos_tree,
        "courses": courses_tree
    }

    # 5. บันทึกลงไฟล์
    output_filename = "curriculum_export.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(export_payload, f, ensure_ascii=False, indent=2)

    print(f"✅ สำเร็จ! ส่งออก Tree-structured JSON ไปยัง '{output_filename}' เรียบร้อยแล้ว (ขนาด {len(courses_tree)} รายวิชา, {len(plos_tree)} PLO แม่)")

except Exception as e:
    print(f"❌ เกิดข้อผิดพลาด: {e}")
finally:
    if 'cursor' in locals(): cursor.close()
    if 'conn' in locals() and getattr(conn, 'closed', 0) == 0: conn.close()