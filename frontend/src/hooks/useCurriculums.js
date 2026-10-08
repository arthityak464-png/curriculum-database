import { useCallback, useEffect, useState } from 'react';
import * as api from '../services/api';

const fetchList = async () => {
  const res = await api.getCurriculums();
  return res.data?.data || [];
};

/** รายการหลักสูตรทั้งหมด + ฟังก์ชันรีเฟรช */
export function useCurriculums() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const apply = useCallback((promise) =>
    promise
      .then((list) => {
        setItems(list);
        setError('');
        return list;
      })
      .catch((err) => {
        setError(api.getErrorMessage(err));
        return [];
      })
      .finally(() => setLoading(false)), []);

  useEffect(() => {
    apply(fetchList());
  }, [apply]);

  const refresh = useCallback(() => {
    setLoading(true);
    return apply(fetchList());
  }, [apply]);

  /** อัปเดตรายการในหน่วยความจำทันที (เช่น หลังอนุมัติ) โดยไม่ต้องโหลดใหม่ */
  const patch = useCallback((id, changes) => {
    setItems((prev) => prev.map((item) => (item.id === id ? { ...item, ...changes } : item)));
  }, []);

  return { items, loading, error, refresh, patch };
}
