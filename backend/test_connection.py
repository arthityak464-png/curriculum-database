import psycopg2

print("กำลังทดสอบการเชื่อมต่อกับฐานข้อมูล mko...")
try:
    # ตั้งค่าการเชื่อมต่อให้ตรงกับที่เราสร้างไว้
    conn = psycopg2.connect(
        dbname="postgres", 
        user="postgres", 
        password="1234", 
        host="localhost", 
        port="5432"
    )
    
    # ถ้าเชื่อมต่อได้ จะแสดงข้อความนี้
    print("✅ ยอดเยี่ยม! VS Code เชื่อมต่อกับฐานข้อมูล mko สำเร็จเรียบร้อยแล้ว!")
    
    # ดึงรายชื่อตารางมาโชว์เพื่อยืนยันอีกรอบ
    cursor = conn.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    tables = cursor.fetchall()
    print(f"พบตารางทั้งหมด {len(tables)} ตาราง ได้แก่: {[t[0] for t in tables]}")
    
    # ปิดการเชื่อมต่อเมื่อใช้งานเสร็จ
    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ การเชื่อมต่อล้มเหลว เกิดข้อผิดพลาด: {e}")