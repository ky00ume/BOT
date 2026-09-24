"""지역 탐험의 1회성 희귀 발견물 사건."""
from __future__ import annotations

EVENTS = {
 "셀루네 수정지": {"id":"selune_sussur_bloom","title":"🌙 마법을 삼키는 푸른 꽃","text":"달빛을 머금은 수정 사이에서 주변의 마력을 잠재우는 푸른 꽃 한 송이가 흔들립니다.","item":"sussur_bloom","item_name":"서서 꽃","choices":[("study","🔎 마력의 흐름을 읽는다"),("take","🧤 조심히 꺾는다"),("leave","🚶 그대로 둔다")]},
 "샤의 잔해 채집지": {"id":"shar_black_pearl","title":"🌑 그림자 웅덩이의 검은 진주","text":"무너진 제단 아래, 빛을 거의 반사하지 않는 검은 진주가 얕은 물속에 잠겨 있습니다.","item":"black_pearl","item_name":"검은 진주","choices":[("study","🕯️ 주변을 살핀다"),("take","🤲 손을 뻗는다"),("leave","🚶 물러난다")]},
}

def state_key(event): return f"rare_discovery:{event['id']}"
def available(player, zone):
    e=EVENTS.get(zone); return bool(e and not player._flags.get(state_key(e),{}).get("resolved"))
def resolve(player, zone, choice, *, rng):
    e=EVENTS[zone]; st=player._flags.setdefault(state_key(e),{})
    if st.get("resolved"): return {"text":"이미 이 발견은 결말이 났습니다.","resolved":True}
    if choice=="leave": return {"text":"위험을 감수하지 않고 물러났습니다. 발견물은 아직 그 자리에 있습니다.","resolved":False}
    dex=player.base_stats.get("dex",10); luck=player.base_stats.get("luck",5); intelligence=player.base_stats.get("int",10)
    chance=min(.94, (.58+intelligence*.015+luck*.008) if choice=="study" else (.42+dex*.018+luck*.008))
    if rng()<chance:
        if player.add_item(e['item'],1):
            st.update(resolved=True,outcome="found"); return {"text":f"✨ 위험을 피해 **{e['item_name']}**을 온전히 확보했습니다!","resolved":True,"reward":f"{e['item_name']} ×1"}
        return {"text":"가방에 자리가 없어 손대지 않고 돌아섰습니다.","resolved":False}
    st.update(resolved=True,outcome="lost")
    return {"text":"손을 대는 순간 주변의 기운이 요동칩니다. 발견물은 금이 가거나 어둠 속으로 사라졌습니다.","resolved":True,"lost":True}
