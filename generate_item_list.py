"""generate_item_list.py — ALL_ITEMS를 CSV로 추출하는 스크립트 + 봇 커맨드 헬퍼"""
import csv
import io
from items import ALL_ITEMS


def generate_csv_buffer() -> io.BytesIO:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["아이템ID", "이름", "타입", "등급", "가격", "설명"])
    for item_id, data in sorted(ALL_ITEMS.items()):
        writer.writerow([
            item_id,
            data.get("name", ""),
            data.get("type", ""),
            data.get("grade", "Normal"),
            data.get("price", 0),
            data.get("desc", ""),
        ])
    buf = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    buf.seek(0)
    return buf


if __name__ == "__main__":
    buf = generate_csv_buffer()
    with open("item_list.csv", "wb") as f:
        f.write(buf.read())
    print("item_list.csv 생성 완료!")
