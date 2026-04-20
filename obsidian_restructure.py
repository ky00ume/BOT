#!/usr/bin/env python3
"""
Obsidian Vault - Karpathy LLM Wiki 방식 재편성 스크립트
대상 경로: D:\Obsidian Vault
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

VAULT_PATH = Path(r"D:\Obsidian Vault")

# 건드리지 않을 시스템/플러그인 폴더
SKIP = {".obsidian", ".smart-env", ".trash", "copilot", "hydrate-chats"}

# 기존 폴더 → 새 폴더 이동 매핑
FOLDER_MAP = {
    "Lilly room": "03_Lilly",
    "PRIVAT":     "04_PRIVAT",
    "WIKI":       "02_wiki",
}

INDEX_CONTENT = """\
# Obsidian Vault Index

> 업데이트: {date}

## 폴더 구조

| 폴더 | 용도 |
|------|------|
| `00_inbox/` | 빠른 메모, 미분류 노트 (여기서 시작) |
| `01_raw/` | 원본 자료 - **수정 금지** (스크랩, PDF, 링크 등) |
| `02_wiki/` | 정제된 지식 베이스 (raw를 읽고 AI가 정리) |
| `03_Lilly/` | Lilly 관련 노트 |
| `04_PRIVAT/` | 개인 기록 |

## 사용 규칙

1. 새 메모 → **00_inbox** 에 먼저 던져두기
2. 원본 자료 → **01_raw** 에 저장, 절대 수정 금지
3. 정리된 지식 → **02_wiki** 에 구조화된 문서로 작성
4. wiki 문서끼리 `[[링크]]` 로 연결하기

## Karpathy LLM Wiki 패턴

- raw: 소스 자료 (스크랩, 링크, PDF)
- wiki: AI가 raw를 읽고 재작성한 구조화 문서
- inbox → wiki 로 정제하는 흐름 유지
"""

LOG_CONTENT = """\
# 작업 로그

## {date}
- 볼트 구조 재편성 완료 (Karpathy LLM Wiki 패턴)
- 생성: 00_inbox, 01_raw, 02_wiki, 03_Lilly, 04_PRIVAT
- 기존: Lilly room → 03_Lilly, PRIVAT → 04_PRIVAT, WIKI → 02_wiki
- 루트의 .md 파일들 → 00_inbox 로 이동

"""


def print_tree():
    print(f"\n{'='*52}")
    print(f"  📂 {VAULT_PATH}")
    print(f"{'='*52}")
    for item in sorted(VAULT_PATH.iterdir()):
        if item.name.startswith("."):
            print(f"  [숨김]  {item.name}/")
        elif item.is_dir():
            md_count = len(list(item.rglob("*.md")))
            print(f"  📁  {item.name}/  ({md_count}개 노트)")
        else:
            print(f"  📄  {item.name}")
    print()


def create_folders():
    new_folders = ["00_inbox", "01_raw", "02_wiki", "03_Lilly", "04_PRIVAT"]
    print("── 새 폴더 생성")
    for name in new_folders:
        p = VAULT_PATH / name
        if not p.exists():
            p.mkdir()
            print(f"   ✅ {name}/")
        else:
            print(f"   ── {name}/  (이미 존재)")


def migrate_folders():
    print("\n── 기존 폴더 이동")
    for old, new in FOLDER_MAP.items():
        src = VAULT_PATH / old
        dst = VAULT_PATH / new
        if not src.exists():
            print(f"   ⏭  {old}/  (없음, 건너뜀)")
            continue
        if dst.exists():
            # 내용 병합
            for item in src.iterdir():
                dest_item = dst / item.name
                if not dest_item.exists():
                    shutil.move(str(item), str(dest_item))
            try:
                src.rmdir()
            except OSError:
                pass
            print(f"   🔀 {old}/ → {new}/  (병합)")
        else:
            src.rename(dst)
            print(f"   ✅ {old}/ → {new}/")


def move_loose_folder():
    """노선/ 폴더는 용도가 불명확하므로 inbox로 이동"""
    src = VAULT_PATH / "노선"
    if src.exists():
        dst = VAULT_PATH / "00_inbox" / "노선"
        if not dst.exists():
            shutil.move(str(src), str(dst))
            print(f"\n── 노선/ → 00_inbox/노선/  (용도 불명, inbox로 이동)")


def move_root_md_files():
    print("\n── 루트의 .md 파일 → 00_inbox/")
    inbox = VAULT_PATH / "00_inbox"
    moved = False
    for item in sorted(VAULT_PATH.iterdir()):
        if item.is_file() and item.suffix == ".md" and item.name not in ("index.md", "log.md"):
            dst = inbox / item.name
            if dst.exists():
                stem = item.stem
                dst = inbox / f"{stem}_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
            shutil.move(str(item), str(dst))
            print(f"   ✅ {item.name}")
            moved = True
    if not moved:
        print("   (이동할 파일 없음)")


def move_root_other_files():
    """루트의 기타 파일들(.base 등) → 00_inbox/"""
    inbox = VAULT_PATH / "00_inbox"
    for item in sorted(VAULT_PATH.iterdir()):
        if item.is_file() and item.name not in ("index.md", "log.md"):
            dst = inbox / item.name
            shutil.move(str(item), str(dst))
            print(f"   ✅ {item.name} → 00_inbox/")


def create_index_log():
    now = datetime.now().strftime("%Y-%m-%d")
    index = VAULT_PATH / "index.md"
    log   = VAULT_PATH / "log.md"

    if not index.exists():
        index.write_text(INDEX_CONTENT.format(date=now), encoding="utf-8")
        print(f"\n── index.md 생성")
    else:
        print(f"\n── index.md 이미 존재 (건너뜀)")

    if not log.exists():
        log.write_text(LOG_CONTENT.format(date=now), encoding="utf-8")
        print(f"── log.md 생성")
    else:
        existing = log.read_text(encoding="utf-8")
        log.write_text(LOG_CONTENT.format(date=now) + existing, encoding="utf-8")
        print(f"── log.md 업데이트")


def main():
    if not VAULT_PATH.exists():
        print(f"❌  볼트를 찾을 수 없어요: {VAULT_PATH}")
        print("    경로를 확인하고 VAULT_PATH 를 수정해주세요.")
        input("엔터를 눌러 종료...")
        return

    print("\n🗂   Obsidian Vault 재편성 — Karpathy LLM Wiki 패턴")
    print(f"    경로: {VAULT_PATH}")

    print("\n현재 구조:")
    print_tree()

    print("재편성 후 구조:")
    print(f"""
  📂 Obsidian Vault/
  ├── 📁 00_inbox/     ← 빠른 메모, 미분류
  ├── 📁 01_raw/       ← 원본 자료 (수정 금지)
  ├── 📁 02_wiki/      ← 정제된 지식 (기존 WIKI)
  ├── 📁 03_Lilly/     ← 기존 Lilly room
  ├── 📁 04_PRIVAT/    ← 기존 PRIVAT
  ├── 📄 index.md      ← 전체 목차
  └── 📄 log.md        ← 작업 이력
""")

    ans = input("진행하시겠습니까? (y/n): ").strip().lower()
    if ans != "y":
        print("취소됨.")
        input("엔터를 눌러 종료...")
        return

    print()
    create_folders()
    migrate_folders()
    move_loose_folder()
    move_root_md_files()
    move_root_other_files()
    create_index_log()

    print("\n✅  완료! 최종 구조:")
    print_tree()
    input("엔터를 눌러 종료...")


if __name__ == "__main__":
    main()
