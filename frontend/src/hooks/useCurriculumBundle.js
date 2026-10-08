import { useCallback, useEffect, useState } from 'react';
import * as api from '../services/api';

const EMPTY_PLOS = { main_plos: [], sub_plos: [], display_plos: [] };
const EMPTY = { id: '', detail: null, courses: [], plos: EMPTY_PLOS, mapping: [], error: '' };

async function fetchBundle(id) {
  const [detail, courses, plos, mapping] = await Promise.allSettled([
    api.getCurriculumDetail(id),
    api.getCurriculumCourses(id),
    api.getCurriculumPlos(id),
    api.getCurriculumMapping(id),
  ]);
  return {
    id,
    detail: detail.status === 'fulfilled' ? detail.value.data : null,
    courses: courses.status === 'fulfilled' ? courses.value.data?.data || [] : [],
    plos: plos.status === 'fulfilled' ? plos.value.data || EMPTY_PLOS : EMPTY_PLOS,
    mapping: mapping.status === 'fulfilled' ? mapping.value.data?.data || [] : [],
    error: detail.status === 'rejected' ? api.getErrorMessage(detail.reason) : '',
  };
}

/** ข้อมูลครบชุดของหลักสูตรหนึ่ง: รายละเอียด, รายวิชา, PLO, ตาราง mapping */
export function useCurriculumBundle(id) {
  const [state, setState] = useState(EMPTY);

  useEffect(() => {
    if (!id) return undefined;
    let active = true;
    fetchBundle(id).then((data) => {
      if (active) setState(data);
    });
    return () => {
      active = false;
    };
  }, [id]);

  const reload = useCallback(async () => {
    if (!id) return;
    setState(await fetchBundle(id));
  }, [id]);

  const setDetail = useCallback((updater) => {
    setState((prev) => ({
      ...prev,
      detail: typeof updater === 'function' ? updater(prev.detail) : updater,
    }));
  }, []);

  const current = state.id === id ? state : { ...EMPTY, id };
  return { ...current, loading: Boolean(id) && state.id !== id, reload, setDetail };
}
