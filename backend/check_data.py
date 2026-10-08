import psycopg2

conn = psycopg2.connect(dbname="postgres", user="postgres", password="1234", host="localhost", port="5432")
cursor = conn.cursor()

print("=" * 60)
print("📊 สรุปข้อมูลที่ถูกสกัดเข้าฐานข้อมูลล่าสุด")
print("=" * 60)

# 1. ตรวจสอบหลักสูตร
cursor.execute("SELECT curriculum_code, curriculum_name_th, total_credits, faculty, department FROM curriculums;")
for row in cursor.fetchall():
    print(f"📌 หลักสูตร: {row[0]} | {row[1]}")
    print(f"   คณะ/สาขา: {row[3]} / {row[4]}")
    print(f"   หน่วยกิตรวม: {row[2]} หน่วยกิต\n")

# 2. ตรวจสอบจำนวนรายวิชา
cursor.execute("SELECT COUNT(*), COUNT(description_th) FROM courses;")
total_c, total_desc = cursor.fetchone()
print(f"📚 รายวิชาทั้งหมด: {total_c} วิชา (มีคำอธิบายวิชา: {total_desc} วิชา)")

# 3. ตรวจสอบ PLO (ต้องได้ 1A-5D)
cursor.execute("SELECT plo_code FROM plos WHERE parent_plo_id IS NOT NULL ORDER BY plo_code;")
plo_codes = [r[0] for r in cursor.fetchall()]
print(f"🎯 Sub-PLOs ({len(plo_codes)} ข้อ): {', '.join(plo_codes)}")

# 4. ตรวจสอบจุด Mapping ทั้งหมด และตรวจวิชา SC
cursor.execute("SELECT COUNT(*) FROM curriculum_mappings;")
total_maps = cursor.fetchone()[0]
print(f"🔗 จุด Mapping ทั้งหมด: {total_maps} จุด")

cursor.execute("""
    SELECT c.course_code, c.course_name_th, p.plo_code, cm.responsibility_type 
    FROM curriculum_mappings cm
    JOIN courses c ON cm.course_id = c.id
    JOIN plos p ON cm.plo_id = p.id
    WHERE c.course_code LIKE 'SC%'
    ORDER BY c.course_code, p.plo_code;
""")
sc_maps = cursor.fetchall()
print(f"\n🔬 จุด Mapping ของวิชาหมวดวิทยาศาสตร์ (SC): พบ {len(sc_maps)} จุด")
for m in sc_maps:
    print(f"   - {m[0]} {m[1]} -> [{m[2]}] ({m[3]})")

print("=" * 60)
cursor.close()
conn.close()