# ส่วนที่ 7 — ภาษา/รูปแบบการเขียน: เลือกให้ตรงงาน ประหยัด token

## หลักการ: อย่าใช้ภาษามนุษย์ (natural language) กับทุกอย่าง

การเขียน prompt ยาวๆ เป็นภาษามนุษย์ทุกครั้ง **กิน token มาก และมีความกำกวม** (AI ต้องเดาใจ) — ระบบนี้ใช้หลักการ **"เลือกรูปแบบให้ตรงกับงาน"**: สิ่งที่เป็นโครงสร้างใช้ declarative config (YAML/JSON) สิ่งที่เป็น logic ซ้ำๆ เขียนเป็นสคริปต์ (Python/JS) ภาษามนุษย์ใช้แค่ที่จำเป็นจริงๆ

---

## ตาราง: ส่วนของระบบ × ภาษา/รูปแบบที่แนะนำ

| ส่วนของระบบ | ภาษา/รูปแบบ | เหตุผล | ตัวอย่างไฟล์ |
|---|---|---|---|
| **Master Canonical Adapter** (schema บังคับ) | **JSON Schema** | declarative, validate อัตโนมัติได้, กระชับมาก | `templates/master-adapter.schema.json` |
| **Gate criteria + Checklist template** | **YAML** | อ่านง่ายสำหรับคน, structured, version control ได้ | `templates/gate-criteria.example.yaml` |
| **Tool/Skill Registry + scope** | **YAML / CSV** | รายการเครื่องมือ + สิทธิ์ กำหนดครั้งเดียว | `registries/tool-skill-registry.csv` |
| **Tool call schemas** | **JSON Schema / OpenAPI** | กันพารามิเตอร์ผิด (ลด tool error จาก 14% → 2.1%) | ใน Tool Registry |
| **Checklist Log (append-only)** | **JSONL** (JSON ต่อบรรทัด) | เขียนต่อเนื่องได้, query ได้, ไม่เสี่ยหาย | `templates/checklog.example.jsonl` |
| **Provenance / link ไป-กลับ** | **JSON-LD + PROV-O** | มาตรฐานสากล, machine-readable | ในทุก data record |
| **Phase logic / transformation / data processing** | **Python** (หรือ JS/TS) | เขียนเป็นสคริปต์ reusable รันครั้งเดียว ไม่ต้อง prompt AI คิดใหม่ | `templates/phase-adapter-skeleton.py` |
| **AI prompt template** | **Jinja / Moustache template** | มีตัวแปร เติมแค่ค่า ไม่ต้องเขียน prompt ยาวซ้ำๆ | `templates/prompt-template.jinja` |
| **Mobile/native component (ถ้ามี)** | **Swift / Kotlin** | ใช้เฉพาะส่วนที่ต้อง native (ถ้ามีจริงๆ) | — |
| **ข้อมูลตาราง / registry** | **CSV** (เปิดได้ใน Excel/Google Sheet) | คนและเครื่องอ่านได้, version control ได้ | โฟลเดอร์ `registries/` |
| **ภาษามนุษย์ (Natural Language)** | ใช้ **เฉพาะ 3 ที่** เท่านั้น: ① input จากผู้ใช้ ② สรุปผลตอนส่งมอบ ③ สิ่งที่ไม่มีโครงสร้างจริงๆ | ที่เหลือห้ามใช้ เพื่อประหยัด token และลดความกำกวม | — |

---

## กลไกประหยัด token (ทำไมวิธีนี้ดีกว่า prompt ยาวๆ)

