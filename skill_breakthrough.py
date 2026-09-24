"""생활 스킬의 굵직한 랭크 구간을 세계 탐험 퀘스트로 연결한다."""
from __future__ import annotations

BREAKTHROUGHS = {
    ("alchemy", "C"): {
        "target_rank": "B", "id": "alchemy_c_b_sussur",
        "title": "🧪 연금술 돌파 · 마력을 잠재우는 꽃",
        "description": "셀루네 수정지에서 수서꽃을 직접 발견하고, 그 성질을 조사해야 B랭크의 문이 열린다.",
        "objectives": [("discover_sussur", "셀루네 수정지에서 수서꽃을 직접 확보한다")],
    },
    ("cooking", "C"): {
        "target_rank":"B","id":"cooking_c_b_underdark_table","title":"🍳 요리 돌파 · 언더다크의 식탁",
        "description":"낯선 균류를 재료가 아니라 한 접시의 음식으로 이해해야 한다.",
        "objectives":[("cook_underdark_truffle_pasta","언더다크 트러플 파스타를 직접 완성한다"),("cook_spore_mushroom_broth","포자 버섯 육수를 직접 완성한다")],
    },
    ("gathering", "B"): {
        "target_rank":"A","id":"gathering_b_a_noblestalk","title":"🌿 채집 돌파 · 폭발밭의 한 송이",
        "description":"비버뱅 군락의 위험을 뚫고 공작버섯을 파괴하지 않은 채 직접 회수한다.",
        "objectives":[("discover_noblestalk","비버뱅 군락지에서 공작버섯을 직접 확보한다")],
    },
    ("metallurgy", "B"): {
        "target_rank":"A","id":"metallurgy_b_a_mithril","title":"🔥 제련 돌파 · 푸른 금속의 온도",
        "description":"고급 광석의 불순물과 온도를 다루는 법을 증명한다.",
        "objectives":[("smelt_mithril","미스릴 주괴 제련에 직접 성공한다")],
    },
    ("blacksmith", "B"): {
        "target_rank":"A","id":"blacksmith_b_a_fine_forge","title":"🔨 블랙스미스 돌파 · 대장장이의 손끝",
        "description":"단순 완성이 아니라 훌륭함 이상의 금속 장비를 직접 만들어 낸다.",
        "objectives":[("forge_excellent_breakthrough","훌륭함 이상의 장비를 직접 완성한다")],
    },
    ("fishing", "B"): {
        "target_rank":"A","id":"fishing_b_a_golden_eel","title":"🎣 낚시 돌파 · 황금빛 입질",
        "description":"평범한 어획이 아닌 전설의 입질을 직접 읽어내야 한다.",
        "objectives":[("catch_golden_eel","황금장어를 직접 낚는다")],
    },
    ("mining", "A"): {
        "target_rank":"9","id":"mining_a_9_diamond","title":"⛏️ 채광 돌파 · 돌 속의 별",
        "description":"고급 광맥에서 전설급 보석을 직접 캐내 광맥을 읽는 눈을 증명한다.",
        "objectives":[("mine_diamond","다이아몬드를 직접 채굴한다")],
    },
    ("woodcutting", "A"): {
        "target_rank":"9","id":"woodcutting_a_9_treant","title":"🪓 벌목 돌파 · 살아 있는 나이테",
        "description":"평범한 목재가 아닌 숲의 오래된 생명력을 품은 재료를 직접 얻는다.",
        "objectives":[("find_treant_core","나무정령 심장을 직접 얻는다")],
    },
}

def get_breakthrough(skill_id, rank): return BREAKTHROUGHS.get((skill_id,rank))
def _bucket(player, quest): return player._flags.setdefault("skill_breakthrough",{}).setdefault(quest["id"],{"started":False,"progress":{}})
def start(player, skill_id, rank):
    q=get_breakthrough(skill_id,rank)
    if not q:return None
    b=_bucket(player,q);b["started"]=True;return q

def record(player,event,count=1):
    changed=[]
    for q in BREAKTHROUGHS.values():
        b=_bucket(player,q)
        if not b.get("started"):continue
        for key,_ in q["objectives"]:
            if key==event:
                was_complete=complete(player,q)
                b["progress"][key]=min(1,b["progress"].get(key,0)+count);changed.append(q["id"])
                if not was_complete and complete(player,q):
                    reward={"alchemy_c_b_sussur":"quest_sussur_specimen","gathering_b_a_noblestalk":"quest_noblestalk_specimen","mining_a_9_diamond":"quest_star_diamond"}.get(q["id"])
                    if reward and getattr(player,"inventory",{}).get(reward,0)<1:
                        player.add_item(reward,1)
    return changed

def complete(player,q):
    b=_bucket(player,q);return b.get("started") and all(b["progress"].get(k,0)>=1 for k,_ in q["objectives"])
def blocks_rank_up(player,skill_id,rank):
    q=get_breakthrough(skill_id,rank)
    if not q:return False
    b=_bucket(player,q)
    # EXP가 구간에 도달하면 퀘스트가 자동 시작되며, 행동 완료 전 승급을 막는다.
    b["started"]=True
    return not complete(player,q)
def status(player,skill_id,rank):
    q=get_breakthrough(skill_id,rank)
    if not q:return None
    b=_bucket(player,q)
    return {**q,"started":b.get("started",False),"complete":complete(player,q),"progress":dict(b.get("progress",{}))}
