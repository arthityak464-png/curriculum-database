import { createContext, useContext } from 'react';

export const ToastContext = createContext({ showToast: () => {} });

/** ใช้แสดงข้อความแจ้งเตือนมุมจอ: showToast('บันทึกแล้ว', 'success' | 'error' | 'info') */
export const useToast = () => useContext(ToastContext);
