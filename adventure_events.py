"""사냥 중 끼어드는 지역별 무사수행식 선택 이벤트."""
from __future__ import annotations
import random

DREAD_HOLLOW_EVENTS = [
    {"id":"cry_in_fog","title":"🌫️ 안개 속 울음소리","text":"수서 나무 너머에서 작은 울음소리가 들립니다.","choices":[("track","🔍 흔적을 살핀다"),("guard","⚔️ 무기를 준비한다"),("leave","🚶 지나친다")]},
    {"id":"webbed_cache","title":"🕸️ 거미줄에 감긴 보따리","text":"굵은 거미줄 사이로 오래된 탐험가의 보따리가 보입니다.","choices":[("study","📖 거미줄을 관찰한다"),("cut","🗡️ 보따리를 꺼낸다"),("leave","🚶 건드리지 않는다")]},
    {"id":"glow_grove","title":"🍄 푸른 발광 군락","text":"평소보다 밝은 버섯 군락이 길 한쪽을 비춥니다.","choices":[("gather","🌿 조심히 채집한다"),("rest","✨ 빛 아래서 쉰다"),("leave","🚶 계속 간다")]},
]

EVENTS_BY_ZONE={"드레드 할로우":DREAD_HOLLOW_EVENTS}

def roll_adventure_event(zone:str, *, rng=random.random):
    pool=EVENTS_BY_ZONE.get(zone,[])
    if not pool or rng() >= 0.28: return None
    return random.choice(pool)

def resolve_adventure_event(player,event_id:str,choice:str,*,rng=random.random)->dict:
    dex=player.base_stats.get("dex",10); luck=player.base_stats.get("luck",5)
    if choice=="leave": return {"text":"위험을 피하고 원래 길로 돌아왔습니다.","battle":False}
    if event_id=="cry_in_fog":
        if choice=="track":
            known=getattr(player,"_flags",{}).get("collection_milestones",[]) or []
            good=rng() < min(.85,.45+dex*.015)
            return {"text":"발자국과 끊어진 거미줄을 읽어 위험을 먼저 알아챘습니다." if good else "흔적을 쫓다 숨어 있던 포식자를 건드렸습니다.","battle":not good,"advantage":good}
        return {"text":"기척이 가까워집니다. 준비한 채로 적과 마주칩니다.","battle":True,"advantage":True}
    if event_id=="webbed_cache":
        if choice=="study":
            player.base_stats["dex"] = player.base_stats.get("dex",10)+1 if rng()<.08 else player.base_stats.get("dex",10)
            return {"text":"거미줄의 진동과 매듭을 관찰했습니다. 다음에는 매복을 더 빨리 알아볼 수 있을 것 같습니다.","battle":False}
        good=rng() < min(.80,.35+luck*.02)
        if good:
            player.add_item("spider_web",1); return {"text":"보따리를 무사히 꺼냈습니다. 쓸 만한 거미줄을 챙겼습니다.","battle":False,"reward":"거미줄 ×1"}
        return {"text":"거미줄이 크게 흔들립니다. 주인이 돌아왔습니다!","battle":True}
    if event_id=="glow_grove":
        if choice=="gather":
            player.add_item("glow_mushroom",1); return {"text":"빛을 잃지 않게 밑동을 살려 발광버섯을 채집했습니다.","battle":False,"reward":"발광버섯 ×1"}
        if choice=="rest":
            before=player.energy; player.restore_energy(8); return {"text":f"푸른 빛 아래 잠시 쉬었습니다. 기력 +{player.energy-before}.","battle":False}
    return {"text":"아무 일도 일어나지 않았습니다.","battle":False}
