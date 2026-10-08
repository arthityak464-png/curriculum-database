import os
import shutil
import hashlib
import json
import uuid
import traceback
from datetime import datetime, timezone
from typing import Optional, List, Any
from contextlib import asynccontextmanager
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer

from pipeline import inspect_pdf, run_pipeline
from search_utils import rank_candidates, escape_like

MODEL_NAME = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
# ค่า cosine ขั้นต่ำของผลค้นหา (ปรับได้ด้วย env หลังลองกับข้อมูลจริง)
DEFAULT_MIN_SIMILARITY = float(os.getenv("SEARCH_MIN_SIMILARITY", "0.45"))
model = None
jobs = {}

def get_embedding_model():
    global model
    if model is None:
        print(f"🤖 กำลังโหลด AI Model {MODEL_NAME} เข้าสู่ RAM...")
        model = SentenceTransformer(MODEL_NAME)
    return model

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 เริ่มต้นระบบ: กำลังเตรียมความพร้อมของ AI Embedding Model...")
    get_embedding_model()
    print("✅ AI Embedding Model พร้อมใช้งาน!")
    yield
    print("🛑 ปิดการทำงานของเซิร์ฟเวอร์")

app = FastAPI(
    title="Curriculum AI API - มหาวิทยาลัยกาฬสินธุ์",
    description="ระบบแปลงและบริหารจัดการฐานข้อมูลหลักสูตรอัจฉริยะ มคอ.2 (Staging & HITL Verification)",
    version="1.2",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "postgres"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "1234"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )

class CurriculumUpdateSchema(BaseModel):
    curriculum_name_th: Optional[str] = None
    curriculum_name_en: Optional[str] = None
    degree_name_th: Optional[str] = None
    degree_name_en: Optional[str] = None
    faculty: Optional[str] = None
    department: Optional[str] = None
    total_credits: Optional[int] = None
    philosophy: Optional[str] = None
    objectives: Optional[str] = None
    graduate_attributes: Optional[str] = None
    responsible_instructors: Optional[List[Any]] = None

class CourseUpdateSchema(BaseModel):
    course_name_th: Optional[str] = None
    course_name_en: Optional[str] = None
    total_credits: Optional[int] = None
    description_th: Optional[str] = None

def update_job(job_id, **values):
    if job_id in jobs:
        jobs[job_id].update(values, updated_at=datetime.now(timezone.utc).isoformat())

def run_pipeline_job(job_id, pdf_path, force_reload):
    update_job(job_id, status="running", progress=2, message="กำลังเริ่มตรวจสอบไฟล์ PDF")
    try:
        print(f"\n▶️ [Job {job_id}] เริ่มต้น Pipeline สกัดข้อมูล: {pdf_path}")
        validation_info = inspect_pdf(pdf_path)
        update_job(job_id, progress=6, message="ตรวจสอบโครงสร้างไฟล์เรียบร้อย", validation=validation_info)

        shared_model = get_embedding_model()
        run_pipeline(
            pdf_path=pdf_path,
            force_reload=force_reload,
            embedding_model=shared_model,
            progress_callback=lambda progress, message: update_job(
                job_id, progress=progress, message=message
            ),
        )
        update_job(job_id, status="completed", progress=100, message="ประมวลผลเสร็จสมบูรณ์")
        print(f"✅ [Job {job_id}] ประมวลผลสำเร็จครบถ้วน\n")
    except Exception as error:
        traceback.print_exc()
        update_job(job_id, status="failed", progress=100, message=f"ล้มเหลว: {str(error)}", error=str(error))

