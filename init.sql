-- 1. เปิดใช้งาน Extension สำหรับ UUID และ Vector 1,024 มิติ
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. สร้างฟังก์ชันสำหรับอัปเดต updated_at อัตโนมัติ
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 3. ตารางข้อมูลหลักสูตร (Curriculums)
CREATE TABLE IF NOT EXISTS curriculums (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    curriculum_code VARCHAR(50) NOT NULL UNIQUE,
    curriculum_name_th VARCHAR(255) NOT NULL,
    curriculum_name_en VARCHAR(255) NOT NULL,
    degree_name_th VARCHAR(255) NOT NULL,
    degree_name_en VARCHAR(255) NOT NULL,
    faculty VARCHAR(255) NOT NULL,
    department VARCHAR(255) NOT NULL,
    total_credits INT NOT NULL,
    philosophy TEXT,
    objectives TEXT,
    graduate_attributes TEXT,
    responsible_instructors JSONB, 
    raw_json JSONB NOT NULL,
    verification_status VARCHAR(20) DEFAULT 'UNVERIFIED',
    file_path VARCHAR(512) NOT NULL,
    file_hash_sha256 CHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 4. ตารางรายวิชา (Courses)
CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    curriculum_id UUID NOT NULL REFERENCES curriculums(id) ON DELETE CASCADE,
    course_code VARCHAR(50) NOT NULL,
    course_name_th VARCHAR(255) NOT NULL,
    course_name_en VARCHAR(255) NOT NULL,
    credit_lecture INT NOT NULL DEFAULT 3,
    credit_lab INT NOT NULL DEFAULT 0,
    credit_self INT NOT NULL DEFAULT 6,
    total_credits INT NOT NULL DEFAULT 3,
    course_group VARCHAR(100) NOT NULL,
    study_year INT,
    study_semester VARCHAR(10),
    description_th TEXT,
    description_en TEXT,
    embedding vector(1024), 
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_curriculum_course UNIQUE (curriculum_id, course_code)
);

-- 5. ตารางผลลัพธ์การเรียนรู้ (PLOs & Sub-PLOs)
CREATE TABLE IF NOT EXISTS plos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    curriculum_id UUID NOT NULL REFERENCES curriculums(id) ON DELETE CASCADE,
    parent_plo_id UUID REFERENCES plos(id) ON DELETE CASCADE, 
    plo_code VARCHAR(50) NOT NULL,
    plo_description TEXT NOT NULL,
    embedding vector(1024),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_curriculum_plo UNIQUE (curriculum_id, plo_code)
);

-- 6. ตารางวิชาบังคับก่อน (Course Prerequisites)
CREATE TABLE IF NOT EXISTS course_prerequisites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    prerequisite_course_code VARCHAR(50) NOT NULL,
    prerequisite_course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_course_prereq UNIQUE (course_id, prerequisite_course_code)
);

-- 7. ตารางความเชื่อมโยง Course-PLO (Curriculum Mappings)
CREATE TABLE IF NOT EXISTS curriculum_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    plo_id UUID NOT NULL REFERENCES plos(id) ON DELETE CASCADE,
    responsibility_type VARCHAR(50) NOT NULL, 
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_course_plo_mapping UNIQUE (course_id, plo_id)
);

-- 8. สร้าง HNSW Index เร่งความเร็วการค้นหา Vector 1,024 มิติ
CREATE INDEX IF NOT EXISTS idx_courses_embedding_hnsw 
ON courses USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_plos_embedding_hnsw 
ON plos USING hnsw (embedding vector_cosine_ops);

-- 9. ผูก Triggers สำหรับอัปเดตเวลาอัตโนมัติ
DROP TRIGGER IF EXISTS update_curriculums_modtime ON curriculums;
CREATE TRIGGER update_curriculums_modtime
    BEFORE UPDATE ON curriculums
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_courses_modtime ON courses;
CREATE TRIGGER update_courses_modtime
    BEFORE UPDATE ON courses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_plos_modtime ON plos;
CREATE TRIGGER update_plos_modtime
    BEFORE UPDATE ON plos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_course_prerequisites_modtime ON course_prerequisites;
CREATE TRIGGER update_course_prerequisites_modtime
    BEFORE UPDATE ON course_prerequisites
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_curriculum_mappings_modtime ON curriculum_mappings;
CREATE TRIGGER update_curriculum_mappings_modtime
    BEFORE UPDATE ON curriculum_mappings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();