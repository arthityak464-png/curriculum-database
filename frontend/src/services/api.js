import axios from 'axios';

// ใช้ Relative Path '/api/v1' เพื่อให้วิ่งผ่าน Vite Proxy ไปหาพอร์ต 8000
export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

/** ดึงข้อความ error ที่อ่านรู้เรื่องจาก response ของ FastAPI */
export const getErrorMessage = (err) =>
  err?.response?.data?.detail || err?.message || 'เกิดข้อผิดพลาดที่ไม่ทราบสาเหตุ';

// ---------- Curriculums ----------
export const getCurriculums = () => apiClient.get('/curriculums');
export const getCurriculumDetail = (id) => apiClient.get(`/curriculums/${id}`);
export const uploadCurriculum = (formData, force = false) =>
  apiClient.post('/curriculums/upload', formData, {
    params: { force },
    headers: { 'Content-Type': 'multipart/form-data' },
  });
export const updateCurriculum = (id, data) => apiClient.put(`/curriculums/${id}`, data);
export const commitCurriculum = (id) => apiClient.post(`/curriculums/${id}/commit`);
export const deleteCurriculum = (id) => apiClient.delete(`/curriculums/${id}`);
export const exportCurriculumJson = (id) => apiClient.get(`/curriculums/${id}/export/json`);
export const reindexCurriculum = (id) => apiClient.post(`/curriculums/${id}/embeddings/reindex`);

// ---------- PDF & Jobs ----------
export const getCurriculumPdfUrl = (id) => `${API_BASE_URL}/curriculums/${id}/pdf`;
export const getJobStatus = (jobId) => apiClient.get(`/jobs/${jobId}`);

// ---------- Courses & Mappings ----------
export const getCurriculumCourses = (id, group = null) =>
  apiClient.get(`/curriculums/${id}/courses`, { params: group ? { course_group: group } : {} });
export const getCourseDetail = (code, curriculumId = null) =>
  apiClient.get(`/courses/${code}`, { params: curriculumId ? { curriculum_id: curriculumId } : {} });
export const updateCourse = (code, data, curriculumId = null) =>
  apiClient.put(`/courses/${code}`, data, { params: curriculumId ? { curriculum_id: curriculumId } : {} });
export const getCurriculumPlos = (id) => apiClient.get(`/curriculums/${id}/plos`);
export const getCurriculumMapping = (id) => apiClient.get(`/curriculums/${id}/mapping`);

// ---------- AI Semantic Search ----------
/**
 * @param {string} query
 * @param {{limit?: number, curriculumId?: string, courseGroup?: string, signal?: AbortSignal}} options
 */
export const searchCourses = (query, { limit = 10, curriculumId, courseGroup, signal } = {}) =>
  apiClient.get('/courses/search', {
    params: {
      query,
      limit,
      ...(curriculumId ? { curriculum_id: curriculumId } : {}),
      ...(courseGroup ? { course_group: courseGroup } : {}),
    },
    signal,
  });

export default apiClient;