def generate_curriculum_embeddings_background(curriculum_id: str):
    """
    สร้าง Dense Vector Embeddings (1024 มิติ) ตามข้อกำหนดโมดูล 2:
    ผสาน 'คำอธิบายรายวิชา (Course Descriptions) และข้อความ PLO' เข้าด้วยกัน
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                c.id, 
                c.course_code,
                c.course_name_th, 
                c.course_name_en,
                COALESCE(c.description_th, '') AS description_th,
                COALESCE(
                    string_agg(
                        DISTINCT p.plo_code || ': ' || p.plo_description, 
                        ' ; '
                    ), 
                    ''
                ) AS mapped_plos
            FROM courses c
            LEFT JOIN curriculum_mappings cm ON c.id = cm.course_id
            LEFT JOIN plos p ON cm.plo_id = p.id
            WHERE c.curriculum_id = %s
            GROUP BY c.id, c.course_code, c.course_name_th, c.course_name_en, c.description_th;
        """, (curriculum_id,))
        course_records = cursor.fetchall()

        if course_records:
            print(f"🤖 [Enriched AI Embedding] กำลังสร้าง Vector สำหรับหลักสูตร {curriculum_id} ({len(course_records)} วิชา)...")
            ai_model = get_embedding_model()

            texts_to_embed = []
            for c in course_records:
                parts = [f"รหัสวิชา {c['course_code']} รายวิชา {c['course_name_th']} ({c['course_name_en']})"]
                if c['description_th'].strip():
                    parts.append(f"คำอธิบายรายวิชา: {c['description_th'].strip()}")
                if c['mapped_plos'].strip():
                    parts.append(f"ผลลัพธ์การเรียนรู้และทักษะที่เกี่ยวข้อง: {c['mapped_plos'].strip()}")
                
                full_text = " | ".join(parts)
                texts_to_embed.append(full_text)

            embeddings = ai_model.encode(texts_to_embed, batch_size=32, show_progress_bar=False).tolist()

            update_data = [(emb, c['id']) for c, emb in zip(course_records, embeddings)]
            execute_batch(cursor, "UPDATE courses SET embedding = %s::vector WHERE id = %s;", update_data)
            conn.commit()
            print(f"✅ [Enriched AI Embedding] สร้าง Vector ผสานคำอธิบายวิชา + PLOs ให้หลักสูตร {curriculum_id} สำเร็จครบถ้วน")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ [Enriched AI Embedding Error] {e}")

@app.get("/", tags=["Health Check"])
def read_root():
    return {
        "status": "online",
        "message": "Curriculum AI API with Staging Gatekeeper is running!",
        "model": "BAAI/bge-m3 (1024 dimensions)"
    }

