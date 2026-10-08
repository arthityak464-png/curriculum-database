import psycopg2
from sentence_transformers import SentenceTransformer

# 1. โหลดโมเดล BAAI/bge-m3 (จะดึงจากแคชในเครื่องทันที)
print("🤖 กำลังโหลดโมเดล...")
model = SentenceTransformer('BAAI/bge-m3')

# 2. ระบุประโยคที่ต้องการค้นหา (ลองเปลี่ยนประโยคนี้ได้ตามต้องการ)
query = "IOT"
print(f"🔍 คำค้นหา: \"{query}\"")

# 3. แปลงคำค้นหาเป็น Dense Vector (1024 มิติ)
query_embedding = model.encode(query).tolist()

# 4. เชื่อมต่อไปยัง PostgreSQL
conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="1234",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# 5. ค้นหารายวิชาที่ใกล้เคียงที่สุดด้วย Cosine Distance (<=>)
# สูตรแปลงเป็น Similarity Score (0 - 100%): 1 - (embedding <=> query_vector)
sql = """
    SELECT 
        course_code, 
        course_name_th, 
        ROUND(((1 - (embedding <=> %s::vector)) * 100)::numeric, 2) AS similarity,
        SUBSTRING(description_th, 1, 100) AS desc_snippet
    FROM courses
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> %s::vector ASC
    LIMIT 5;
"""

cursor.execute(sql, (query_embedding, query_embedding))
results = cursor.fetchall()

print("\n🎯 ผลลัพธ์ 5 รายวิชาที่ความหมายตรงกับคำค้นหาที่สุด:")
print("=" * 70)
for rank, (code, name, sim, snippet) in enumerate(results, 1):
    print(f"#{rank} [{code}] {name}  (ความตรงกัน: {sim}%)")
    print(f"   เนื้อหาโดยย่อ: {snippet}...")
    print("-" * 70)

cursor.close()
conn.close()