import psycopg2

print("🧹 กำลังล้างข้อมูลทั้งหมดในฐานข้อมูล...")

try:
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432"
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # ล้างข้อมูลตารางหลักแบบ CASCADE (ตารางลูกทั้งหมดจะถูกล้างทิ้งไปด้วยทันที)
    cursor.execute("""
        TRUNCATE TABLE 
            curriculums, 
            courses, 
            plos, 
            course_prerequisites, 
            curriculum_mappings 
        CASCADE;
    """)

    print("✅ สำเร็จ! ฐานข้อมูลว่างเปล่าเรียบร้อยแล้ว (โครงสร้างตารางยังอยู่ครบ)")

except Exception as e:
    print(f"❌ เกิดข้อผิดพลาด: {e}")
finally:
    if 'cursor' in locals(): cursor.close()
    if 'conn' in locals(): conn.close()