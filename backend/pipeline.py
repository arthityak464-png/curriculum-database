import os
import re
import sys
import json
import hashlib
import tempfile
import difflib
import unicodedata
from typing import Callable, Optional, Dict, Any, List
import psycopg2
from psycopg2.extras import execute_batch
import pdfplumber
from sentence_transformers import SentenceTransformer

# ==========================================
# 1. การตั้งค่าระบบ (Configuration)
# ==========================================
DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "postgres"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "1234"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432")
}

DEFAULT_FILENAME = "วศ.บ. (วิศวกรรมคอมพิวเตอร์)-ปรับปรุง พ.ศ. 2566.pdf"
DEFAULT_PDF = os.path.join("uploads", DEFAULT_FILENAME)
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
_CACHED_MODEL = None

def get_default_model():
    global _CACHED_MODEL
    if _CACHED_MODEL is None:
        print(f"🤖 [Pipeline] โหลด AI Model {MODEL_NAME} เข้าสู่ RAM...")
        _CACHED_MODEL = SentenceTransformer(MODEL_NAME)
    return _CACHED_MODEL

def calculate_file_hash(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def resolve_pdf_path(pdf_path):
    if os.path.isabs(pdf_path) and os.path.exists(pdf_path):
        return pdf_path

    candidates = [
        pdf_path,
        os.path.abspath(pdf_path),
        os.path.join("uploads", os.path.basename(pdf_path)),
        os.path.join("backend", "uploads", os.path.basename(pdf_path)),
        os.path.join(os.path.dirname(__file__), "uploads", os.path.basename(pdf_path)),
        os.path.join(os.path.dirname(__file__), os.path.basename(pdf_path)),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return os.path.abspath(c)
    return pdf_path

def inspect_pdf(pdf_path):
    resolved = resolve_pdf_path(pdf_path)
    if not os.path.exists(resolved):
        raise FileNotFoundError(f"ไม่พบไฟล์ PDF บนเซิร์ฟเวอร์: {pdf_path}")

    try:
        with pdfplumber.open(resolved) as pdf:
            page_count = len(pdf.pages)
            sample_indices = [0, min(3, page_count - 1), min(8, page_count - 1), min(15, page_count - 1)]
            sample_pages = [pdf.pages[i] for i in set(sample_indices)]
            has_text = any((p.extract_text(layout=False) or "").strip() for p in sample_pages)

        return {
            "page_count": page_count,
            "text_pages": page_count if has_text else 0,
            "table_pages": 0,
            "is_scanned": not has_text,
            "has_extractable_text": has_text,
        }
    except Exception as e:
        return {
            "page_count": 0, "text_pages": 0, "table_pages": 0,
            "is_scanned": False, "has_extractable_text": True, "error": str(e)
        }

def clean_text(t):
    return re.sub(r'\s+', ' ', t or '').strip()

def normalize_pdf_thai_text(text, preserve_newlines=False):
    if not text:
        return ""

    text = text.replace("(:127)", "ิ").replace("\x7f", "ิ")
    text = text.replace("ฟ(:127)สิกส์", "ฟิสิกส์").replace("ฟสิกส์", "ฟิสิกส์")

    pua_map = {
        '\uf701': '่', '\uf702': '้', '\uf703': '๊', '\uf704': '๋', '\uf705': '์',
        '\uf706': '่', '\uf707': '้', '\uf708': '๊', '\uf709': '๋', '\uf70a': '์',
        '\uf710': '่', '\uf711': '้', '\uf712': '๊', '\uf713': '๋', '\uf714': '์',
    }
    for k, v in pua_map.items():
        text = text.replace(k, v)

    word_map = {
        "ผู%ช'วย": "ผู้ช่วย", "ผู%ช่วย": "ผู้ช่วย", "ผู%รับผิดชอบ": "ผู้รับผิดชอบ", "ผู0รับผิดชอบ": "ผู้รับผิดชอบ",
        "ศาสตราจารย 0": "ศาสตราจารย์", "ศาสตราจารย0": "ศาสตราจารย์", "ศาสตราจารย-": "ศาสตราจารย์",
        "อาจารย 0": "อาจารย์", "อาจารย0": "อาจารย์", "อาจารย-": "อาจารย์",
        "ป3ยณัฐ": "ปิยณัฐ", "โตอ'อน": "โตอ่อน", "คำหล%า": "คำหล้า",
        "ณัฐนันท0": "ณัฐนันท์", "ณัฐนนท0": "ณัฐนนท์", "อิสสระพงศ0": "อิสสระพงศ์", "อิสสระพงศ*": "อิสสระพงศ์",
        "แสงเสถ3ยร": "แสงเสถียร", "แสงเสถ3ยร0": "แสงเสถียร"
    }
    for k, v in word_map.items():
        text = text.replace(k, v)

    text = re.sub(r'([ก-๙])â', r'\1ั', text)
    text = re.sub(r'â([ก-๙])', r'ั\1', text)
    text = re.sub(r'([ก-๙])=', r'\1็', text)
    text = re.sub(r'=([ก-๙])', r'็\1', text)
    text = re.sub(r'([ก-๙])I', r'\1้', text)
    text = re.sub(r'I([ก-๙])', r'้\1', text)
    text = re.sub(r'([ก-๙])R', r'\1่', text)
    text = re.sub(r'R([ก-๙])', r'่\1', text)
    text = re.sub(r'([ก-๙])\'', r'\1่', text)
    text = re.sub(r'\'([ก-๙])', r'่\1', text)
    text = re.sub(r'([ก-๙])%', r'\1้', text)
    text = re.sub(r'%([ก-๙])', r'้\1', text)
    text = re.sub(r'([ก-๙])0(?!\d)', r'\1์', text)
    text = re.sub(r'([ก-๙])6(?!\d)', r'\1์', text)
    text = re.sub(r'([ก-๙])F(?!\w)', r'\1์', text)
    text = re.sub(r'([ก-๙])G(?!\w)', r'\1้', text)
    text = re.sub(r'([ก-๙])m\b', r'\1้', text)
    text = re.sub(r'([ก-๙])w([ก-๙])', r'\1็\2', text)
    text = re.sub(r'([ก-๙])n([ก-๙])', r'\1ั\2', text)
    text = re.sub(r'([ก-๙])3([ก-ฮ])', r'\1ิ\2', text)
    text = re.sub(r'([ก-๙])n\b', r'\1้', text)
    text = re.sub(r'([ก-๙])Ö', r'\1ี', text)
    text = re.sub(r'Ö([ก-๙])', r'ี\1', text)
    text = re.sub(r'([ก-๙])ß', r'\1ึ', text)
    text = re.sub(r'ß([ก-๙])', r'ึ\1', text)
    text = re.sub(r'([ก-๙])[ûÉ]', r'\1้', text)
    text = re.sub(r'[ûÉ]([ก-๙])', r'้\1', text)

    text = text.replace("*", "").replace("\u200b", "").replace("\xa0", " ")
    
    if preserve_newlines:
        lines = [re.sub(r'[^\S\r\n]+', ' ', line).strip() for line in text.splitlines()]
        return "\n".join(l for l in lines if l)
    return clean_text(text)

def generate_curriculum_code(major_name, year):
    major_map = {
        "คอมพิวเตอร์": "CPE", "อุตสาหการ": "IE", "โลจิสติกส์": "LOG",
        "เมคคาทรอนิกส์": "MCT", "ไฟฟ้า": "EE", "โยธา": "CE",
        "เครื่องกล": "ME", "อิเล็กทรอนิกส์": "ETE", "สิ่งแวดล้อม": "ENV"
    }
    for k, v in major_map.items():
        if k in major_name:
            return f"{v}{year}"
    clean_m = re.sub(r'[^ก-๙a-zA-Z]', '', major_name)[:4]
    return f"CURR_{clean_m}{year}"

def is_table_of_contents(text: str) -> bool:
    t = text.replace(" ", "")
    if "สารบัญ" in t: return True
    if "หมวดที่1" in t and "หมวดที่2" in t: return True
    if "หมวดที่2" in t and "หมวดที่3" in t: return True
    return False

def parse_academic_position(pos_raw: str) -> str:
    clean_p = re.sub(r'\s+', '', pos_raw)
    if "รองศาสตราจารย์" in clean_p or "รศ." in clean_p:
        return "รองศาสตราจารย์"
    elif "ผู้ช่วยศาสตราจารย์" in clean_p or "ผศ." in clean_p:
        return "ผู้ช่วยศาสตราจารย์"
    elif "ศาสตราจารย์" in clean_p or clean_p.startswith("ศ."):
        return "ศาสตราจารย์"
    return "อาจารย์"

# ==========================================
# 2. ฟังก์ชันประมวลผล Pipeline
# ==========================================
def run_pipeline(
    pdf_path=DEFAULT_PDF, 
    force_reload=False, 
    progress_callback: Optional[Callable] = None,
    embedding_model: Optional[SentenceTransformer] = None
):
    def report(progress, message):
        if progress_callback:
            progress_callback(progress, message)

    pdf_path = resolve_pdf_path(pdf_path)
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"❌ ไม่พบไฟล์ PDF: {pdf_path}")

    report(3, "กำลังตรวจสอบไฟล์ PDF...")
    file_hash = calculate_file_hash(pdf_path)
    base_filename = os.path.basename(pdf_path)

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cursor = conn.cursor()

    for alter_sql in [
        "ALTER TABLE courses ALTER COLUMN course_name_th TYPE TEXT;",
        "ALTER TABLE courses ALTER COLUMN course_name_en TYPE TEXT;",
        "ALTER TABLE courses ALTER COLUMN course_group TYPE TEXT;",
        "ALTER TABLE courses ALTER COLUMN study_semester TYPE TEXT;",
        "ALTER TABLE courses ALTER COLUMN description_th TYPE TEXT;",
        "ALTER TABLE courses ALTER COLUMN description_en TYPE TEXT;"
    ]:
        try: cursor.execute(alter_sql)
        except Exception: pass

    for clean_sql in [
        "DELETE FROM courses a USING courses b WHERE a.id < b.id AND a.curriculum_id = b.curriculum_id AND a.course_code = b.course_code;",
        "DELETE FROM plos a USING plos b WHERE a.id < b.id AND a.curriculum_id = b.curriculum_id AND a.plo_code = b.plo_code;",
        "DELETE FROM curriculum_mappings a USING curriculum_mappings b WHERE a.id < b.id AND a.course_id = b.course_id AND a.plo_id = b.plo_id;"
    ]:
        try: cursor.execute(clean_sql)
        except Exception: pass

    for idx_sql in [
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_curriculum_course ON courses (curriculum_id, course_code);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_curriculum_plo ON plos (curriculum_id, plo_code);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_mapping ON curriculum_mappings (course_id, plo_id);"
    ]:
        try: cursor.execute(idx_sql)
        except Exception: pass

    conn.autocommit = False

    try:
        cursor.execute("SELECT id, curriculum_code FROM curriculums WHERE file_hash_sha256 = %s;", (file_hash,))
        curr_row = cursor.fetchone()

        if curr_row and not force_reload:
            cursor.execute("SELECT COUNT(*) FROM courses WHERE curriculum_id = %s;", (curr_row[0],))
            c_cnt = cursor.fetchone()[0]
            if c_cnt > 0:
                conn.rollback()
                report(100, "เอกสารนี้อยู่ในระบบแล้วและมีข้อมูลครบถ้วน")
                return True

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)

            # ========================================================
            # [หมวดที่ 1] ข้อมูลทั่วไป
            # ========================================================
            report(10, "กำลังอ่านข้อมูลทั่วไป หมวดที่ 1...")

            m1_start_page = 0
            for p_idx in range(min(35, total_pages)):
                norm_t = normalize_pdf_thai_text(pdf.pages[p_idx].extract_text() or "")
                if ("หมวดที่ 1 ข้อมูลทั่วไป" in norm_t or "หมวดที่ 1" in norm_t) and not is_table_of_contents(norm_t):
                    m1_start_page = p_idx
                    break

            m1_text = ""
            for p_idx in range(m1_start_page, min(m1_start_page + 12, total_pages)):
                m1_text += normalize_pdf_thai_text(pdf.pages[p_idx].extract_text() or "") + "\n"

            report(15, "กำลังสกัดรหัสหลักสูตรและจำนวนหน่วยกิต...")
            curr_code_match = re.search(r'รหัสหลักสูตร\s*[:\s]*(\d{14})', m1_text)
            year_match = re.search(r'25\d{2}', base_filename + " " + m1_text)
            year_str = year_match.group(0) if year_match else "2566"

            name_th_match = re.search(r'(หลักสูตร[ก-๙\s]+บัณฑิต\s+สาขาวิชา[ก-๙\s]+)', m1_text)
            if name_th_match:
                curr_name_th = clean_text(name_th_match.group(1))
            else:
                clean_b = re.sub(r'[\(\)\-\d\.\s]|วศ\.บ\.|ปรับปรุง|พ\.ศ\.', '', base_filename).replace('pdf', '').strip()
                curr_name_th = f"หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชา{clean_b}"

            dept_match = re.search(r'สาขาวิชา([ก-๙]+)', curr_name_th)
            major_clean = dept_match.group(1) if dept_match else "วิศวกรรมศาสตร์"
            curr_code = curr_code_match.group(1) if curr_code_match else generate_curriculum_code(major_clean, year_str)

            name_en_match = re.search(r'(Bachelor of Engineering Program in [A-Za-z\s]+)', m1_text, re.IGNORECASE)
            curr_name_en = clean_text(name_en_match.group(1)) if name_en_match else f"Bachelor of Engineering Program in {major_clean} Engineering"

            degree_th = f"วิศวกรรมศาสตรบัณฑิต ({major_clean})"
            degree_en = f"Bachelor of Engineering ({major_clean} Engineering)"

            credits_match = re.search(r'(?:จำนวนหน่วยกิตที่เรียนตลอดหลักสูตร|หน่วยกิตรวม|ตลอดหลักสูตร)[^\d]*(\d{2,3})\s*(?:หน่วยกิต|หน่วย)?', m1_text)
            tot_credits = int(credits_match.group(1)) if credits_match else 136

            # สกัดอาจารย์ผู้รับผิดชอบหลักสูตร
            report(20, "กำลังสกัดตารางอาจารย์ผู้รับผิดชอบหลักสูตร...")
            instructors = []
            seen_clean_names = set()
            reading_instructors = False

            for p_idx in range(m1_start_page, min(m1_start_page + 18, total_pages)):
                page = pdf.pages[p_idx]
                p_raw = page.extract_text() or ""
                p_norm = normalize_pdf_thai_text(p_raw)
                if is_table_of_contents(p_norm): continue

                has_header = any(kw in p_norm for kw in ["อาจารย์ผู้รับผิดชอบ", "คุณวุฒิการศึกษาของอาจารย์", "ตำแหน่งและคุณวุฒิ"])
                if any(kw in p_norm for kw in ["9. สถานที่จัดการเรียน", "สถานที่จัดการเรียนการสอน", "หมวดที่ 2 ข้อมูลเฉพาะ", "หมวดที่ 2"]):
                    if reading_instructors: break

                if has_header or reading_instructors:
                    tables = page.extract_tables() or []
                    for tbl in tables:
                        for row in tbl:
                            if not row or len(row) < 3: continue
                            row_full = " ".join([clean_text(normalize_pdf_thai_text(str(c or ""))) for c in row])
                            if any(h in row_full for h in ["ลำดับที่", "ชื่อ-นามสกุล", "คุณวุฒิการศึกษา", "ปีที่จบ"]): 
                                reading_instructors = True
                                continue

                            col0_clean = clean_text(str(row[0] or ""))
                            is_new_no = bool(re.search(r'^\d+$', col0_clean))
                            
                            pos_text, name_text, degrees_text, institutions_text, years_text, remarks_text = "", "", "", "", "", ""
                            if len(row) >= 6:
                                pos_text = normalize_pdf_thai_text(str(row[1] or "")).replace("\n", " ").strip()
                                name_text = normalize_pdf_thai_text(str(row[2] or "")).replace("\n", " ").strip()
                                degrees_text = normalize_pdf_thai_text(str(row[3] or ""), preserve_newlines=True)
                                institutions_text = normalize_pdf_thai_text(str(row[4] or ""), preserve_newlines=True)
                                years_text = normalize_pdf_thai_text(str(row[5] or ""), preserve_newlines=True)
                                if len(row) > 6: remarks_text = normalize_pdf_thai_text(str(row[6] or "")).replace("\n", " ").strip()
                            else:
                                for cell in row:
                                    c_clean = clean_text(normalize_pdf_thai_text(str(cell or "")))
                                    if any(t in c_clean for t in ["ศาสตราจารย์", "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์", "อาจารย์"]): pos_text = c_clean
                                    if re.search(r'(นาย|นางสาว|นาง|ดร\.)\s*[ก-๙]', c_clean): name_text = c_clean

                            name_m = re.search(r'(นาย|นางสาว|นาง|ดร\.)\s*([ก-๙]+)\s+([ก-๙*]+)', name_text)

                            if not name_m and not is_new_no and len(instructors) > 0:
                                deg_cell = degrees_text or clean_text(normalize_pdf_thai_text(str(row[min(3, len(row)-1)] or "")))
                                inst_cell = institutions_text or (clean_text(normalize_pdf_thai_text(str(row[4] or ""))) if len(row) > 4 else "")
                                yr_cell = years_text or (clean_text(normalize_pdf_thai_text(str(row[5] or ""))) if len(row) > 5 else "")
                                if any(d_kw in deg_cell for d_kw in ["วศ.", "ปร.ด.", "วท.", "ค.อ.", "Ph.D.", "M.Sc."]) or inst_cell:
                                    instructors[-1]["educations"].append({
                                        "degree": deg_cell or "-",
                                        "institution": inst_cell or "-",
                                        "year": yr_cell or "-"
                                    })
                                    continue

                            if name_m:
                                prefix, fname, lname = name_m.group(1), name_m.group(2), name_m.group(3)
                                is_chair = "*" in lname or "ประธาน" in remarks_text
                                lname = re.sub(r'[\*\d\s]+$', '', lname).strip()
                                actual_name = f"{prefix}{fname} {lname}".strip()
                                matched_pos = parse_academic_position(pos_text)

                                deg_list = [d.strip() for d in degrees_text.splitlines() if d.strip()]
                                inst_list = [i.strip() for i in institutions_text.splitlines() if i.strip()]
                                yr_list = re.findall(r'\b25\d{2}\b', years_text) or [y.strip() for y in years_text.splitlines() if y.strip()]

                                education_records = []
                                for i in range(max(len(deg_list), len(inst_list), len(yr_list), 1)):
                                    d = deg_list[i] if i < len(deg_list) else ""
                                    inst = inst_list[i] if i < len(inst_list) else ""
                                    yr = yr_list[i] if i < len(yr_list) else ""
                                    if d or inst or yr: education_records.append({"degree": d, "institution": inst, "year": yr})

                                clean_key = f"{fname}_{lname}"
                                if clean_key not in seen_clean_names:
                                    seen_clean_names.add(clean_key)
                                    rem = "ประธานหลักสูตร" if is_chair else remarks_text
                                    instructors.append({
                                        "no": len(instructors) + 1, "academic_position": matched_pos,
                                        "name": actual_name, "educations": education_records, "remarks": rem
                                    })
                                    reading_instructors = True

                    lines = [clean_text(normalize_pdf_thai_text(l)) for l in p_raw.splitlines() if l.strip()]
                    for l in lines:
                        match = re.search(r'(ผู้ช่วยศาสตราจารย์|รองศาสตราจารย์|ศาสตราจารย์|อาจารย์)?\s*(นาย|นางสาว|นาง|ดร\.)\s*([ก-๙]+)\s+([ก-๙*]+)', l)
                        if match:
                            pos_str = match.group(1) or l
                            matched_pos = parse_academic_position(pos_str)
                            prefix, fname, lname = match.group(2), match.group(3), match.group(4)
                            is_chair = "*" in lname or "ประธาน" in l
                            lname = re.sub(r'[\*\d\s]+$', '', lname).strip()
                            actual_name = f"{prefix}{fname} {lname}".strip()
                            clean_key = f"{fname}_{lname}"

                            if clean_key not in seen_clean_names:
                                seen_clean_names.add(clean_key)
                                deg_m = re.findall(r'(วศ\.[มบด]\.|ปร\.ด\.|Ph\.D\.|M\.Sc\.|วท\.[มบด]\.|ค\.อ\.[มบ]\.)[^\d]*', l)
                                inst_m = re.findall(r'(ม\.\s*[ก-๙]+|มหาวิทยาลัย[ก-๙]+|University of [A-Za-z]+|U\.\s*of [A-Za-z]+|สถาบัน[ก-๙]+)', l)
                                yr_m = re.findall(r'\b25\d{2}\b', l)
                                ed_records = []
                                for i in range(max(len(deg_m), len(inst_m), len(yr_m), 1)):
                                    ed_records.append({
                                        "degree": clean_text(deg_m[i]) if i < len(deg_m) else "-",
                                        "institution": clean_text(inst_m[i]) if i < len(inst_m) else "-",
                                        "year": yr_m[i] if i < len(yr_m) else "-"
                                    })
                                instructors.append({
                                    "no": len(instructors) + 1, "academic_position": matched_pos,
                                    "name": actual_name, "educations": ed_records, "remarks": "ประธานหลักสูตร" if is_chair else ""
                                })
                                reading_instructors = True

            report(24, "กำลังสกัดปรัชญาและวัตถุประสงค์หลักสูตร (หมวด 2)...")
            m2_start_page = None
            for p_idx in range(m1_start_page, min(m1_start_page + 35, total_pages)):
                norm_t = normalize_pdf_thai_text(pdf.pages[p_idx].extract_text() or "")
                if is_table_of_contents(norm_t): continue
                if "หมวดที่ 2 ข้อมูลเฉพาะของหลักสูตร" in norm_t or ("หมวดที่ 2" in norm_t and "ข้อมูลเฉพาะ" in norm_t):
                    m2_start_page = p_idx
                    break

            m2_text = ""
            if m2_start_page is not None:
                for p_idx in range(m2_start_page, min(m2_start_page + 8, total_pages)):
                    m2_text += normalize_pdf_thai_text(pdf.pages[p_idx].extract_text() or "") + "\n"

            phil_match = re.search(r'1\.1\s*ปรัชญาของหลักสูตร\s*(.*?)(?=\n\s*1\.[2-9]|\n\s*1\.2|\n\s*ความสำคัญ|\n\s*อัตลักษณ์)', m2_text, re.DOTALL)
            curr_philosophy = clean_text(phil_match.group(1)) if phil_match else f"มุ่งผลิตบัณฑิตที่มีความรู้ความเชี่ยวชาญในวิชาชีพวิศวกรรม{major_clean} มีคุณธรรม จริยธรรม และจรรยาบรรณตามหลักวิชาชีพ"

            attr_match = re.search(r'1\.2\s*อัตลักษณ์ของหลักสูตร\s*(.*?)(?=\n\s*1\.[3-9]|\n\s*ความสำคัญ|\n\s*1\.3)', m2_text, re.DOTALL)
            curr_attributes = clean_text(attr_match.group(1)) if attr_match else f"พร้อมทำงาน ก้าวทันเทคโนโลยี มีจรรยาบรรณตามหลักวิชาชีพ{major_clean}"

            obj_match = re.search(r'1\.4\s*วัตถุประสงค์\s*(.*?)(?=\n\s*(?:หมวดที่|2\.|แผนพัฒนา|2\.1))', m2_text, re.DOTALL)
            curr_objectives = clean_text(obj_match.group(1)) if obj_match else f"เพื่อผลิตบัณฑิตวิศวกรให้มีความรู้ความสามารถด้านวิชาการและวิชาชีพทั้งภาคทฤษฎีและภาคปฏิบัติในงานวิศวกรรม{major_clean}"

            credit_structure = {}
            for p_idx in range(m2_start_page or 15, min((m2_start_page or 15) + 25, total_pages)):
                p_norm = normalize_pdf_thai_text(pdf.pages[p_idx].extract_text() or "")
                if is_table_of_contents(p_norm): continue
                if "3.1 โครงสร้างหลักสูตร" in p_norm or "โครงสร้างหลักสูตรวิศวกรรมศาสตรบัณฑิต" in p_norm:
                    ge_m = re.search(r'หมวดวิชาศึกษาทั่วไป\s*(\d{1,3})\s*หน่วยกิต', p_norm)
                    sp_m = re.search(r'หมวดวิชาเฉพาะ\s*(\d{1,3})\s*หน่วยกิต', p_norm)
                    fe_m = re.search(r'หมวดวิชาเลือกเสรี\s*(\d{1,3})\s*หน่วยกิต', p_norm)
                    if ge_m: credit_structure["general_education_credits"] = int(ge_m.group(1))
                    if sp_m: credit_structure["specialized_credits"] = int(sp_m.group(1))
                    if fe_m: credit_structure["free_elective_credits"] = int(fe_m.group(1))
                    break

            instructors_json = json.dumps(instructors, ensure_ascii=False)
            curriculum_data = {
                "curriculum_code": curr_code,
                "curriculum_name_th": curr_name_th,
                "curriculum_name_en": curr_name_en,
                "degree_name_th": degree_th,
                "degree_name_en": degree_en,
                "faculty": "คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม",
                "department": f"สาขาวิชาวิศวกรรม{major_clean}",
                "total_credits": tot_credits,
                "credit_structure": credit_structure,
                "philosophy": curr_philosophy,
                "objectives": curr_objectives,
                "graduate_attributes": curr_attributes
            }
            raw_json_str = json.dumps(curriculum_data, ensure_ascii=False)

            if curr_row:
                curriculum_id = curr_row[0]
                cursor.execute("""
                    UPDATE curriculums 
                    SET curriculum_code = %s, curriculum_name_th = %s, curriculum_name_en = %s, degree_name_th = %s, degree_name_en = %s,
                        faculty = %s, department = %s, total_credits = %s, philosophy = %s, objectives = %s,
                        graduate_attributes = %s, responsible_instructors = %s::jsonb, raw_json = %s::jsonb,
                        file_path = %s, file_hash_sha256 = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (
                    curr_code, curriculum_data["curriculum_name_th"], curriculum_data["curriculum_name_en"],
                    curriculum_data["degree_name_th"], curriculum_data["degree_name_en"],
                    curriculum_data["faculty"], curriculum_data["department"], curriculum_data["total_credits"],
                    curriculum_data["philosophy"], curriculum_data["objectives"], curriculum_data["graduate_attributes"],
                    instructors_json, raw_json_str, pdf_path, file_hash, curriculum_id
                ))
            else:
                cursor.execute("SELECT id FROM curriculums WHERE curriculum_code = %s;", (curr_code,))
                if cursor.fetchone():
                    curr_code = f"{curr_code}_{file_hash[:4].upper()}"

                cursor.execute("""
                    INSERT INTO curriculums (
                        curriculum_code, curriculum_name_th, curriculum_name_en, degree_name_th,
                        degree_name_en, faculty, department, total_credits, philosophy,
                        objectives, graduate_attributes, responsible_instructors, raw_json, file_path, file_hash_sha256
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
                    RETURNING id;
                """, (
                    curr_code, curriculum_data["curriculum_name_th"], curriculum_data["curriculum_name_en"],
                    curriculum_data["degree_name_th"], curriculum_data["degree_name_en"],
                    curriculum_data["faculty"], curriculum_data["department"], curriculum_data["total_credits"],
                    curriculum_data["philosophy"], curriculum_data["objectives"], curriculum_data["graduate_attributes"],
                    instructors_json, raw_json_str, pdf_path, file_hash
                ))
                curriculum_id = cursor.fetchone()[0]

            report(28, f"บันทึกข้อมูลหลักสูตร {curr_code} เรียบร้อย")

            # ========================================================
            # [หมวดที่ 3] แผนการศึกษาและคำอธิบายรายวิชา
            # ========================================================
            report(35, "กำลังสแกนแผนการศึกษา 4 ปี...")
            plan_mapping = {}
            current_yr, current_sem = 1, 1

            for p_idx in range(20, min(100, total_pages)):
                p_text = normalize_pdf_thai_text(pdf.pages[p_idx].extract_text(layout=False) or "")
                if is_table_of_contents(p_text): continue
                if "แผนการศึกษา" in p_text or "ปีการศึกษาที่" in p_text:
                    yr_m = re.search(r'ปีการศึกษาที่\s*(\d)', p_text)
                    sem_m = re.search(r'ภาคการศึกษาที่\s*(\d)', p_text)
                    if yr_m: current_yr = int(yr_m.group(1))
                    if sem_m: current_sem = int(sem_m.group(1))

                    for c_code in re.findall(r'\b([A-Za-z0-9]{2}\s*[-–]?\s*\d{3}\s*[-–]?\s*\d{3})\b', p_text):
                        clean_c = re.sub(r'\s+', '', c_code).replace('–', '-').upper()
                        if clean_c not in plan_mapping:
                            plan_mapping[clean_c] = (current_yr, current_sem)

            report(45, "กำลังระบุตำแหน่งหมวดคำอธิบายรายวิชา...")
            desc_start_page = None
            desc_end_page = total_pages

            for p_idx in range(30, total_pages):
                txt = normalize_pdf_thai_text(pdf.pages[p_idx].extract_text(layout=False) or "")
                if is_table_of_contents(txt): continue
                if ("คำอธิบายรายวิชา" in txt or "3.1.6 คำอธิบายรายวิชา" in txt) and desc_start_page is None:
                    desc_start_page = p_idx
                if desc_start_page is not None and p_idx > desc_start_page:
                    if any(stop_kw in txt for stop_kw in ["หมวดที่ 4", "หมวดที่ 5", "3.2 ชื่อ สกุล", "การกระจายความรับผิดชอบ", "Curriculum Mapping"]):
                        desc_end_page = p_idx
                        break

            if desc_start_page is None:
                desc_start_page = 40

            report(50, f"กำลังสกัดคำอธิบายรายวิชา (หน้า {desc_start_page + 1} ถึง {desc_end_page})...")
            desc_texts = []
            for p_idx in range(desc_start_page, desc_end_page):
                desc_texts.append(pdf.pages[p_idx].extract_text(layout=False) or "")

            full_desc_text = "\n".join(desc_texts)
            full_desc_text = normalize_pdf_thai_text(full_desc_text, preserve_newlines=True)
            full_desc_text = re.sub(r'([A-Za-z]{2})\s*[-–]?\s*(\d{3})\s*[-–]?\s*(\d{3})', r'\1-\2-\3', full_desc_text)
            entries = re.split(r'\n(?=[A-Za-z]{2}-\d{3}-\d{3}\b)', full_desc_text)
            course_map_db = {}

            for entry in entries:
                match = re.match(r'^([A-Za-z]{2}-\d{3}-\d{3})\s*(.*?)$', entry, re.DOTALL)
                if match:
                    c_code = match.group(1).strip().upper()
                    body = match.group(2).strip()

                    credit_m = re.search(r'(\d+)\s*\(\s*(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s*\)', body)
                    if credit_m:
                        tot_c = int(credit_m.group(1))
                        lec = int(credit_m.group(2))
                        lab = int(credit_m.group(3))
                        self_std = int(credit_m.group(4))
                        header_part = body[:credit_m.start()].split('\n')[0]
                    else:
                        tot_c, lec, lab, self_std = 3, 3, 0, 6
                        header_part = body.split('\n')[0]

                    header_clean = normalize_pdf_thai_text(header_part)
                    header_clean = re.sub(r'\([A-Za-z\s\-,/():&]+\)', '', header_clean)
                    header_clean = re.sub(r'[^ก-๙0-9\s\(\)\-\.\,\/\+\&\:\;]', '', header_clean)
                    raw_th_name = clean_text(header_clean)

                    if not raw_th_name:
                        raw_th_name = f"รายวิชา {c_code}"

                    c_en_name = ""
                    en_m = re.search(r'\(\s*([A-Za-z][A-Za-z0-9\s\-,/():&]{2,200}?)\s*\)', body[:350])
                    if en_m:
                        c_en_name = clean_text(en_m.group(1))
                    else:
                        for l in body.split('\n')[:4]:
                            clean_l = clean_text(l)
                            if re.match(r'^[A-Za-z\s\-,/():&]+$', clean_l) and 3 < len(clean_l) < 200:
                                c_en_name = clean_l
                                break

                    content_lines = body.split('\n')
                    desc_lines_th, desc_lines_en = [], []

                    for line in content_lines[1:]:
                        clean_l = clean_text(line)
                        if any(kw in clean_l for kw in ["วิชาบังคับก่อน", "Prerequisite", "รายวิชาบังคับก่อน"]):
                            continue
                        if credit_m and str(tot_c) in clean_l and f"({lec}-{lab}-{self_std})" in clean_l:
                            continue

                        has_thai = bool(re.search(r'[ก-๙]', clean_l))
                        has_eng = bool(re.search(r'[A-Za-z]{3,}', clean_l))

                        if has_thai:
                            desc_lines_th.append(normalize_pdf_thai_text(clean_l))
                        elif has_eng:
                            desc_lines_en.append(clean_l)

                    desc_th = clean_text(" ".join(desc_lines_th))
                    desc_en = clean_text(" ".join(desc_lines_en))

                    course_group = "หมวดวิชาศึกษาทั่วไป" if (c_code.startswith("GE-") or re.match(r'^\d', c_code)) else ("หมวดวิชาเลือกเสรี" if "เลือกเสรี" in raw_th_name else "หมวดวิชาเฉพาะ")
                    study_yr, study_sem = plan_mapping.get(c_code, (None, None))

                    safe_th_name = raw_th_name[:500].strip() if raw_th_name else f"รายวิชา {c_code}"
                    safe_en_name = c_en_name[:500].strip() if c_en_name else ""
                    safe_group = str(course_group)[:100].strip() if course_group else "หมวดวิชาเฉพาะ"
                    safe_sem = str(study_sem)[:10] if study_sem is not None else None

                    cursor.execute("""
                        INSERT INTO courses (
                            curriculum_id, course_code, course_name_th, course_name_en,
                            credit_lecture, credit_lab, credit_self, total_credits, course_group,
                            study_year, study_semester, description_th, description_en
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (curriculum_id, course_code) 
                        DO UPDATE SET 
                            course_name_th = EXCLUDED.course_name_th,
                            course_name_en = EXCLUDED.course_name_en,
                            total_credits = EXCLUDED.total_credits,
                            credit_lecture = EXCLUDED.credit_lecture,
                            credit_lab = EXCLUDED.credit_lab,
                            credit_self = EXCLUDED.credit_self,
                            course_group = EXCLUDED.course_group,
                            study_year = COALESCE(EXCLUDED.study_year, courses.study_year),
                            study_semester = COALESCE(EXCLUDED.study_semester, courses.study_semester),
                            description_th = EXCLUDED.description_th,
                            description_en = EXCLUDED.description_en,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING id;
                    """, (curriculum_id, c_code, safe_th_name, safe_en_name, lec, lab, self_std, tot_c, safe_group, study_yr, safe_sem, desc_th, desc_en))
                    course_map_db[c_code] = cursor.fetchone()[0]

            cursor.execute("DELETE FROM course_prerequisites WHERE course_id IN (SELECT id FROM courses WHERE curriculum_id = %s);", (curriculum_id,))
            for c_code, c_id in course_map_db.items():
                cursor.execute("SELECT description_th FROM courses WHERE id = %s;", (c_id,))
                d_th = cursor.fetchone()[0] or ""
                for p_code in re.findall(r'(?:รายวิชาบังคับก่อน|Prerequisite|วิชาบังคับก่อน)\s*[:\s]*([A-Za-z0-9]{2}-\d{3}-\d{3})', d_th):
                    p_code = p_code.upper()
                    cursor.execute("""
                        INSERT INTO course_prerequisites (course_id, prerequisite_course_code, prerequisite_course_id)
                        VALUES (%s, %s, %s) ON CONFLICT (course_id, prerequisite_course_code) DO NOTHING;
                    """, (c_id, p_code, course_map_db.get(p_code)))

            # ========================================================
            # [หมวดที่ 4] ผลลัพธ์การเรียนรู้ (PLOs) & Curriculum Mapping
            # ========================================================
            report(65, "กำลังสแกนหาข้อความ PLO และวิเคราะห์ตาราง Mapping ทั่วทั้งเล่ม...")

            cursor.execute("DELETE FROM curriculum_mappings WHERE course_id IN (SELECT id FROM courses WHERE curriculum_id = %s);", (curriculum_id,))
            cursor.execute("UPDATE plos SET parent_plo_id = NULL WHERE curriculum_id = %s;", (curriculum_id,))
            cursor.execute("DELETE FROM plos WHERE curriculum_id = %s;", (curriculum_id,))

            CHECKMARK_CHARS = ['✓', '✔', '☑', '', 'ü', 'þ', 'P', 'p', 'v', 'V', '/', '\\', 'x', 'X', '\uf0fc', '\uf0fe', '\uf050', '\uf051', '\uf020', '\u2713', '\u2714', '\u2705', '\u221a']
            PRIMARY_CHARS = ['⚫', '●', '•', '', '\uf06c', '\uf0b7', '⬤', '⦁', '■', '1', 'l'] + CHECKMARK_CHARS
            SECONDARY_CHARS = ['\uf0a1', '○', '⚪', '', '', '\uf04f', '\uf06e', '◯', '□', '◦', '¡', '2', 'o', 'O']

            def detect_responsibility(cell_val: str) -> Optional[str]:
                if not cell_val: return None
                raw = str(cell_val).replace("\u200b", "").replace("\xa0", " ").strip()
                if not raw: return None
                if re.search(r'[ก-๙]', raw): return None
                if len(raw) > 5 and not any(s in raw for s in PRIMARY_CHARS + SECONDARY_CHARS): return None
                
                for ch in raw:
                    code_pt = ord(ch)
                    if 0xf000 <= code_pt <= 0xf0ff:
                        if code_pt in [0xf0a1, 0xf04f, 0xf06e]:
                            return "ความรับผิดชอบรอง"
                        return "ความรับผิดชอบหลัก"

                if any(s in raw for s in PRIMARY_CHARS):
                    return "ความรับผิดชอบหลัก"
                if any(s in raw for s in SECONDARY_CHARS):
                    return "ความรับผิดชอบรอง"
                return None

            # ค้นหาหน้าตาราง Mapping ทั้งหมดทั่วทั้งเล่ม
            mapping_pages_idx = []
            for p_idx in range(15, total_pages):
                txt = normalize_pdf_thai_text(pdf.pages[p_idx].extract_text(layout=False) or "")
                if is_table_of_contents(txt): continue
                
                is_map_page = any(kw in txt for kw in [
                    "การกระจายความรับผิดชอบ", "Curriculum Mapping", "ตารางแสดงความรับผิดชอบ",
                    "รายวิชา/CLOs", "แผนที่แสดงการกระจาย", "CLO", "CLOs", "PLO1", "PLO 1",
                    "ความรับผิดชอบหลัก", "ผลลัพธ์การเรียนรู้สู่รายวิชา", "ความสัมพันธ์ระหว่างผลลัพธ์"
                ])
                if is_map_page:
                    mapping_pages_idx.append(p_idx)

            # ค้นหาหน้าต่อ (Continuation pages) ต่อเนื่องไม่ให้หลุด
            expanded = set(mapping_pages_idx)
            for p in mapping_pages_idx:
                for next_p in range(p + 1, min(p + 15, total_pages)):
                    next_txt = normalize_pdf_thai_text(pdf.pages[next_p].extract_text(layout=False) or "")
                    if any(stop_kw in next_txt for stop_kw in ["หมวดที่ 5", "หมวดที่ 6"]): break
                    if any(s in next_txt for s in PRIMARY_CHARS + SECONDARY_CHARS) or re.search(r'\b[A-Za-z]{2}\s*[-–]?\s*\d{3}', next_txt):
                        expanded.add(next_p)
            mapping_pages_idx = sorted(list(expanded))

            # ------------------------------------------------------------------------
            # จุดชี้ขาด: ค้นหาหัวตาราง PLO ของหลักสูตรวิศวกรรมจริง (PLO1–PLO10) ทั่วทุกหน้า
            # ------------------------------------------------------------------------
            has_plo_format = False
            has_subplo_format = False
            max_plo_num = 10
            discovered_subplos = []

            for p_idx in mapping_pages_idx:
                tbls = pdf.pages[p_idx].extract_tables() or []
                for tbl in tbls:
                    if not tbl or len(tbl) < 2: continue
                    for row in tbl[:4]:
                        for cell in row:
                            c_str = clean_text(normalize_pdf_thai_text(str(cell or ""))).replace(" ", "").upper()
                            plo_m = re.match(r'^PLO(\d+)$', c_str)
                            if plo_m:
                                has_plo_format = True
                                max_plo_num = max(max_plo_num, int(plo_m.group(1)))
                            elif re.match(r'^\d+[A-Z]$', c_str):
                                has_subplo_format = True
                                if c_str not in discovered_subplos:
                                    discovered_subplos.append(c_str)

            plos_dict = {}
            # 1. หากพบ PLO1 - PLO10 (เล่มเครื่องกล / เล่มวิศวกรรมหลัก)
            if has_plo_format or not has_subplo_format:
                for i in range(1, max_plo_num + 1):
                    plos_dict[str(i)] = {"code": str(i), "desc": f"ผลลัพธ์การเรียนรู้ที่ {i} (PLO{i})", "subs": {}}
            # 2. หากพบ Sub-PLO เช่น 1A, 1B (เล่มวิศวกรรมคอมพิวเตอร์)
            elif has_subplo_format:
                for h in discovered_subplos:
                    m_num = re.search(r'\d+', h).group(0) if re.search(r'\d+', h) else "1"
                    if m_num not in plos_dict:
                        plos_dict[m_num] = {"code": m_num, "desc": f"ผลลัพธ์การเรียนรู้ที่ {m_num}", "subs": {}}
                    plos_dict[m_num]["subs"][h] = f"ผลลัพธ์การเรียนรู้ย่อย {h}"

            plo_db_lookup = {}
            ordered_sub_plos = []
            
            for m_code, data in plos_dict.items():
                cursor.execute("""
                    INSERT INTO plos (curriculum_id, plo_code, plo_description, parent_plo_id)
                    VALUES (%s, %s, %s, NULL) RETURNING id;
                """, (curriculum_id, f"PLO{m_code}", data["desc"]))
                parent_id = cursor.fetchone()[0]

                # ลงทะเบียน Lookup ทุกรูปแบบ เพื่อให้ดึงจุดได้ทั้ง 2 ตาราง
                plo_db_lookup[f"PLO{m_code}"] = parent_id
                plo_db_lookup[str(m_code)] = parent_id
                ordered_sub_plos.append(f"PLO{m_code}")

                # สะพานเชื่อม: แมป GELO 1.1-1.2 -> PLO1, 2.1-2.4 -> PLO2 ... 5.1-5.4 -> PLO5 อัตโนมัติ
                if int(m_code) <= 5:
                    for sub_idx in range(1, 6):
                        plo_db_lookup[f"{m_code}.{sub_idx}"] = parent_id

                for s_code, s_desc in data["subs"].items():
                    cursor.execute("""
                        INSERT INTO plos (curriculum_id, plo_code, plo_description, parent_plo_id)
                        VALUES (%s, %s, %s, %s) RETURNING id;
                    """, (curriculum_id, s_code, s_desc, parent_id))
                    sub_id = cursor.fetchone()[0]
                    plo_db_lookup[s_code] = sub_id
                    plo_db_lookup[f"PLO{s_code}"] = sub_id
                    ordered_sub_plos.append(s_code)

            report(75, f"ลงทะเบียน PLO สำเร็จ ({len(ordered_sub_plos)} ข้อ) กำลังดึงเมทริกซ์ทุกรายวิชา...")
            report(80, f"พบหน้าตาราง Mapping {len(mapping_pages_idx)} หน้า กำลังอ่านเมทริกซ์...")

            course_mappings = []
            last_col_to_plo = {}

            for p_idx in mapping_pages_idx:
                page = pdf.pages[p_idx]
                tables = page.extract_tables() or []
                table_found = False

                for tbl in tables:
                    if not tbl or len(tbl) < 2: continue
                    header_row_idx = None
                    col_to_plo = {}

                    # 1. พยายามจับคู่หัวตารางจาก 4 แถวแรก
                    for r_i, row in enumerate(tbl[:4]):
                        matched = {}
                        for c_i, cell in enumerate(row):
                            c_raw = clean_text(normalize_pdf_thai_text(str(cell or ""))).strip()
                            c_clean = c_raw.replace(" ", "").replace("-", "").replace(".", "").upper()
                            if not c_clean: continue
                            
                            # ตรวจจับแบบตรงรหัส PLO1..PLO10 หรือ 1A..5D
                            for plo in ordered_sub_plos:
                                clean_plo = plo.replace("-", "").replace(".", "").upper()
                                if c_clean in [clean_plo, f"PLO{clean_plo}"] or (clean_plo.startswith("PLO") and c_clean == clean_plo[3:]) or (re.match(r'^\d+$', c_clean) and clean_plo == f"PLO{c_clean}"):
                                    matched[c_i] = plo
                                    break
                                    
                            # ตรวจจับแบบรหัสย่อย 1.1, 1.2
                            if c_i not in matched and c_raw in plo_db_lookup:
                                matched[c_i] = c_raw
                                    
                        if len(matched) >= 3:
                            header_row_idx = r_i
                            col_to_plo = matched
                            last_col_to_plo = col_to_plo.copy()
                            break

                    # 2. จำพิกัดข้ามหน้าต่อ (Continuation Page)
                    if not col_to_plo and last_col_to_plo:
                        max_cols_in_tbl = max(len(r) for r in tbl if r)
                        if max_cols_in_tbl >= max(last_col_to_plo.keys()) + 1:
                            col_to_plo = last_col_to_plo.copy()
                            header_row_idx = -1

                    if col_to_plo:
                        table_found = True
                        start_r = header_row_idx + 1 if header_row_idx is not None and header_row_idx >= 0 else 0
                        for row in tbl[start_r:]:
                            if not row: continue
                            subj_cell = " ".join(normalize_pdf_thai_text(str(row[i] or "")) for i in range(min(5, len(row))) if i not in col_to_plo)
                            if any(h in subj_cell for h in ["รหัสวิชา", "ชื่อวิชา", "ความรับผิดชอบ", "ผลการเรียนรู้", "Curriculum", "GELO"]):
                                continue

                            dots = []
                            for c_i, plo in col_to_plo.items():
                                if c_i < len(row):
                                    res_type = detect_responsibility(row[c_i])
                                    if res_type:
                                        dots.append({'plo': plo, 'type': res_type})
                            if dots and subj_cell.strip():
                                course_mappings.append({'course_text': subj_cell, 'mappings': dots})

                # Fallback ด้วยพิกัดคำ
                if not table_found:
                    words = page.extract_words(x_tolerance=2, y_tolerance=3)
                    if not words: continue

                    dot_words = [w for w in words if detect_responsibility(w['text']) and (w['x0'] + w['x1']) / 2 > 140]
                    if dot_words:
                        x_centers = sorted([(w['x0'] + w['x1']) / 2 for w in dot_words])
                        clusters = []
                        for xc in x_centers:
                            if not clusters or abs(clusters[-1] - xc) > 7:
                                clusters.append(xc)

                        if len(clusters) >= 4:
                            rows = []
                            for w in words:
                                y_center = (w['top'] + w['bottom']) / 2
                                matched_row = next((r for r in rows if abs(r['y_center'] - y_center) < 11), None)
                                if matched_row: matched_row['words'].append(w)
                                else: rows.append({'y_center': y_center, 'words': [w]})

                            min_col_x = min(clusters) - 10
                            for r in rows:
                                r_words = sorted(r['words'], key=lambda x: x['x0'])
                                subj_parts, dots = [], []
                                for w in r_words:
                                    w_cx = (w['x0'] + w['x1']) / 2
                                    res_type = detect_responsibility(w['text'])

                                    if res_type and w_cx >= min_col_x:
                                        closest_idx = min(range(len(clusters)), key=lambda i: abs(w_cx - clusters[i]))
                                        if abs(w_cx - clusters[closest_idx]) < 18 and closest_idx < len(ordered_sub_plos):
                                            dots.append({'plo': ordered_sub_plos[closest_idx], 'type': res_type})
                                    elif w_cx < min_col_x:
                                        subj_parts.append(w['text'])

                                if dots:
                                    raw_c = normalize_pdf_thai_text(" ".join(subj_parts))
                                    if raw_c and not any(kw in raw_c for kw in ["ความรับผิดชอบ", "ผลลัพธ์", "Curriculum", "GELO"]):
                                        course_mappings.append({'course_text': raw_c, 'mappings': dots})

            # ========================================================
            # บันทึกความเชื่อมโยง Course-PLO (พร้อมระบบ Auto-Insert วิชาตกหล่น)
            # ========================================================
            cursor.execute("SELECT id, course_code, course_name_th FROM courses WHERE curriculum_id = %s;", (curriculum_id,))
            courses_db = list(cursor.fetchall())
            mapping_count = 0

            clean_fn = lambda s: re.sub(r'[^ก-๙0-9A-Za-z]', '', normalize_pdf_thai_text(s or '')).lower()
            clean_code_fn = lambda s: re.sub(r'[^A-Za-z0-9]', '', s or '').upper()

            for item in course_mappings:
                raw_text = normalize_pdf_thai_text(item['course_text'])
                clean_raw = clean_fn(raw_text)
                c_id = None

                # 1. จับคู่จากรหัสวิชาตรงๆ
                code_match = re.search(r'\b([A-Za-z]{2})\s*[-–]?\s*(\d{3})\s*[-–]?\s*(\d{3})\b', raw_text)
                if code_match:
                    target_code = f"{code_match.group(1).upper()}-{code_match.group(2)}-{code_match.group(3)}"
                    for cid, ccode, cth in courses_db:
                        if clean_code_fn(ccode) == clean_code_fn(target_code):
                            c_id = cid
                            break

                # 2. จับคู่ชื่อวิชาตรง 100%
                if not c_id:
                    for cid, ccode, cth in courses_db:
                        if clean_fn(cth) == clean_raw:
                            c_id = cid
                            break

                # 3. จับคู่ชื่อวิชา + บังคับตัวเลขกำกับท้ายวิชาตรงกัน
                if not c_id:
                    raw_digits = re.findall(r'\d+', clean_raw)
                    for cid, ccode, cth in courses_db:
                        clean_db = clean_fn(cth)
                        db_digits = re.findall(r'\d+', clean_db)
                        if (clean_db in clean_raw or clean_raw in clean_db) and (not db_digits or raw_digits == db_digits):
                            c_id = cid
                            break

                # 4. Fuzzy Matching
                if not c_id:
                    best_ratio, best_cid = 0, None
                    for cid, ccode, cth in courses_db:
                        clean_db = clean_fn(cth)
                        ratio = difflib.SequenceMatcher(None, clean_db, clean_raw).ratio()
                        if ratio > best_ratio and ratio >= 0.65:
                            best_ratio, best_cid = ratio, cid
                    if best_cid: c_id = best_cid

                # 5. ถ้ารายวิชามีรหัสชัดเจนในตาราง Mapping แต่ไม่มีในตาราง courses ให้สร้างวิชาขึ้นมารองรับจุดทันที
                if not c_id and code_match:
                    c_code = f"{code_match.group(1).upper()}-{code_match.group(2)}-{code_match.group(3)}"
                    c_name = clean_text(re.sub(r'^[A-Za-z0-9\s\-–]+', '', raw_text)) or f"รายวิชา {c_code}"
                    c_group = "หมวดวิชาศึกษาทั่วไป" if c_code.startswith("GE-") else "หมวดวิชาเฉพาะ"

                    cursor.execute("""
                        INSERT INTO courses (
                            curriculum_id, course_code, course_name_th, course_name_en,
                            credit_lecture, credit_lab, credit_self, total_credits, course_group
                        ) VALUES (%s, %s, %s, '', 3, 0, 6, 3, %s)
                        ON CONFLICT (curriculum_id, course_code) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
                        RETURNING id;
                    """, (curriculum_id, c_code, c_name, c_group))
                    c_id = cursor.fetchone()[0]
                    courses_db.append((c_id, c_code, c_name))

                if c_id:
                    for m in item['mappings']:
                        p_id = plo_db_lookup.get(m['plo'])
                        if p_id:
                            cursor.execute("""
                                INSERT INTO curriculum_mappings (course_id, plo_id, responsibility_type)
                                VALUES (%s, %s, %s)
                                ON CONFLICT (course_id, plo_id)
                                DO UPDATE SET responsibility_type = EXCLUDED.responsibility_type;
                            """, (c_id, p_id, m['type']))
                            mapping_count += 1

            report(95, f"บันทึกเมทริกซ์ Course-PLO สำเร็จ {mapping_count} จุด")

        conn.commit()
        report(100, "ประมวลผลเอกสารเสร็จสมบูรณ์")
        print(f"\n🎉 สกัดข้อมูลเสร็จสิ้นครบถ้วน! บันทึกอาจารย์ {len(instructors)} ท่าน และเมทริกซ์ PLO ทั้งหมด {mapping_count} จุด")
        return True

    except Exception as e:
        conn.rollback()
        print(f"❌ Pipeline Error: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    pdf_input = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else DEFAULT_PDF
    force = "--force" in sys.argv
    run_pipeline(pdf_path=pdf_input, force_reload=force)