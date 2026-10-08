import { useEffect, useRef, useState } from 'react';
import * as api from '../services/api';

const FINISHED = ['completed', 'failed'];

/** ติดตามสถานะงานสกัดข้อมูล (poll ทุก 1.5 วินาที) */
export function usePipelineJob({ onComplete, onFail } = {}) {
  const [job, setJob] = useState(null);
  const callbacks = useRef({ onComplete, onFail });

  useEffect(() => {
    callbacks.current = { onComplete, onFail };
  });

  useEffect(() => {
    if (!job?.job_id || FINISHED.includes(job.status)) return undefined;
    const timer = window.setInterval(async () => {
      try {
        const res = await api.getJobStatus(job.job_id);
        setJob((prev) => ({ ...prev, ...res.data }));
        if (res.data.status === 'completed') callbacks.current.onComplete?.(res.data);
        if (res.data.status === 'failed') callbacks.current.onFail?.(res.data);
      } catch (err) {
        console.warn('กำลังติดตามสถานะงาน...', err);
      }
    }, 1500);
    return () => window.clearInterval(timer);
  }, [job?.job_id, job?.status]);

  return {
    job,
    isRunning: Boolean(job) && !FINISHED.includes(job.status),
    start: setJob,
    dismiss: () => setJob(null),
  };
}
