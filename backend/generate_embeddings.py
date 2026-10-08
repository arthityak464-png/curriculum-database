import psycopg2
from sentence_transformers import SentenceTransformer
import sys

print("🤖 กำลังโหลด AI Model 'BAAI/bge-m3' (ครั้งแรกอาจใช้เวลาดาวน์โหลดสักครู่)...")
model = SentenceTransformer('BAAI/bge-m3')

try:
    print("🔌 กำลังเชื่อมต่อฐานข้อมูล...")
    # แก้ host เป็น localhost ให้ตรงกับไฟล์อื่นๆ
    conn = psycopg2.connect(dbname="postgres", user="postgres", password="1234", host="localhost", port="5432")
    cursor = conn.cursor()
    
    # เพิ่มคำสั่งบังคับเปิดใช้งาน Vector เพื่อป้องกัน Error "type vector does not exist"
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()
    print("✅ ตรวจสอบและเปิดใช้งานระบบ Vector สำเร็จ")
    
    cursor.execute("SELECT id, course_code, course_name_th, description_th FROM courses WHERE description_th IS NOT NULL;")
    courses = cursor.fetchall()
    
    if not courses:
        print("⚠️ ไม่พบข้อมูลวิชาเลย! กรุณารันไฟล์สกัดข้อมูลเข้าตาราง courses ก่อน")
        sys.exit()
        
    print(f"🔍 พบรายวิชาที่มีคำอธิบายทั้งหมด {len(courses)} วิชา กำลังแปลงเป็น Vector Embeddings...")
    
    update_count = 0
    for course_id, code, name, desc in courses:
        text_to_encode = f"วิชา: {name} ({code}) คำอธิบาย: {desc}"
        embedding = model.encode(text_to_encode).tolist()
        
        cursor.execute("""
            UPDATE courses 
            SET embedding = %s::vector 
            WHERE id = %s;
        """, (embedding, course_id))
        
        update_count += 1
        if update_count % 10 == 0:
            print(f"   ⏳ แปลงเสร็จแล้ว {update_count}/{len(courses)} วิชา...")
            
    conn.commit()
    print(f"🎉 สำเร็จ! แปลงและบันทึก Vector Embeddings เรียบร้อยแล้วจำนวน {update_count} รายการ")

except Exception as e:
    print(f"❌ เกิดข้อผิดพลาด: {e}")
    if 'conn' in locals(): conn.rollback()
finally:
    if 'cursor' in locals(): cursor.close()
    if 'conn' in locals() and getattr(conn, 'closed', 0) == 0: conn.close()