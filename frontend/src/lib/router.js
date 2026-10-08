import { useEffect, useState } from 'react';

/**
 * Router แบบ hash เล็ก ๆ (ไม่ต้องเพิ่ม dependency)
 *   #/                 → ภาพรวม
 *   #/search?q=...     → ค้นหาด้วย AI
 *   #/catalog/:id      → คลังหลักสูตร
 *   #/studio/:id       → ห้องตรวจทาน
 */
function parseHash() {
  const raw = window.location.hash.replace(/^#/, '') || '/';
  const [path, queryString = ''] = raw.split('?');
  const segments = path.split('/').filter(Boolean);
  return {
    page: segments[0] || 'dashboard',
    id: segments[1] ? decodeURIComponent(segments[1]) : '',
    params: new URLSearchParams(queryString),
  };
}

export function useHashRoute() {
  const [route, setRoute] = useState(parseHash);
  useEffect(() => {
    const onChange = () => {
      setRoute(parseHash());
      window.scrollTo({ top: 0 });
    };
    window.addEventListener('hashchange', onChange);
    return () => window.removeEventListener('hashchange', onChange);
  }, []);
  return route;
}

export const paths = {
  dashboard: () => '#/',
  search: (query) => (query ? `#/search?q=${encodeURIComponent(query)}` : '#/search'),
  catalog: (id) => (id ? `#/catalog/${encodeURIComponent(id)}` : '#/catalog'),
  studio: (id) => (id ? `#/studio/${encodeURIComponent(id)}` : '#/studio'),
};

export function navigate(href) {
  window.location.hash = href.replace(/^#/, '');
}
