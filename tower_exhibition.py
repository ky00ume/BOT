"""비전의 탑 전시관: 돌파 퀘스트 유일품을 영구 전시하고 토템 효과를 부여한다."""
from __future__ import annotations

EXHIBITS = {
    "star_diamond": {"name":"별빛을 품은 다이아몬드","emoji":"💎","item_id":"quest_star_diamond","set":"지하의 기억","origin":"채광 A→9 돌파","desc":"깊은 광맥에서 직접 찾아낸, 내부에 별빛 같은 균열이 흐르는 다이아몬드."},
    "sussur_specimen": {"name":"수서꽃 표본","emoji":"🌸","item_id":"quest_sussur_specimen","set":"비전 연구","origin":"연금술 C→B 돌파","desc":"반마법 성질을 잃지 않도록 봉인한 수서꽃 표본."},
    "noblestalk_specimen": {"name":"공작버섯 표본","emoji":"🍄","item_id":"quest_noblestalk_specimen","set":"이계 식물 표본","origin":"채집 B→A 돌파","desc":"비버뱅 군락에서 온전히 회수한 희귀 공작버섯 표본."},
}
MILESTONES=((3,{"max_energy":2},"낯선 유물의 공명"),(6,{"luck":1},"수집가의 직감"),(10,{"dex":1,"int":1},"탑의 축적된 지식"))

def ensure_state(player):
    if not isinstance(getattr(player,"tower_state",None),dict): player.tower_state={}
    return player.tower_state.setdefault("exhibition",{"displayed":[],"claimed":[]})
def displayed(player): return list(ensure_state(player).get("displayed",[]))
def available_to_display(player):
    inv=getattr(player,"inventory",{})
    shown=set(displayed(player))
    return [k for k,v in EXHIBITS.items() if k not in shown and inv.get(v["item_id"],0)>0]
def display(player,key):
    if key not in EXHIBITS or key not in available_to_display(player): return False,[]
    item=EXHIBITS[key]
    if not player.remove_item(item["item_id"],1): return False,[]
    st=ensure_state(player);st["displayed"].append(key)
    return True,apply_milestones(player)
def apply_milestones(player):
    st=ensure_state(player);n=len(st["displayed"]);rewards=[]
    for need,bonus,label in MILESTONES:
        token=str(need)
        if n<need or token in st["claimed"]: continue
        if "max_energy" in bonus:
            player.max_energy+=bonus["max_energy"];player.energy=min(player.max_energy,player.energy+bonus["max_energy"])
        for stat in ("str","int","dex","will","luck"):
            if stat in bonus: player.stats[stat]=player.stats.get(stat,0)+bonus[stat]
        st["claimed"].append(token);rewards.append((label,dict(bonus)))
    return rewards
def summary(player):
    st=ensure_state(player);n=len(st["displayed"]);next_m=next((m for m in MILESTONES if n<m[0]),None)
    return {"count":n,"total":len(EXHIBITS),"displayed":[EXHIBITS[k] for k in st["displayed"] if k in EXHIBITS],"next":next_m}
