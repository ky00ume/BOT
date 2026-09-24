"""비버뱅 군락의 1회성 공작버섯 구조 이벤트."""
from __future__ import annotations

EVENT_ID = "bibberbang_noblestalk_rescue"

def event_available(player) -> bool:
    return not player._flags.get(EVENT_ID, {}).get("resolved", False)

def event_payload() -> dict:
    return {"id": EVENT_ID, "title":"💥 비버뱅 사이의 공작버섯", "text":"부푼 비버뱅 사이에 희귀한 공작버섯이 보입니다. 조금만 잘못 건드려도 포자 연쇄 폭발이 일어날 것 같습니다.", "choices":[("careful","🧤 천천히 길을 만든다"),("dash","🏃 단숨에 낚아챈다"),("burn","🔥 불로 길을 연다"),("leave","🚶 물러난다")]}

def resolve(player, choice: str, *, rng) -> dict:
    state=player._flags.setdefault(EVENT_ID,{})
    if state.get("resolved"): return {"text":"이미 이곳의 공작버섯 사건은 끝났습니다.","resolved":True}
    dex=player.base_stats.get("dex",10); luck=player.base_stats.get("luck",5)
    if choice=="leave": return {"text":"비버뱅을 건드리지 않고 물러났습니다. 아직 공작버섯은 그 자리에 있습니다.","resolved":False}
    if choice=="burn":
        state.update(resolved=True,outcome="destroyed")
        return {"text":"🔥 불꽃이 비버뱅을 건드리자 연쇄 폭발이 터졌습니다. 길은 열렸지만 공작버섯도 재가 되어 사라졌습니다.","resolved":True,"destroyed":True}
    chance=min(.92,(.48+dex*.018) if choice=="careful" else (.28+dex*.015+luck*.01))
    if rng() < chance:
        if player.add_item("noblestalk",1):
            state.update(resolved=True,outcome="saved")
            return {"text":"🍄 포자 주머니 사이를 무사히 통과해 공작버섯을 온전히 회수했습니다!","resolved":True,"reward":"공작버섯 ×1"}
        return {"text":"공작버섯까지 닿았지만 가방이 가득 찼습니다. 버섯은 아직 그 자리에 있습니다.","resolved":False}
    state.update(resolved=True,outcome="destroyed")
    return {"text":"💥 발밑의 비버뱅 하나가 터지며 연쇄 폭발이 번졌습니다. 공작버섯은 포자와 함께 사라졌습니다.","resolved":True,"destroyed":True}
