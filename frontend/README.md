# Frontend — ระบบฐานข้อมูลหลักสูตร มคอ.2 (มหาวิทยาลัยกาฬสินธุ์)

React 19 + Vite + Tailwind CSS v4 (ไม่มี dependency เพิ่มจากเดิม)

```bash
npm install
npm run dev      # http://localhost:5173 (proxy /api → http://127.0.0.1:8000)
npm run build
```

## โครงสร้าง

```
src/
├── App.jsx                  # รวมหน้า + routing + อัปโหลด/ลบ
├── index.css                # Design tokens สีมหาวิทยาลัย (@theme)
├── assets/ksu-emblem.png    # ตรามหาวิทยาลัย
├── services/api.js          # เรียก Backend ทั้งหมด
├── lib/
│   ├── router.js            # hash router: #/ #/search #/catalog/:id #/studio/:id
│   └── curriculum.js        # ฟังก์ชันจัดรูปข้อมูล (ไม่มี React)
├── context/toast.js         # useToast()
├── hooks/                   # โหลดข้อมูลและสถานะ
│   ├── useCurriculums.js
│   ├── useCurriculumBundle.js
│   ├── usePipelineJob.js
│   └── useSectionProgress.js
├── components/
│   ├── ui/                  # ปุ่ม, Badge, Card, Modal, Select ฯลฯ ใช้ทั้งระบบ
│   ├── layout/              # AppShell, Sidebar, BrandLogo, PageHeader
│   └── curriculum/          # ชิ้นส่วนเฉพาะหลักสูตร: PloMatrix, CourseCard, UploadDialog ฯลฯ
└── pages/
    ├── dashboard/           # ภาพรวม + คิวเอกสาร
    ├── search/              # ค้นหาด้วย AI
    ├── catalog/             # คลังหลักสูตร
    └── studio/              # ห้องตรวจทาน (PDF คู่กับข้อมูลที่สกัดได้)
```

## สีและตัวอักษร

ใช้คลาสจาก token ได้เลย เช่น `bg-ksu-navy`, `text-ksu-blue`, `bg-ksu-mist`, `text-muted`, `border-line`,
`bg-warn-bg text-warn-fg` (ต้องตรวจ), `bg-ok-bg text-ok-fg` (ผ่าน) — แก้ค่าสีที่เดียวใน `src/index.css`
