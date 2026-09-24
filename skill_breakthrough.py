"""생활 스킬의 굵직한 랭크 구간을 세계 탐험 퀘스트로 연결한다."""
from __future__ import annotations

BREAKTHROUGHS = {
    ("alchemy", "C"): {
        "target_rank": "B", "id": "alchemy_c_b_sussur",
        "title": "🧪 연금술 돌파 · 마력을 잠재우는 꽃",
        "description": "셀루네 수정지에서 수서꽃을 직접 발견하고, 그 성질을 조사해야 B랭크의 문이 열린다.",
        "objectives": [("discover_sussur", "셀루네 수정지에서 수서꽃을 직접 확보한다")],
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
                b["progress"][key]=min(1,b["progress"].get(key,0)+count);changed.append(q["id"])
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
