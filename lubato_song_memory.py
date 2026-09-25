"""루바토의 노래 기억: 플레이에서 실제로 겪은 일을 짧은 노래로 남긴다."""
from __future__ import annotations

STATE_KEY = "lubato_song_memories"

# 마제스티(루바토)가 원래 가지고 있는 레퍼토리. 사건 해금 없이 언제든 들을 수 있다.
REPERTOIRE = {
    "eight_shadows": {"title": "여덟 개의 그림자", "verse": "♪ 길 하나에 그림자는 여덟\n어느 것이 먼저 닿아도\n나는 뒤따라 걷지 않아\n내 노래로 옆을 걸을 거야 ♪\n\n♪ 듣고 있는지 묻지 않을게\n대답 같은 것도 필요 없어\n네가 저만큼 앞에 있다면\n나는 여기서 계속 부를 테니 ♪"},
    "shadowlantern": {"title": "그림자등불", "verse": "♪ 손에 든 빛이 길을 비추면\n그 빛은 누구의 것이 될까\n쥔 사람의 것일까\n따라가는 사람의 것일까 ♪\n\n♪ 나는 등불을 들지 않을래\n대신 네가 보이는 데 있을게\n길을 잃으면 이름을 부르고\n대답이 없으면 한 번 더 부를게 ♪"},
    "spider_rhythm": {"title": "거미는 박자를 모른다", "verse": "♪ 다리가 둘이면 하나 둘\n다리가 넷이면 하나 둘 셋 넷\n그런데 여덟 개가 우다다 오면\n잠깐만, 처음부터 다시 ♪\n\n“츄라이더, 오른쪽 세 번째 다리가 자꾸 빨라.”\n“그걸 어떻게 구분함미까?”\n“나도 몰라. 그래서 노래가 망했잖아.”"},
    "come_back_alive": {"title": "살아 돌아온 사람에게", "verse": "♪ 영웅이라 부르지 않아도 돼\n멋진 이야기가 아니어도 돼\n흙투성이 신발을 끌고 와서\n여기 있다고 말해주면 돼 ♪\n\n♪ 이긴 날은 크게 부르고\n진 날에는 조금 작게 부르자\n오늘 돌아온 사람에게는\n내일 부를 노래가 있으니까 ♪"},
    "tower_lights": {"title": "탑에 불이 켜지는 시간", "verse": "♪ 높은 창에 불이 하나\n아래층에도 불이 하나\n누가 돌아왔는지 묻지 않아도\n오늘은 방들이 따뜻하네 ♪\n\n♪ 먼저 온 사람은 기다리고\n늦게 온 사람은 문을 열고\n그렇게 하나씩 돌아오다 보면\n커다란 탑도 집이 되네 ♪"},
    "pet_song": {"title": "복복송", "verse": "♪ 복복 한 번, 복복 두 번\n세 번째부터 세지 마세요\n츄라이더가 납작해져도\n행복한 거니까 계속하세요 ♪\n\n츄라이더가 눈을 반짝입니다.\n“2절도 있슴미까?”\n\n마제스티가 리라 줄을 한 번 튕깁니다.\n“당연하지.”"},
}

REPERTOIRE_INSTRUMENTS = {
    "eight_shadows": "류트",
    "shadowlantern": "리라",
    "spider_rhythm": "리라",
    "come_back_alive": "류트",
    "tower_lights": "류트",
    "pet_song": "류트",
}

