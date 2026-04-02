"""
fix_portrait_bg.py — NPC 초상화 흰색/단색 배경 투명화 유틸리티
사용법: python3 fix_portrait_bg.py static/portraits/npc/팅커벨.png
"""
import sys
import os
from PIL import Image


def remove_white_background(input_path: str, output_path: str = None,
                             threshold: int = 230, feather_range: int = 50):
    """흰색/밝은 단색 배경을 투명하게 변환."""
    if output_path is None:
        output_path = input_path

    img = Image.open(input_path).convert("RGBA")
    pixels = img.load()
    w, h = img.size

    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            whiteness = min(r, g, b)  # 모든 채널이 높으면 흰색/회색

            if whiteness >= threshold:
                pixels[x, y] = (r, g, b, 0)
            elif whiteness >= threshold - feather_range:
                # 가장자리 부드럽게: 알파 값을 점진적으로 낮춤
                ratio = (threshold - whiteness) / feather_range
                new_a = int(a * ratio)
                pixels[x, y] = (r, g, b, new_a)

    img.save(output_path, "PNG")
    print(f"완료: {output_path}")


def process_all_portraits(portrait_dir: str = "static/portraits/npc"):
    """디렉토리 내 모든 NPC 초상화의 배경 상태를 확인."""
    for fname in sorted(os.listdir(portrait_dir)):
        if not fname.endswith(".png"):
            continue
        path = os.path.join(portrait_dir, fname)
        img = Image.open(path).convert("RGBA")
        # 코너 픽셀 알파 확인
        corners = [(0, 0), (img.width - 1, 0),
                   (0, img.height - 1), (img.width - 1, img.height - 1)]
        max_corner_alpha = max(img.getpixel(c)[3] for c in corners)
        if max_corner_alpha > 10:
            print(f"[배경 필요] {fname} — 코너 알파={max_corner_alpha}")
        else:
            print(f"[투명 OK ] {fname}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python3 fix_portrait_bg.py <이미지 경로>")
        print("       python3 fix_portrait_bg.py --check  (전체 초상화 상태 확인)")
        sys.exit(1)

    if sys.argv[1] == "--check":
        process_all_portraits()
    else:
        path = sys.argv[1]
        if not os.path.isfile(path):
            print(f"파일 없음: {path}")
            sys.exit(1)
        remove_white_background(path)
