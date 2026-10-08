"""
ตัวช่วยจัดอันดับผลการค้นหาแบบ Hybrid (Vector + Keyword)

แยกออกจาก main.py เพื่อให้ทดสอบได้โดยไม่ต้องต่อฐานข้อมูล
"""
import re
from typing import Dict, List

# น้ำหนักการรวมคะแนน: ความหมาย (vector) เป็นหลัก คำค้นตรงตัวเป็นตัวเสริม
SEMANTIC_WEIGHT = 0.8
KEYWORD_WEIGHT = 0.2

KEYWORD_FIELDS = {
    "course_code": "รหัสวิชา",
    "course_name_th": "ชื่อวิชา (ไทย)",
    "course_name_en": "ชื่อวิชา (อังกฤษ)",
    "description_th": "คำอธิบายรายวิชา",
    "description_en": "คำอธิบายรายวิชา (อังกฤษ)",
}


def tokenize_query(query: str) -> List[str]:
    """แยกคำค้นด้วยช่องว่าง/เครื่องหมาย (ภาษาไทยไม่มีช่องว่างระหว่างคำ จึงเก็บทั้งวลีไว้ด้วย)"""
    query = (query or "").strip().lower()
    if not query:
        return []
    parts = [p for p in re.split(r"[\s,;/|]+", query) if len(p) >= 2]
    tokens = [query] + parts
    seen, unique = set(), []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            unique.append(token)
    return unique


def keyword_match(row: Dict, tokens: List[str]):
    """คืนค่า (สัดส่วนคำที่พบ 0..1, รายชื่อฟิลด์ที่พบ)"""
    if not tokens:
        return 0.0, []
    # คำย่อยที่ใช้คิดสัดส่วน (ไม่นับวลีเต็มซ้ำ ถ้ามีหลายคำ)
    scoring_tokens = tokens[1:] if len(tokens) > 1 else tokens
    hits, fields = 0, []
    for token in scoring_tokens:
        found = False
        for field in KEYWORD_FIELDS:
            value = (row.get(field) or "").lower()
            if token in value:
                found = True
                if field not in fields:
                    fields.append(field)
        hits += 1 if found else 0
    ratio = hits / len(scoring_tokens)
    # วลีเต็มตรงกับรหัสหรือชื่อวิชา = ตรงมาก
    full = tokens[0]
    for field in ("course_code", "course_name_th", "course_name_en"):
        if full in (row.get(field) or "").lower():
            ratio = 1.0
            if field not in fields:
                fields.append(field)
    return ratio, fields


def rank_candidates(rows: List[Dict], query: str, min_score: float, limit: int) -> List[Dict]:
    """
    rows ต้องมีคีย์ similarity (cosine 0..1) และฟิลด์ข้อความของรายวิชา
    คืนรายการที่จัดอันดับแล้ว พร้อม score (0..100), match_type และ matched_fields
    """
    tokens = tokenize_query(query)
    ranked = []
    for row in rows:
        similarity = float(row.get("similarity") or 0.0)
        kw_ratio, fields = keyword_match(row, tokens)
        combined = SEMANTIC_WEIGHT * similarity + KEYWORD_WEIGHT * kw_ratio

        if kw_ratio > 0 and similarity >= min_score:
            match_type = "both"
        elif kw_ratio > 0:
            match_type = "keyword"
        else:
            match_type = "semantic"

        # ตัดผลที่ทั้งความหมายต่ำกว่าเกณฑ์และไม่มีคำค้นตรงเลย
        if similarity < min_score and kw_ratio == 0:
            continue

        item = dict(row)
        item["similarity"] = round(similarity, 4)
        item["keyword_ratio"] = round(kw_ratio, 3)
        item["score"] = round(combined * 100, 1)
        item["match_type"] = match_type
        item["matched_fields"] = [KEYWORD_FIELDS[f] for f in fields]
        ranked.append(item)

    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked[:limit]


def escape_like(text: str) -> str:
    """กันไม่ให้ % และ _ ในคำค้นกลายเป็น wildcard ของ ILIKE"""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