SONGS = {
    "karniss_hide": {
        "title": "책장 아래의 작은 것",
        "trigger": "카르니스를 피해 숨었던 날",
        "verse": "♪ 여덟 다리를 꼭 접고\n작은 소리도 감춘 채\n지나가라, 지나가라\n오늘은 여기 없는 척 ♪\n\n♪ 무서운 건 알고 있고\n미움받는 것도 알지만\n그래도 돌아갈 자리는\n아직 따뜻하게 남아 있네 ♪",
        "after": "“끝. 네 노래치고는 조금 조용하지?”\n\n츄라이더가 책장 아래에서 고개를 내밉니다.\n“...카르니스 들으면 화낼 검미댜.”\n\n“그럼 다음엔 더 작게 부르지, 뭐.”",
    },
    "highness_pet": {
        "title": "하이네스의 손바닥",
        "trigger": "하이네스에게 오래 복복 받은 날",
        "verse": "♪ 쪼르르 달려가 머리를 콩\n한 번 더 해달라 손바닥 콩\n여덟 다리 힘이 전부 풀려도\n오늘의 복복은 아직 안 끝났네 ♪",
        "after": "루바토가 웃으며 츄라이더를 봅니다.\n“이건 후렴이 끝이 없겠는데?”\n\n“하이네스는 영원히 복복함미댜. 그러니까 노래도 영원히 해야 함미댜.”",
    },
    "majesty_pet": {
        "title": "조금만 더",
        "trigger": "마제스티의 손길에 늘어진 날",
        "verse": "♪ 한 번 쓰다듬으면 눈이 가늘어지고\n두 번 쓰다듬으면 다리가 풀리고\n세 번째부터는 세지 않기로 해\n조금만 더, 조금만 더 ♪",
        "after": "“이 노래는 끝나는 법을 모르네.”\n\n츄라이더가 당연하다는 듯 몸을 낮춥니다.\n“마제스티가 그만할 때까지임미댜.”",
    },
    "lubato_song": {
        "title": "노래는 안 물어뜯어",
        "trigger": "리라 소리를 따라 루바토를 찾아온 날",
        "verse": "♪ 상자 뒤의 눈 두 개\n아니, 더 많이 반짝이네\n겁낼 필요 없어 나야\n오늘 온 건 노래뿐이야 ♪",
        "after": "루바토가 리라를 무릎에 눕힙니다.\n“이제 알겠지? 내 노래는 안 물어뜯어.”\n\n“그건 이미 알고 있었슴미댜.”",
    },
    "lubato_karniss": {
        "title": "망토 반쪽",
        "trigger": "루바토의 망토 뒤에서 카르니스를 피한 날",
        "verse": "♪ 절반은 망토 뒤에\n절반은 노래 곁에\n저쪽의 무거운 발소리는\n그냥 저쪽에 두자 ♪\n\n♪ 숨을 곳 하나 있으면\n한 소절쯤 들을 수 있지\n오늘도 끝까지 들었으니\n그걸로 된 거야 ♪",
        "after": "루바토가 망토 끝을 살펴봅니다.\n“좋아. 거미줄은 없네.”\n\n“약속은 지킴미댜.”",
    },
    "noblestalk_saved": {
        "title": "포자밭에서 가져온 것",
        "trigger": "비버뱅 사이에서 공작버섯을 구해낸 날",
        "verse": "♪ 한 발 잘못 디디면 펑\n다음 것도 그다음 것도 펑\n그래도 두 손에 남은 건\n재가 아니라 작은 버섯 하나 ♪\n\n♪ 살아 돌아와 보여줬으니\n이제 그날은 노래가 됐네 ♪",
        "after": "“위험한 모험은 별로지만, 무사히 돌아온 모험은 좋아해.”\n\n츄라이더가 고개를 끄덕입니다.\n“노래로 만들 수 있으니까 말임미까?”\n\n“그것도 있고.”",
    },
    "sussur_found": {
        "title": "마법을 조용하게 하는 꽃",
        "trigger": "수서꽃을 온전히 발견한 날",
        "verse": "♪ 빛나는 주문도 잠잠하게\n떠들던 마력도 얌전하게\n푸른 꽃 한 송이 앞에서는\n리라도 잠깐 쉬어가네 ♪",
        "after": "루바토가 일부러 한 박자 쉬었다가 다시 현을 튕깁니다.\n“꽃이 여기 없어서 다행이지?”",
    },
    "golden_eel": {
        "title": "금빛 꼬리가 물을 찬 날",
        "trigger": "황금장어를 처음 낚은 날",
        "verse": "♪ 물 아래 금빛 한 줄\n손끝에는 팽팽한 줄\n놓치지 마, 조금만 더\n오늘 저녁 자랑거리가 올라온다 ♪",
        "after": "“내가 봤으면 더 크게 환호했을 텐데.”\n\n“그러면 물고기가 도망갔을 검미댜.”\n\n“그건 그렇네.”",
    },
    "first_exhibition_resonance": {
        "title": "탑이 기억한 세 가지",
        "trigger": "전시관의 첫 공명을 깨운 날",
        "verse": "♪ 빈 진열대 하나 둘 셋\n모험에서 가져온 이야기도 하나 둘 셋\n먼지뿐이던 오래된 방이\n이제 네가 다녀온 곳을 기억하네 ♪",
        "after": "루바토가 전시관 쪽을 돌아봅니다.\n“물건을 모은 줄 알았는데, 지나온 날을 모으고 있었네.”",
    },
}


def _state(player) -> dict:
    if not hasattr(player, "_flags") or player._flags is None:
        player._flags = {}
    state = player._flags.setdefault(STATE_KEY, {"unlocked": []})
    if not isinstance(state, dict):
        state = {"unlocked": []}
        player._flags[STATE_KEY] = state
    state.setdefault("unlocked", [])
    return state


def remember(player, song_id: str) -> bool:
    """처음 겪은 사건만 기억한다. 새 기억이면 True."""
    if song_id not in SONGS:
        return False
    unlocked = _state(player)["unlocked"]
    if song_id in unlocked:
        return False
    unlocked.append(song_id)
    return True


def unlocked_songs(player) -> list[tuple[str, dict]]:
    unlocked = _state(player)["unlocked"]
    return [(key, SONGS[key]) for key in unlocked if key in SONGS]


def song_text(song_id: str) -> str:
    song = SONGS[song_id]
    return f"루바토가 리라의 줄을 천천히 고릅니다.\n\n“이건 **{song['trigger']}**의 노래야.”\n\n{song['verse']}\n\n{song['after']}"


def repertoire_songs() -> list[tuple[str, dict]]:
    return list(REPERTOIRE.items())

def repertoire_text(song_id: str) -> str:
    song = REPERTOIRE[song_id]
    instrument = REPERTOIRE_INSTRUMENTS.get(song_id, "류트")
    return f"마제스티가 {instrument}를 들고 익숙한 곡을 시작합니다.\n\n**〈{song['title']}〉** · {instrument}\n\n{song['verse']}"
