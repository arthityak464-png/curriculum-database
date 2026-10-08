import psycopg2
from sentence_transformers import SentenceTransformer
import sys

print("🤖 กำลังโหลด AI Model 'BAAI/bge-m3'...")
model = SentenceTransformer('BAAI/bge-m3')

try:
    print("🔌 กำลังเชื่อมต่อฐานข้อมูล...")
    # ตั้งค่าพอร์ตเป็น 5433 ตามที่ Docker ของคุณรันอยู่ล่าสุด
    conn = psycopg2.connect(dbname="postgres", user="postgres", password="1234", host="localhost", port="5432")
    cursor = conn.cursor()
    
    # เช็กการเปิดใช้งาน Vector และเพิ่มคอลัมน์ embedding ในตาราง plos
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cursor.execute("ALTER TABLE plos ADD COLUMN IF NOT EXISTS embedding vector(1024);")
    conn.commit()
    
    # ดึงข้อมูล PLO ทั้งหมด
    cursor.execute("SELECT id, plo_code, plo_description FROM plos WHERE plo_description IS NOT NULL;")
    plos = cursor.fetchall()
    
    if not plos:
        print("⚠️ ไม่พบข้อมูล PLO เลย! (คุณอาจจะยังไม่ได้รันไฟล์ extract_plos.py)")
        sys.exit()
        
    print(f"🔍 พบข้อมูล PLO ทั้งหมด {len(plos)} ข้อ กำลังแปลงเป็น Vector...")
    
    update_count = 0
    for plo_id, code, desc in plos:
        text_to_encode = f"[{code}] {desc}"
        embedding = model.encode(text_to_encode).tolist()
        
        cursor.execute("""
            UPDATE plos 
            SET embedding = %s::vector 
            WHERE id = %s;
        """, (embedding, plo_id))
        
        update_count += 1
            
    conn.commit()
    print(f"🎉 สำเร็จ! แปลงและบันทึก Vector Embeddings สำหรับ PLO เรียบร้อยแล้วจำนวน {update_count} รายการ")

except Exception as e:
    print(f"❌ เกิดข้อผิดพลาด: {e}")
    if 'conn' in locals(): conn.rollback()
finally:
    if 'cursor' in locals(): cursor.close()
    if 'conn' in locals() and getattr(conn, 'closed', 0) == 0: conn.close()