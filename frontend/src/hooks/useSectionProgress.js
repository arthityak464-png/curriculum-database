import { useState } from 'react';

const SECTION_COUNT = 3;
const storageKey = (id) => `verification-sections:${id}`;

function read(id) {
  const empty = Array(SECTION_COUNT).fill(false);
  if (!id) return empty;
  try {
    const parsed = JSON.parse(window.localStorage.getItem(storageKey(id)) || 'null');
    return Array.isArray(parsed) && parsed.length === SECTION_COUNT ? parsed.map(Boolean) : empty;
  } catch {
    window.localStorage.removeItem(storageKey(id));
    return empty;
  }
}

/** ความคืบหน้าการตรวจทาน 3 ส่วน (เก็บในเบราว์เซอร์) */
export function useSectionProgress(id) {
  const [store, setStore] = useState(() => ({ id, done: read(id) }));
  const done = store.id === id ? store.done : read(id);

  const markDone = (index) => {
    const next = done.map((value, i) => (i === index ? true : value));
    if (id) window.localStorage.setItem(storageKey(id), JSON.stringify(next));
    setStore({ id, done: next });
    return next;
  };

  const clear = (targetId) => window.localStorage.removeItem(storageKey(targetId));

  return { done, markDone, clear };
}
