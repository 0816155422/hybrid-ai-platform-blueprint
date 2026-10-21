#!/usr/bin/env python3
"""
Phase Adapter Skeleton — โครงสร้างสคริปต์ Python สำหรับทุกเฟส
ทุกเฟสใช้โครงเดียวกัน แค่เปลี่ยน logic ใน do_work()

รูปแบบการทำงาน (5 ขั้นตอน):
1. PLAN — บันทึกแผนลง Checklist Log (ทำก่อนเรียกสคริปต์นี้)
2. validate_input() — ตรวจ input ผ่าน Master Adapter
3. do_work() — ประมวลผล/ทำงาน (ไม่มีการตรวจสอบในขั้นนี้)
4. validate_output() — ตรวจ output ผ่าน Master Adapter
5. บันทึกผลลง Checklist Log (ทำหลังสคริปต์เสร็จ)
"""

import json
import jsonschema
from datetime import datetime, timezone, timedelta

# === การตั้งค่าเฟส (แก้ตรงนี้สำหรับแต่ละเฟส) ===
PHASE_ID = "phase1"  # เปลี่ยนตามเฟส: phase0..phase6
SCHEMA_PATH = "templates/master-adapter.schema.json"
CHECKLOG_PATH = "logs/checklog.jsonl"
ACTOR = "ai:gpt-4o"  # หรือ user:xxx
BANGKOK_TZ = timezone(timedelta(hours=7))


def load_schema(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_record(record: dict, schema: dict) -> list:
    """ตรวจสอบ record กับ JSON Schema (Master Adapter)
    คืน list ของ error (ว่าง = ผ่าน)"""
    errors = []
    try:
        jsonschema.validate(instance=record, schema=schema)
    except jsonschema.ValidationError as e:
        errors.append(f"{e.json_path}: {e.message}")
    return errors


def log_to_checklog(entry: dict):
    """บันทึกลง Checklist Log (append-only JSONL)"""
    entry["timestamp"] = datetime.now(BANGKOK_TZ).isoformat()
    entry["entry_id"] = f"LOG-{datetime.now(BANGKOK_TZ).strftime('%Y%m%d')}-{entry.get('seq', '000')}"
    with open(CHECKLOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def validate_input(input_records: list, schema: dict) -> list:
    """ขั้นตอนที่ 2: ตรวจ input ผ่าน Master Adapter — ถ้ามีผิด หยุดทันที"""
    all_errors = []
    for rec in input_records:
        errs = validate_record(rec, schema)
        if errs:
            all_errors.append({rec.get("id", "unknown"): errs})
    return all_errors


def do_work(input_records: list) -> list:
    """ขั้นตอนที่ 3: ทำงานจริง — แก้ logic นี้ตามเฟส
    ⚠️ ห้ามตรวจสอบอะไรในขั้นนี้ ทำให้จบก่อน
    ⚠️ ห้ามเรียกเครื่องมือนอก Skill Set ของเฟสนี้
    ⚠️ ทุก output record ต้องมี derived_from ชี้ไปยัง input"""
    output_records = []
    for rec in input_records:
        # TODO: ใส่ logic การประมวลผลของเฟสนี้ที่นี่
        # ตัวอย่าง: เรียก LLM ผ่าน LiteLLM, เรียก tool, transform data
        processed = {
            "id": f"{PHASE_ID}-output-{rec['id']}",
            "phase": PHASE_ID,
            "derived_from": [rec["id"]],  # ⚠️ บังคับ: ต้องชี้กลับไป input
            "contributes_to": [],  # เติมทีหลังเมื่อส่งต่อไปเฟสถัดไป
            "timestamp": datetime.now(BANGKOK_TZ).isoformat(),
            "owner": ACTOR,
            "schema_version": "v1.0",
            "confidence": 0.9,  # TODO: ระบุความมั่นใจจริง ถ้า <0.7 ต้อง escalation
            "payload": {}  # TODO: ใส่ผลลัพธ์จริง
        }
        output_records.append(processed)
    return output_records


def validate_output(output_records: list, schema: dict) -> list:
    """ขั้นตอนที่ 4: ตรวจ output ผ่าน Master Adapter — ถ้ามีผิด ส่งกลับไปแก้"""
    all_errors = []
    for rec in output_records:
        errs = validate_record(rec, schema)
        if errs:
            all_errors.append({rec.get("id", "unknown"): errs})
        # ตรวจเพิ่มเติม: ทุก output ต้องมี derived_from ไม่ว่าง (ยกเว้นเฟส0)
        if PHASE_ID != "phase0" and not rec.get("derived_from"):
            all_errors.append({rec.get("id", "unknown"): "derived_from is required (provenance)"})
    return all_errors


def main():
    schema = load_schema(SCHEMA_PATH)

    # TODO: โหลด input records จากคลังข้อมูล (Silver/Gold ของเฟสก่อนหน้า)
    input_records = []  # โหลดจาก data/...

    # ขั้นตอนที่ 2: ตรวจ input
    input_errors = validate_input(input_records, schema)
    if input_errors:
        log_to_checklog({"phase_id": PHASE_ID, "actor": ACTOR, "entry_type": "CHECK",
                         "item": "validate_input", "status": "BLOCKED",
                         "blocker_reason": json.dumps(input_errors, ensure_ascii=False)})
        print("❌ Input validation failed:", input_errors)
        return 1

    # ขั้นตอนที่ 3: ทำงาน (ไม่มีการตรวจสอบ)
    output_records = do_work(input_records)

    # ขั้นตอนที่ 4: ตรวจ output
    output_errors = validate_output(output_records, schema)
    if output_errors:
        log_to_checklog({"phase_id": PHASE_ID, "actor": ACTOR, "entry_type": "CHECK",
                         "item": "validate_output", "status": "FAIL",
                         "blocker_reason": json.dumps(output_errors, ensure_ascii=False)})
        print("❌ Output validation failed:", output_errors)
        return 1

    # TODO: บันทึก output ลงคลังข้อมูล (data/silver/ หรือ data/gold/)

    # บันทึกผลสำเร็จ
    log_to_checklog({"phase_id": PHASE_ID, "actor": ACTOR, "entry_type": "CHECK",
                     "item": f"phase work complete ({len(output_records)} records)",
                     "status": "DONE", "links": [r["id"] for r in output_records]})
    print(f"✅ Phase {PHASE_ID} complete. {len(output_records)} records produced.")
    print("⏭️  Next: ส่ง output ให้ Gate ตรวจสอบ (ตัดสิน PASS/FAIL/BLOCKED)")
    return 0


if __name__ == "__main__":
    exit(main())