# ========================================================
# 1. จัดการข้อมูลหลักสูตร
# ========================================================
@app.post("/api/v1/curriculums/upload", tags=["Curriculums"])
async def upload_curriculum(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    force: bool = Query(False, description="บังคับประมวลผลใหม่ทั้งหมดแม้เป็นไฟล์ซ้ำ")
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="กรุณาอัปโหลดไฟล์นามสกุล .pdf เท่านั้น")

    upload_dir = os.path.abspath("uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    try:
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        file_hash = hashlib.sha256(content).hexdigest()

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, curriculum_code, verification_status FROM curriculums WHERE file_hash_sha256 = %s;", (file_hash,))
        existing = cursor.fetchone()

        has_courses = False
        if existing:
            cursor.execute("SELECT COUNT(*) AS cnt FROM courses WHERE curriculum_id = %s;", (existing["id"],))
            cnt_row = cursor.fetchone()
            has_courses = (cnt_row["cnt"] > 0) if cnt_row else False

        cursor.close()
        conn.close()

        if existing and has_courses and not force:
            job_id = str(uuid.uuid4())
            jobs[job_id] = {
                "job_id": job_id,
                "status": "completed",
                "progress": 100,
                "message": "เอกสารนี้อยู่ในระบบแล้วและมีข้อมูลครบถ้วน",
                "filename": file.filename,
                "file_hash_sha256": file_hash,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            return {
                "status": "already_exists",
                "job_id": job_id,
                "curriculum_id": str(existing["id"]),
                "curriculum_code": existing["curriculum_code"],
                "verification_status": existing.get("verification_status") or "STAGED",
                "filename": file.filename,
                "file_hash_sha256": file_hash,
                "message": "เอกสารนี้อยู่ในระบบแล้ว กำลังเปิดข้อมูลให้ตรวจทาน"
            }

        effective_force = force or (existing is not None and not has_courses)
        job_id = str(uuid.uuid4())
        jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0,
            "message": "นำเข้าไฟล์เข้าสู่คิวงานเรียบร้อย",
            "filename": file.filename,
            "file_hash_sha256": file_hash,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        background_tasks.add_task(run_pipeline_job, job_id, file_path, effective_force)

        return {
            "status": "staged",
            "job_id": job_id,
            "filename": file.filename,
            "file_path": file_path,
            "file_hash_sha256": file_hash,
            "message": "อัปโหลดเอกสารสำเร็จ ข้อมูลถูกส่งเข้าประมวลผลเรียบร้อย"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการอัปโหลดไฟล์: {str(e)}")

@app.get("/api/v1/jobs/{job_id}", tags=["Pipeline"])
def get_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="ไม่พบงานประมวลผลตาม ID ที่ระบุ")
    return job

@app.get("/api/v1/curriculums", tags=["Curriculums"])
def get_curriculums():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT 
                id::text AS id, 
                curriculum_code AS code, 
                curriculum_name_th AS name,
                degree_name_th AS degree,
                total_credits,
                faculty,
                department,
                COALESCE(verification_status, 'STAGED') AS verification_status,
                file_hash_sha256,
                updated_at
            FROM curriculums
            ORDER BY updated_at DESC;
        """)
        rows = cursor.fetchall()
        return {"data": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/v1/curriculums/{id}", tags=["Curriculums"])
def get_curriculum_detail(id: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT 
                id::text AS id,
                curriculum_code,
                curriculum_name_th,
                curriculum_name_en,
                degree_name_th,
                degree_name_en,
                faculty,
                department,
                total_credits,
                philosophy,
                objectives,
                graduate_attributes,
                responsible_instructors,
                COALESCE(verification_status, 'STAGED') AS verification_status,
                file_hash_sha256,
                created_at,
                updated_at
            FROM curriculums 
            WHERE id = %s;
        """, (id,))
        curriculum = cursor.fetchone()
        if not curriculum:
            raise HTTPException(status_code=404, detail="ไม่พบข้อมูลหลักสูตรตาม ID ที่ระบุ")
        return curriculum
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/v1/curriculums/{id}/pdf", tags=["Curriculums"])
def get_curriculum_pdf(id: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT file_path, curriculum_code FROM curriculums WHERE id = %s;", (id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="ไม่พบหลักสูตรตาม ID ที่ระบุ")

        raw_path = row.get("file_path")
        filename = os.path.basename(raw_path) if raw_path else ""

        candidate_paths = [
            raw_path,
            os.path.join("uploads", filename) if filename else None,
            os.path.join("backend", "uploads", filename) if filename else None,
            os.path.join(os.path.dirname(__file__), "uploads", filename) if filename else None,
            filename if filename else None,
        ]

        target_file = None
        for p in candidate_paths:
            if p and os.path.exists(p):
                target_file = p
                break

        if not target_file:
            for root, _, files in os.walk("."):
                for f in files:
                    if filename and f.lower() == filename.lower():
                        target_file = os.path.join(root, f)
                        break
                if target_file:
                    break

        if not target_file or not os.path.exists(target_file):
            raise HTTPException(status_code=404, detail="ไม่พบไฟล์เอกสาร PDF บนเซิร์ฟเวอร์")

        return FileResponse(
            path=target_file,
            media_type="application/pdf",
            content_disposition_type="inline"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.put("/api/v1/curriculums/{id}", tags=["Curriculums"])
def update_curriculum(id: str, payload: CurriculumUpdateSchema):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        instructors_json = json.dumps(payload.responsible_instructors, ensure_ascii=False) if payload.responsible_instructors is not None else None

        cursor.execute("""
            UPDATE curriculums
            SET 
                curriculum_name_th = COALESCE(%s, curriculum_name_th),
                curriculum_name_en = COALESCE(%s, curriculum_name_en),
                degree_name_th = COALESCE(%s, degree_name_th),
                degree_name_en = COALESCE(%s, degree_name_en),
                faculty = COALESCE(%s, faculty),
                department = COALESCE(%s, department),
                total_credits = COALESCE(%s, total_credits),
                philosophy = COALESCE(%s, philosophy),
                objectives = COALESCE(%s, objectives),
                graduate_attributes = COALESCE(%s, graduate_attributes),
                responsible_instructors = COALESCE(%s::jsonb, responsible_instructors),
                updated_at = NOW()
            WHERE id = %s
            RETURNING id::text AS id, curriculum_code, curriculum_name_th, updated_at;
        """, (
            payload.curriculum_name_th, payload.curriculum_name_en,
            payload.degree_name_th, payload.degree_name_en,
            payload.faculty, payload.department, payload.total_credits,
            payload.philosophy, payload.objectives, payload.graduate_attributes,
            instructors_json,
            id
        ))
        updated = cursor.fetchone()
        if not updated:
            raise HTTPException(status_code=404, detail="ไม่พบหลักสูตรที่ต้องการแก้ไข")
            
        conn.commit()
        return {
            "status": "success",
            "message": "บันทึกการแก้ไขข้อมูลเรียบร้อยแล้ว",
            "data": updated
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.put("/api/v1/curriculums/{id}/verify", tags=["Curriculums"])
@app.post("/api/v1/curriculums/{id}/commit", tags=["Curriculums"])
def commit_curriculum(id: str, background_tasks: BackgroundTasks):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE curriculums 
            SET verification_status = 'VERIFIED',
                updated_at = NOW()
            WHERE id = %s;
        """, (id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="ไม่พบข้อมูลหลักสูตรตาม ID ที่ระบุ")
            
        conn.commit()
        background_tasks.add_task(generate_curriculum_embeddings_background, id)

        return {
            "curriculum_id": id,
            "verification_status": "VERIFIED",
            "message": "อนุมัติข้อมูลสำเร็จ! หลักสูตรได้รับการบันทึกเข้าสู่ฐานข้อมูลหลักอย่างเป็นทางการ"
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/api/v1/curriculums/{id}/embeddings/reindex", tags=["Curriculums"])
def reindex_curriculum_embeddings(id: str, background_tasks: BackgroundTasks):
    """สั่งสร้าง Vector Embedding ใหม่ทันที โดยรวมข้อความคำอธิบายรายวิชาและ PLOs เข้าด้วยกัน"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM curriculums WHERE id = %s;", (id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="ไม่พบหลักสูตรตาม ID ที่ระบุ")
    
    cursor.close()
    conn.close()
    
    background_tasks.add_task(generate_curriculum_embeddings_background, id)
    return {
        "status": "queued",
        "message": f"เริ่มกระบวนการสร้าง Enriched Vector Embedding สำหรับหลักสูตร {id} เรียบร้อย"
    }

@app.delete("/api/v1/curriculums/{id}", tags=["Curriculums"])
@app.post("/api/v1/curriculums/{id}/delete", tags=["Curriculums"])
def delete_curriculum(id: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT id, file_path, curriculum_code FROM curriculums WHERE id = %s;", (id,))
        curr = cursor.fetchone()
        if not curr:
            raise HTTPException(status_code=404, detail="ไม่พบข้อมูลหลักสูตรที่ต้องการลบ")

        cursor.execute("DELETE FROM curriculum_mappings WHERE course_id IN (SELECT id FROM courses WHERE curriculum_id = %s);", (id,))
        cursor.execute("DELETE FROM course_prerequisites WHERE course_id IN (SELECT id FROM courses WHERE curriculum_id = %s);", (id,))
        cursor.execute("DELETE FROM courses WHERE curriculum_id = %s;", (id,))
        
        cursor.execute("UPDATE plos SET parent_plo_id = NULL WHERE curriculum_id = %s;", (id,))
        cursor.execute("DELETE FROM plos WHERE curriculum_id = %s;", (id,))
        
        cursor.execute("DELETE FROM curriculums WHERE id = %s;", (id,))
        conn.commit()

        file_path = curr.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

        return {
            "status": "success",
            "message": f"ลบหลักสูตร {curr['curriculum_code']} เรียบร้อยแล้ว"
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ========================================================
# 2. ค้นหารายวิชาด้วย AI (Hybrid Search Engine)
# ========================================================
@app.get("/api/v1/courses/search", tags=["Semantic Search"])
def search_courses(
    query: str,
    limit: int = Query(10, ge=1, le=50),
    curriculum_id: Optional[str] = Query(None, description="จำกัดเฉพาะหลักสูตรนี้"),
    course_group: Optional[str] = Query(None, description="จำกัดเฉพาะหมวดวิชานี้"),
    min_score: float = Query(DEFAULT_MIN_SIMILARITY, ge=0.0, le=1.0, description="ค่า cosine similarity ขั้นต่ำ"),
):
    """
    Hybrid Search: ดึงผู้สมัครจาก Vector (HNSW) + Keyword แล้วจัดอันดับรวมใน search_utils.rank_candidates
    คะแนนที่คืนเป็นค่าจริงจาก cosine similarity ไม่มีการยืดหรือบีบตัวเลข
    """
    query_clean = (query or "").strip()
    if not query_clean:
        raise HTTPException(status_code=400, detail="กรุณาระบุคำค้นหา")

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT COUNT(*) AS n FROM curriculums WHERE verification_status = 'VERIFIED';")
        verified_curricula = cursor.fetchone()["n"]
        cursor.execute("""
            SELECT COUNT(*) AS n FROM courses c
            JOIN curriculums cu ON cu.id = c.curriculum_id
            WHERE cu.verification_status = 'VERIFIED' AND c.embedding IS NOT NULL;
        """)
        indexed_courses = cursor.fetchone()["n"]

        meta = {
            "search_query": query_clean,
            "search_type": "Hybrid Search (Vector bge-m3 + Keyword)",
            "min_score": min_score,
            "verified_curricula": verified_curricula,
            "indexed_courses": indexed_courses,
        }
        if indexed_courses == 0:
            return {**meta, "total_found": 0, "results": []}

        query_embedding = get_embedding_model().encode(query_clean, normalize_embeddings=True).tolist()

        where = ["cu.verification_status = 'VERIFIED'", "c.embedding IS NOT NULL"]
        params = {
            "emb": query_embedding,
            "like": f"%{escape_like(query_clean)}%",
            "pool": max(limit * 5, 40),
        }
        if curriculum_id:
            where.append("cu.id::text = %(curriculum_id)s")
            params["curriculum_id"] = curriculum_id
        if course_group:
            where.append("c.course_group = %(course_group)s")
            params["course_group"] = course_group
        where_sql = " AND ".join(where)

        cursor.execute(f"""
            WITH vec AS (
                SELECT c.id
                FROM courses c JOIN curriculums cu ON cu.id = c.curriculum_id
                WHERE {where_sql}
                ORDER BY c.embedding <=> %(emb)s::vector
                LIMIT %(pool)s
            ),
            kw AS (
                SELECT c.id
                FROM courses c JOIN curriculums cu ON cu.id = c.curriculum_id
                WHERE {where_sql}
                  AND (c.course_code ILIKE %(like)s OR c.course_name_th ILIKE %(like)s
                       OR c.course_name_en ILIKE %(like)s OR c.description_th ILIKE %(like)s)
                LIMIT %(pool)s
            ),
            cand AS (SELECT id FROM vec UNION SELECT id FROM kw)
            SELECT
                c.id::text AS id,
                c.course_code, c.course_name_th, c.course_name_en,
                c.description_th, c.description_en,
                c.total_credits, c.credit_lecture, c.credit_lab, c.credit_self,
                c.course_group, c.study_year, c.study_semester,
                cu.id::text AS curriculum_id,
                cu.curriculum_code, cu.curriculum_name_th, cu.department,
                1 - (c.embedding <=> %(emb)s::vector) AS similarity
            FROM cand
            JOIN courses c ON c.id = cand.id
            JOIN curriculums cu ON cu.id = c.curriculum_id;
        """, params)
        candidates = [dict(r) for r in cursor.fetchall()]
        results = rank_candidates(candidates, query_clean, min_score, limit)

        # แนบ PLO ที่วิชานั้นรับผิดชอบ + PLO ที่ความหมายใกล้คำค้นที่สุด (อธิบายว่าทำไมวิชานี้ถูกเลือก)
        if results:
            cursor.execute("""
                SELECT cm.course_id::text AS course_id, p.plo_code, p.plo_description,
                       cm.responsibility_type,
                       CASE WHEN p.embedding IS NULL THEN NULL
                            ELSE 1 - (p.embedding <=> %(emb)s::vector) END AS similarity
                FROM curriculum_mappings cm
                JOIN plos p ON p.id = cm.plo_id
                WHERE cm.course_id::text = ANY(%(ids)s);
            """, {"emb": query_embedding, "ids": [r["id"] for r in results]})
            plos_by_course = {}
            for row in cursor.fetchall():
                plos_by_course.setdefault(row["course_id"], []).append(row)
            for item in results:
                plos = plos_by_course.get(item["id"], [])
                codes = sorted({p["plo_code"] for p in plos})
                item["plo_codes"] = codes
                item["matched_plos"] = ", ".join(codes)  # คงไว้เพื่อความเข้ากันได้กับ frontend เดิม
                scored = sorted(
                    (p for p in plos if p["similarity"] is not None),
                    key=lambda p: p["similarity"], reverse=True,
                )
                item["related_plos"] = [
                    {
                        "plo_code": p["plo_code"],
                        "plo_description": p["plo_description"],
                        "responsibility_type": p["responsibility_type"],
                        "similarity": round(float(p["similarity"]), 4),
                    }
                    for p in scored[:2]
                ]

        return {**meta, "total_found": len(results), "results": results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/v1/curriculums/{id}/courses", tags=["Courses"])
def get_curriculum_courses(id: str, course_group: Optional[str] = Query(None)):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT p.course_id::text AS course_id, p.prerequisite_course_code
            FROM course_prerequisites p
            JOIN courses c ON p.course_id = c.id
            WHERE c.curriculum_id = %s;
        """, (id,))
        prereqs = {}
        for r in cursor.fetchall():
            prereqs.setdefault(r["course_id"], []).append(r["prerequisite_course_code"])

        query = """
            SELECT 
                id::text AS id,
                course_code,
                course_name_th,
                course_name_en,
                credit_lecture,
                credit_lab,
                credit_self,
                total_credits,
                course_group,
                study_year,
                study_semester,
                description_th,
                description_en
            FROM courses
            WHERE curriculum_id = %s
        """
        params = [id]
        if course_group:
            query += " AND course_group = %s"
            params.append(course_group)
        query += " ORDER BY course_code ASC;"

        cursor.execute(query, tuple(params))
        courses = cursor.fetchall()
        for c in courses:
            c["prerequisites"] = prereqs.get(c["id"], [])

        return {
            "curriculum_id": id,
            "total_courses": len(courses),
            "data": courses
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/v1/courses/{course_code}", tags=["Courses"])
def get_course_detail(course_code: str, curriculum_id: Optional[str] = Query(None)):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        query = "SELECT * FROM courses WHERE course_code = %s"
        params = [course_code]
        if curriculum_id:
            query += " AND curriculum_id = %s"
            params.append(curriculum_id)

        cursor.execute(query, tuple(params))
        course = cursor.fetchone()
        if not course:
            raise HTTPException(status_code=404, detail=f"ไม่พบรายวิชา {course_code}")

        cursor.execute("""
            SELECT prerequisite_course_code 
            FROM course_prerequisites 
            WHERE course_id = %s;
        """, (course["id"],))
        course["prerequisites"] = [r["prerequisite_course_code"] for r in cursor.fetchall()]

        cursor.execute("""
            SELECT p.plo_code, cm.responsibility_type
            FROM curriculum_mappings cm
            JOIN plos p ON cm.plo_id = p.id
            WHERE cm.course_id = %s
            ORDER BY p.plo_code;
        """, (course["id"],))
        course["mappings"] = cursor.fetchall()

        course.pop("embedding", None)
        course["id"] = str(course["id"])
        course["curriculum_id"] = str(course["curriculum_id"])
        return course
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.put("/api/v1/courses/{course_code}", tags=["Courses"])
def update_course(course_code: str, payload: CourseUpdateSchema, curriculum_id: Optional[str] = Query(None)):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        query = "SELECT id, course_name_th, description_th FROM courses WHERE course_code = %s"
        params = [course_code]
        if curriculum_id:
            query += " AND curriculum_id = %s"
            params.append(curriculum_id)
            
        cursor.execute(query, tuple(params))
        course = cursor.fetchone()
        if not course:
            raise HTTPException(status_code=404, detail=f"ไม่พบรายวิชา {course_code}")

        cursor.execute("""
            UPDATE courses
            SET 
                course_name_th = COALESCE(%s, course_name_th),
                course_name_en = COALESCE(%s, course_name_en),
                total_credits = COALESCE(%s, total_credits),
                description_th = COALESCE(%s, description_th),
                updated_at = NOW()
            WHERE id = %s
            RETURNING id::text AS id, course_code, course_name_th, description_th;
        """, (
            payload.course_name_th, payload.course_name_en,
            payload.total_credits, payload.description_th,
            course["id"]
        ))
        updated_course = cursor.fetchone()

        if payload.description_th:
            content_to_embed = f"{updated_course['course_name_th']}: {payload.description_th}"
            new_emb = get_embedding_model().encode(content_to_embed).tolist()
            cursor.execute("UPDATE courses SET embedding = %s::vector WHERE id = %s;", (new_emb, course["id"]))

        conn.commit()
        return {
            "status": "success",
            "message": f"แก้ไขรายวิชา {course_code} สำเร็จ",
            "data": updated_course
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ========================================================
# 3. ผลลัพธ์การเรียนรู้และเมทริกซ์ (PLO & Matrix)
# ========================================================
@app.get("/api/v1/curriculums/{id}/plos", tags=["Curriculum Mappings"])
def get_curriculum_plos(id: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT 
                id::text AS id,
                parent_plo_id::text AS parent_plo_id,
                plo_code,
                plo_description,
                CASE WHEN parent_plo_id IS NULL THEN TRUE ELSE FALSE END AS is_main_plo
            FROM plos
            WHERE curriculum_id = %s
            ORDER BY 
                CASE 
                    WHEN plo_code ~ '^[0-9]+\.[0-9]+$' THEN split_part(plo_code, '.', 1)::int * 100 + split_part(plo_code, '.', 2)::int
                    WHEN plo_code ~ '^PLO[0-9]+$' THEN substring(plo_code from 4)::int
                    WHEN plo_code ~ '^[0-9]+$' THEN plo_code::int
                    ELSE 9999
                END ASC,
                LENGTH(plo_code) ASC,
                plo_code ASC;
        """, (id,))
        rows = cursor.fetchall()
        
        main_list = [r for r in rows if r["is_main_plo"]]
        sub_list = [r for r in rows if not r["is_main_plo"]]
        
        effective_subs = sub_list if len(sub_list) > 0 else main_list

        return {
            "curriculum_id": id,
            "total_plos": len(main_list),
            "total_sub_plos": len(effective_subs),
            "has_sub_plos": len(sub_list) > 0,
            "main_plos": main_list,
            "sub_plos": effective_subs,
            "display_plos": effective_subs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/v1/curriculums/{id}/mapping", tags=["Curriculum Mappings"])
def get_mapping(id: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT id::text AS id, course_code, course_name_th
            FROM courses
            WHERE curriculum_id = %s
            ORDER BY course_code ASC;
        """, (id,))
        courses = cursor.fetchall()

        cursor.execute("""
            SELECT 
                cm.course_id::text AS course_id,
                p.plo_code,
                p.plo_description,
                p.parent_plo_id::text AS parent_plo_id,
                cm.responsibility_type
            FROM curriculum_mappings cm
            JOIN plos p ON cm.plo_id = p.id
            JOIN courses c ON cm.course_id = c.id
            WHERE c.curriculum_id = %s
            ORDER BY 
                CASE 
                    WHEN p.plo_code ~ '^[0-9]+\.[0-9]+$' THEN split_part(p.plo_code, '.', 1)::int * 100 + split_part(p.plo_code, '.', 2)::int
                    WHEN p.plo_code ~ '^PLO[0-9]+$' THEN substring(p.plo_code from 4)::int
                    WHEN p.plo_code ~ '^[0-9]+$' THEN p.plo_code::int
                    ELSE 9999
                END ASC,
                LENGTH(p.plo_code), p.plo_code;
        """, (id,))
        mapping_rows = cursor.fetchall()

        mapping_by_course = {}
        for m in mapping_rows:
            mapping_by_course.setdefault(m["course_id"], []).append({
                "plo_code": m["plo_code"],
                "parent_plo_id": m["parent_plo_id"],
                "responsibility_type": m["responsibility_type"]
            })

        matrix_result = []
        for c in courses:
            matrix_result.append({
                "course_code": c["course_code"],
                "course_name_th": c["course_name_th"],
                "mappings": mapping_by_course.get(c["id"], [])
            })

        return {
            "curriculum_id": id,
            "total_mapping_points": len(mapping_rows),
            "data": matrix_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/v1/curriculums/{id}/export/json", tags=["Curriculums"])
def export_curriculum_json(id: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM curriculums WHERE id = %s;", (id,))
        curriculum = cursor.fetchone()
        if not curriculum:
            raise HTTPException(status_code=404, detail="ไม่พบหลักสูตรตาม ID ที่ระบุ")

        cursor.execute("""
            SELECT 
                p.course_id::text AS course_id,
                p.prerequisite_course_code
            FROM course_prerequisites p
            JOIN courses c ON p.course_id = c.id
            WHERE c.curriculum_id = %s;
        """, (id,))
        prereqs_rows = cursor.fetchall()
        
        prereqs_map = {}
        for pr in prereqs_rows:
            cid = pr["course_id"]
            prereqs_map.setdefault(cid, []).append({
                "prerequisite_course_code": pr["prerequisite_course_code"]
            })

        cursor.execute("""
            SELECT 
                id::text AS id,
                course_code, 
                course_name_th, 
                course_name_en, 
                credit_lecture,
                credit_lab,
                credit_self,
                total_credits, 
                course_group, 
                description_th,
                description_en
            FROM courses 
            WHERE curriculum_id = %s 
            ORDER BY course_code;
        """, (id,))
        courses = cursor.fetchall()

        for c in courses:
            c["prerequisites"] = prereqs_map.get(c["id"], [])
            del c["id"]

        cursor.execute("""
            SELECT 
                plo_code, 
                plo_description, 
                parent_plo_id::text AS parent_plo_id
            FROM plos 
            WHERE curriculum_id = %s 
            ORDER BY 
                CASE 
                    WHEN plo_code ~ '^[0-9]+\.[0-9]+$' THEN split_part(plo_code, '.', 1)::int * 100 + split_part(plo_code, '.', 2)::int
                    ELSE 9999
                END ASC,
                LENGTH(plo_code), plo_code;
        """, (id,))
        plos = cursor.fetchall()

        return {
            "metadata": {
                "curriculum_code": curriculum["curriculum_code"],
                "curriculum_name_th": curriculum["curriculum_name_th"],
                "curriculum_name_en": curriculum["curriculum_name_en"],
                "degree_name_th": curriculum["degree_name_th"],
                "degree_name_en": curriculum["degree_name_en"],
                "total_credits": curriculum["total_credits"],
                "faculty": curriculum.get("faculty"),
                "department": curriculum.get("department"),
                "philosophy": curriculum.get("philosophy"),
                "objectives": curriculum.get("objectives"),
                "graduate_attributes": curriculum.get("graduate_attributes"),
                "instructors": curriculum.get("responsible_instructors"),
                "verification_status": curriculum.get("verification_status") or "STAGED",
                "sha256_hash": curriculum.get("file_hash_sha256")
            },
            "program_learning_outcomes": plos,
            "courses_catalog": courses
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()