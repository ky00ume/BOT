#!/usr/bin/env python3
"""
recover_affinity.py — players_backup 테이블에서 호감도 데이터를 복구합니다.

사용법:
    python tools/recover_affinity.py          # 미리보기 (실제 복구 안 함)
    python tools/recover_affinity.py --apply  # 실제로 복구 적용
"""
import sys
import os
import json
import argparse

# 봇 루트를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_connection, DB_PATH


def find_best_backup(user_id: int = 0):
    """players_backup에서 affinity 데이터가 실제로 있는 가장 최근 백업을 찾습니다."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT backup_id, backed_at, data
            FROM players_backup
            WHERE user_id = ?
            ORDER BY backup_id DESC
        """, (user_id,))
        rows = cursor.fetchall()
    finally:
        conn.close()

    if not rows:
        print(f"[복구] players_backup 에 user_id={user_id} 데이터가 없습니다.")
        return None

    print(f"[복구] 백업 {len(rows)}개 발견. 호감도 데이터 검색 중...\n")

    for row in rows:
        try:
            data = json.loads(row["data"])
        except Exception:
            continue

        affinity_raw = data.get("affinity_data", "{}")
        try:
            aff = json.loads(affinity_raw) if isinstance(affinity_raw, str) else affinity_raw
        except Exception:
            aff = {}

        affinities = aff.get("affinities", {})
        if affinities:
            print(f"  ✅ backup_id={row['backup_id']}  backed_at={row['backed_at']}")
            print(f"     NPC 수: {len(affinities)}개")
            for npc, pts in affinities.items():
                print(f"       {npc}: {pts}pt")
            print()
            return row["backup_id"], aff

        else:
            print(f"  ❌ backup_id={row['backup_id']}  backed_at={row['backed_at']}  (호감도 없음)")

    print("\n[복구] 호감도가 있는 백업을 찾지 못했습니다.")
    return None


def apply_recovery(backup_id: int, aff_data: dict, user_id: int = 0):
    """찾은 호감도 데이터를 현재 players 행에 적용합니다."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        affinity_json = json.dumps(aff_data, ensure_ascii=False)
        cursor.execute(
            "UPDATE players SET affinity_data = ? WHERE user_id = ?",
            (affinity_json, user_id)
        )
        if cursor.rowcount == 0:
            print(f"[복구] user_id={user_id} 행이 players 테이블에 없습니다.")
            return False
        conn.commit()
        print(f"[복구] ✅ backup_id={backup_id} 의 호감도를 현재 DB에 적용했습니다.")
        return True
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="호감도 데이터 복구 도구")
    parser.add_argument("--apply",   action="store_true", help="실제로 복구를 적용합니다 (기본: 미리보기만)")
    parser.add_argument("--user-id", type=int, default=0, help="복구할 user_id (기본: 0)")
    args = parser.parse_args()

    print(f"DB 경로: {DB_PATH}\n")

    result = find_best_backup(args.user_id)
    if result is None:
        sys.exit(1)

    backup_id, aff_data = result

    if args.apply:
        apply_recovery(backup_id, aff_data, args.user_id)
    else:
        print("[미리보기] 실제로 적용하려면 --apply 옵션을 추가하세요.")
        print("           python tools/recover_affinity.py --apply")


if __name__ == "__main__":
    main()