| วิธีเดิม (prompt ยาวทุกครั้ง) | วิธีใหม่ (config + script + template) | ประหยัดได้ |
|---|---|---|
| ทุกครั้งเขียนอธิบายว่า "ต้องทำตามขั้นตอน X Y Z" | เก็บเป็น YAML config อ่านครั้งเดียว | ~80-90% token สำหรับคำสั่ง |
| ทุกครั้งให้ AI คิด logic การประมวลผลใหม่ | เขียน Python script รันบนเครื่อง (ไม่เสีย token) | 100% (ไม่ต้องใช้ AI สำหรับ logic ที่แน่นอน) |
| ทุกครั้งเขียน prompt เต็ม | ใช้ Jinja template เติมแค่ตัวแปร | ~70% token สำหรับ prompt |
| AI เรียกเครื่องมือโดยเดา | Schema บังคับพารามิเตอร์ (ลดความผิด ไม่ต้อง retry) | ลด retry ซึ่งกิน token เพิ่ม |

---

## ตัวอย่าง: การทำงานร่วมกัน (Composition) ของหลายรูปแบบ

```
1. YAML config (กำหนดเฟส + skill set + gate criteria)
        ↓ อ่านเข้าโปรแกรม
2. Python script (ประมวลผล logic ที่แน่นอน: จัดระเบียบไฟล์, validate, transform)
        ↓ เรียก
3. Jinja template (เติมตัวแปร → สร้าง prompt สำหรับ AI เฉพาะส่วนที่ต้องคิด)
        ↓ ส่งให้ AI (LLM)
4. AI คืนผลลัพธ์ (เฉพาะส่วนที่ต้องใช้ความคิดสร้างสรรค์/วิเคราะห์)
        ↓ ผ่าน
5. JSON Schema (Master Adapter validate รูปแบบ)
        ↓ ถ้าผ่าน
6. Gate (ตรวจ cross-phase consistency ตาม YAML criteria)
        ↓ ผลบันทึก
7. JSONL (Checklist Log append-only)
        ↓ ตอนส่งมอบ
8. Natural language summary (แค่ขั้นสุดท้าย สำหรับคนอ่าน)
```

**สังเกต:** AI (LLM) ถูกเรียกใช้แค่ขั้นที่ 4 เท่านั้น — ส่วนอื่นๆ เป็นโค้ด/config ที่รันบนเครื่องไม่เสีย token และทำงานได้แม่นยำกว่า

---

## กฎการเลือกภาษา/รูปแบบ (จำให้ได้)
1. **ถ้าเป็น "การกำหนดค่า/โครงสร้าง"** → ใช้ declarative (YAML/JSON/JSON Schema) — ไม่ต้องเขียนเป็นภาษามนุษย์
2. **ถ้าเป็น "logic ที่ทำซ้ำได้และแน่นอน"** → เขียนเป็นสคริปต์ (Python/JS) — ไม่ต้องให้ AI คิด
3. **ถ้าเป็น "prompt สำหรับ AI"** → ใช้ template (Jinja) — มีตัวแปร เติมแค่ค่า
4. **ถ้าเป็น "บันทึก/ประวัติ"** → ใช้ JSONL/CSV — structured, query ได้
5. **ถ้าเป็น "การสื่อสารกับคน"** (input ผู้ใช้, สรุปผล) → ถึงจะใช้ภาษามนุษย์

---

## สิ่งที่ต้องจำ
- **อย่าใช้ AI สำหรับสิ่งที่โค้ดทำได้ดีกว่า** — AI ใช้สำหรับสิ่งที่ต้องความคิดสร้างสรรค์/วิเคราะห์/เข้าใจภาษามนุษย์เท่านั้น
- **ทุกอย่างที่เป็นโครงสร้างต้องเป็นไฟล์ config** — ไม่ฝังอยู่ใน prompt (จะแก้ยาก และกิน token)
- **template มีตัวแปร** — อย่าเขียน prompt เต็มซ้ำๆ ทุกครั้ง
- **เปลี่ยนภาษา/รูปแบบได้ตลอด** — ถ้าเห็นว่ารูปแบบไหนไม่เหมาะสม เปลี่ยนได้ (ทุกอย่างเป็น adapter)
