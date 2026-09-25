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
    st = player.tower_state.setdefault("exhibition",{"displayed":[],"claimed":[]})
    st.setdefault("piano_quest", "locked")
    return st
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
def store_carried_exhibits(player):
    """탑 귀환 시 휴대 중인 전시용 유일품을 전시관으로 자동 이관한다."""
    stored=[];rewards=[]
    for key in list(available_to_display(player)):
        ok,new_rewards=display(player,key)
        if ok:
            stored.append(EXHIBITS[key]["name"]);rewards.extend(new_rewards)
    return stored,rewards

def entry_notice(player):
    stored,rewards=store_carried_exhibits(player)
    if not stored: return None
    names=", ".join(stored)
    text=f"🏛️ **{names}**을(를) 비전의 탑 전시관에 보관했습니다."
    if rewards:
        text += "\n" + "\n".join(f"🔮 **{label}** 공명이 깨어났습니다." for label,_ in rewards)
    return text

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
        if need == 3:
            st["piano_quest"] = "available"
            try:
                from lubato_song_memory import remember
                remember(player, "first_exhibition_resonance")
            except Exception:
                pass
    return rewards
def summary(player):
    st=ensure_state(player);n=len(st["displayed"]);next_m=next((m for m in MILESTONES if n<m[0]),None)
    return {"count":n,"total":len(EXHIBITS),"displayed":[EXHIBITS[k] for k in st["displayed"] if k in EXHIBITS],"next":next_m}


def hall_stage(player):
    n=len(displayed(player))
    if n>=10: return {"level":4,"name":"기억의 전당","desc":"안쪽의 봉인된 전시실까지 열렸다. 유물의 빛이 천장 문양을 따라 흐르고, 탑 전체가 오래된 기억을 되찾은 듯 낮게 울린다.","change":"🔓 안쪽 전시실 개방 · 천장 비전 문양 점등"}
    if n>=6: return {"level":3,"name":"관리되는 전시실","desc":"진열장마다 작은 조명이 켜지고 버나드가 전시품의 위치와 상태를 기록하기 시작했다. 빈 방이 이제 제법 박물관처럼 보인다.","change":"🤖 버나드 전시 관리 시작 · 진열장 조명 점등"}
    if n>=3: return {"level":2,"name":"깨어난 전시실","desc":"첫 공명과 함께 먼지뿐이던 방의 진열장에 은은한 불이 들어왔다. 모험에서 가져온 물건들이 탑 안에 자기 자리를 얻기 시작한다.","change":"✨ 진열장 조명 점등 · 전시관 공명 활성화"}
    if n>=1: return {"level":1,"name":"작은 전시실","desc":"오래 비어 있던 방에 첫 발견물이 놓였다. 아직 어둡고 조용하지만, 이곳이 무엇을 위한 방인지는 분명해졌다.","change":"🏛️ 첫 진열대 활성화"}
    return {"level":0,"name":"빈 전시실","desc":"먼지 쌓인 진열대와 비어 있는 받침대만 남은 방. 아직 이 탑의 새 주인이 남긴 이야기는 없다.","change":"빈 진열대"}


def piano_quest_state(player):
    """전시관 첫 공명 뒤 열리는 지하실의 오래된 피아노 사이드 스토리."""
    st = ensure_state(player)
    if len(st.get("displayed", [])) >= 3 and st.get("piano_quest") == "locked":
        st["piano_quest"] = "available"
    return st.get("piano_quest", "locked")

def advance_piano_quest(player):
    st = ensure_state(player)
    state = piano_quest_state(player)
    order = {"available":"found", "found":"opened", "opened":"restored"}
    if state in order:
        st["piano_quest"] = order[state]
    return st.get("piano_quest", state)

def piano_unlocked(player):
    return piano_quest_state(player) == "restored"
