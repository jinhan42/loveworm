#!/bin/bash
# DB 스키마 마이그레이션 스크립트

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DB_FILE="$PROJECT_DIR/loveworm.db"
PYTHON="$PROJECT_DIR/backend/venv/bin/python3"

if [ ! -f "$DB_FILE" ]; then
  echo "DB 파일이 없습니다: $DB_FILE"
  echo "서비스를 한 번 실행하면 자동 생성됩니다."
  exit 0
fi

echo "=== DB 마이그레이션 시작: $DB_FILE ==="

TMPPY=$(mktemp /tmp/migrate_XXXXXX.py)

cat > "$TMPPY" << 'PYEOF'
import sqlite3, sys

db_path = sys.argv[1]
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("PRAGMA table_info(heat_exchanger_records)")
hx_cols = [r[1] for r in cur.fetchall()]
cur.execute("PRAGMA table_info(immersion_tank_records)")
imm_cols = [r[1] for r in cur.fetchall()]

print("heat_exchanger_records 현재 컬럼:", hx_cols)
print("immersion_tank_records 현재 컬럼:", imm_cols)

if 'pipe_temp' not in hx_cols:
    cur.execute("ALTER TABLE heat_exchanger_records ADD COLUMN pipe_temp REAL")
    print("v heat_exchanger_records.pipe_temp 컬럼 추가")
else:
    print("- heat_exchanger_records.pipe_temp 이미 존재")

needs_migration = 'oil_flow' in imm_cols or 'flow_upper' not in imm_cols or 'flow_lower' not in imm_cols

if needs_migration:
    print("immersion_tank_records 스키마 재구성 중...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS immersion_tank_records_new (
            id INTEGER PRIMARY KEY,
            temp_upper REAL,
            temp_lower REAL,
            flow_upper REAL,
            flow_lower REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    old_flow = 'oil_flow' if 'oil_flow' in imm_cols else ('flow_upper' if 'flow_upper' in imm_cols else None)
    if old_flow:
        cur.execute("""
            INSERT INTO immersion_tank_records_new (id, temp_upper, temp_lower, flow_upper, timestamp)
            SELECT id, temp_upper, temp_lower, {}, timestamp FROM immersion_tank_records
        """.format(old_flow))
    else:
        cur.execute("""
            INSERT INTO immersion_tank_records_new (id, temp_upper, temp_lower, timestamp)
            SELECT id, temp_upper, temp_lower, timestamp FROM immersion_tank_records
        """)
    cur.execute("DROP TABLE immersion_tank_records")
    cur.execute("ALTER TABLE immersion_tank_records_new RENAME TO immersion_tank_records")
    print("v immersion_tank_records 스키마 업데이트 완료")
else:
    print("- immersion_tank_records 스키마 이미 최신")

cur.execute("PRAGMA table_info(pdu_records)")
pdu_cols = [r[1] for r in cur.fetchall()]
print("pdu_records 현재 컬럼:", pdu_cols)

pdu_new_columns = {
    "unit": "TEXT",
    "voltage": "REAL",
    "current": "REAL",
    "power_factor": "REAL",
    "load_rate": "REAL",
    "temp1": "REAL",
    "temp2": "REAL",
    "temp3_door": "REAL",
    "humidity": "REAL",
    "kwh": "REAL",
    "alarm": "INTEGER",
}
for col, coltype in pdu_new_columns.items():
    if col not in pdu_cols:
        cur.execute(f"ALTER TABLE pdu_records ADD COLUMN {col} {coltype}")
        print(f"v pdu_records.{col} 컬럼 추가")
    else:
        print(f"- pdu_records.{col} 이미 존재")

conn.commit()
conn.close()
print("=== 마이그레이션 완료 ===")
PYEOF

$PYTHON "$TMPPY" "$DB_FILE"
rm -f "$TMPPY"
