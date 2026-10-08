import psycopg2

print("กำลังสร้างตารางในฐานข้อมูล mko...")
try:
    # เชื่อมต่อฐานข้อมูล
    conn = psycopg2.connect(
        dbname="postgres", user="postgres", password="1234", host="localhost", port="5432"
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # อ่านคำสั่ง SQL จากไฟล์ init.sql ของเรามารัน
    with open('init.sql', 'r', encoding='utf-8') as file:
        sql_commands = file.read()
        
    cursor.execute(sql_commands)
    print("✅ สร้างโครงสร้างตารางทั้ง 5 และระบบ Extension สำเร็จเรียบร้อยแล้ว!")
    
except Exception as e:
    print(f"❌ เกิดข้อผิดพลาด: {e}")
finally:
    if 'cursor' in locals(): cursor.close()
    if 'conn' in locals(): conn.close()