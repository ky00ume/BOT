"""renderer/cards.py — BG3Renderer 클래스 (모든 render_* 메서드)"""
import io
from typing import Optional

try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from renderer.palette import C
from renderer.fonts import _f, _tw, _th
from renderer.assets import _load_portrait, _load_banner
from renderer.drawing import (
    _make_base, _gv, _rr, _glow, _orn, _notxt, _wrap, _gold_frame,
    _to_buf, _bar_A, _grade_badge, _ph_portrait, _paste_stat_icon,
    _MAX_IMG_DIM,
)


class BG3Renderer:

    # ─── 범용 카드 ───────────────────────────────────────────────
    def render_card(self, title, rows,
                    grade="Normal", subtitle=None,
                    system_key="system",
                    footer="✦ 비전 타운 ✦",
                    w=520, h=380) -> io.BytesIO:
        w = min(w, _MAX_IMG_DIM); h = min(h, _MAX_IMG_DIM)
        title = str(title)[:200]; subtitle = str(subtitle)[:200] if subtitle else None
        PAD = 24; HH = 66 if not subtitle else 88; FH = 46

        # 아이템 수에 따라 글씨 크기 유동 조절
        # D-2: 인벤토리 가독성 개선을 위해 폰트 크기 증가
        n_rows = len(rows)
        if n_rows > 26:
            _lh_val = 22; _font_val = 20; _font_lbl = 18; _row_min = 32
        elif n_rows > 14:
            _lh_val = 26; _font_val = 24; _font_lbl = 22; _row_min = 40
        else:
            _lh_val = 30; _font_val = 27; _font_lbl = 24; _row_min = 48

        fV = _f(_font_val, True)
        fL = _f(_font_lbl)
        mx_col = PAD + (w - PAD * 2) * 2 // 5 + 26
        val_maxw = w - PAD - mx_col - 8

        # 행별 실제 높이 계산 (텍스트 줄바꿈 고려)
        _tmp = Image.new("RGBA", (w, 1))
        _tmp_d = ImageDraw.Draw(_tmp)
        row_heights = []
        for row in rows:
            val = str(row.get("value", ""))
            line = ""; n = 0
            for ch in val:
                test = line + ch
                if _tw(_tmp_d, test, fV) > val_maxw and line:
                    n += 1; line = ch
                else:
                    line = test
            if line:
                n += 1
            row_heights.append(max(_row_min, n * _lh_val + 14))

        min_h = HH + FH + 30 + sum(row_heights) + 10
        h = max(h, min_h)
        h = min(h, _MAX_IMG_DIM)

        img = _make_base(w, h, system_key, grade)
        d   = ImageDraw.Draw(img)
        rc  = C.RARITY.get(grade, (155, 155, 155))
        fT  = _f(28, True); fS = _f(16); fF = _f(14)

        # 헤더 패널
        hdr = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        _gv(hdr, 0, 0, w, HH, (*C.BG3, 225), (0, 0, 0, 0))
        img.alpha_composite(hdr); d = ImageDraw.Draw(img)

        _notxt(d, (PAD, 13), title, fT, C.TXT_HI)
        if subtitle: _notxt(d, (PAD + 1, 50), subtitle, fS, C.TXT_LO)
        _grade_badge(img, d, w - 165, 12, grade)
        _orn(img, d, PAD, HH, w - PAD, color=rc)

        # 콘텐츠 패널
        CT = HH + 12; CB = h - FH - 6
        _rr(img, PAD, CT, w - PAD, CB, 8, fill=(*C.BG2, 115))
        d = ImageDraw.Draw(img)
        cy = CT + 12

        for i, (row, rh) in enumerate(zip(rows, row_heights)):
            lbl = row.get("label", ""); val = str(row.get("value", ""))
            col = row.get("color", C.TXT_HI)
            if i > 0: d.line([(PAD + 18, cy - 5), (w - PAD - 18, cy - 5)], fill=C.SEP, width=1)
            _notxt(d, (PAD + 18, cy), lbl + ":", fL, C.TXT_LBL)
            _wrap(d, val, fV, mx_col, cy, val_maxw, col, lh=_lh_val)
            cy += rh

        sy = h - FH; _orn(img, d, PAD, sy, w - PAD, color=C.GOLD_LO)
        fw = _tw(d, footer, fF); fh = _th(d, footer, fF)
        _notxt(d, (w // 2 - fw // 2, sy + (FH - fh) // 2), footer, fF, C.TXT_LO)
        _gold_frame(img); return _to_buf(img)

    # ─── 상태창 ──────────────────────────────────────────────────
    def render_status_card(self,
                           name, level, title_str,
                           hp, max_hp, mp, max_mp, en, max_en,
                           gold, exp, exp_needed,
                           stats: dict,
                           inv_used, inv_max) -> io.BytesIO:
        W = 520
        PAD = 22; HH = 78

        # ── 폰트 (모바일 가독성 우선 — 큰 사이즈) ────────────
        fN  = _f(34, True)   # 이름
        fT  = _f(20)         # 칭호
        fLb = _f(18, True)   # HP/MP/EN 라벨
        fBv = _f(18)         # 바 수치
        fSec = _f(18, True)  # 섹션 헤더
        fSt = _f(20)         # 스탯 이름
        fV  = _f(22, True)   # 스탯 값
        fFt = _f(20, True)   # 하단

        # ── 높이 계산 (세로 배치) ─────────────────────────────
        # 헤더(78) + 바간격(18) + 바3줄(126) + 구분(16) + EXP(42)
        # + 구분+헤더(42) + 스탯5줄(180) + 하단(66)
        H = HH + 18 + 126 + 16 + 42 + 42 + 180 + 66
        img = _make_base(W, H, "status")
        d   = ImageDraw.Draw(img)

        # ── 헤더 ──────────────────────────────────────────────
        hdr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        _gv(hdr, 0, 0, W, HH, (*C.BG3, 230), (0, 0, 0, 0))
        img.alpha_composite(hdr); d = ImageDraw.Draw(img)
        _notxt(d, (PAD, 10), f"Lv.{level}  {name}", fN, C.TXT_HI)
        if title_str and str(title_str) != "None":
            _notxt(d, (PAD + 2, 42), f"✦ {title_str}", fT, C.GOLD_MID)
        _orn(img, d, PAD, HH, W - PAD)

        # ── 게이지 바 (전체 폭 사용) ─────────────────────────
        BW = W - PAD * 2 - 62; BH = 24; BX = PAD + 56; LX = PAD + 4
        bars = [("HP", hp, max_hp, C.HP), ("MP", mp, max_mp, C.MP), ("EN", en, max_en, C.EN)]
        by = HH + 18
        for lbl, cur, mx2, cols in bars:
            _notxt(d, (LX, by + 3), lbl, fLb, C.TXT_LBL)
            _bar_A(img, d, BX, by, BW, BH, cur, mx2, cols, show_val=False)
            d = ImageDraw.Draw(img)
            # 수치를 바 안쪽 오른편에 표시
            vtxt = f"{cur}/{mx2}"
            vw = _tw(d, vtxt, fBv)
            _notxt(d, (BX + BW - vw - 6, by + 3), vtxt, fBv, C.TXT_HI)
            by += 42

        # EXP 바
        _orn(img, d, PAD, by + 2, W - PAD, color=C.GOLD_LO); by += 16
        _notxt(d, (LX, by + 3), "EXP", fLb, C.TXT_LBL)
        _bar_A(img, d, BX, by, BW, BH, int(exp), exp_needed, C.EXP, show_val=False)
        d = ImageDraw.Draw(img)
        vtxt = f"{int(exp)}/{exp_needed}"
        vw = _tw(d, vtxt, fBv)
        _notxt(d, (BX + BW - vw - 6, by + 3), vtxt, fBv, C.TXT_HI)
        by += 42

        # ── 구분선 + 스탯 (바 아래에 배치) ────────────────────
        _orn(img, d, PAD, by, W - PAD)
        by += 12
        _notxt(d, (PAD + 8, by), "[ 기본 스탯 ]", fSec, C.GOLD_MID)
        by += 30

        STAT_DATA = [
            ("str",  "힘",   stats.get("str", 0)),
            ("dex",  "민첩", stats.get("dex", 0)),
            ("int",  "지력", stats.get("int", 0)),
            ("will", "의지", stats.get("will", 0)),
            ("luck", "운",   stats.get("luck", 0)),
        ]
        IS = 26  # 아이콘 크기
        for sk, sname, val in STAT_DATA:
            _paste_stat_icon(img, d, sk, PAD + 8, by, IS)
            d = ImageDraw.Draw(img)
            text_y = by + (IS - _th(d, "가", fSt)) // 2
            _notxt(d, (PAD + 8 + IS + 12, text_y), sname, fSt, C.TXT_LBL)
            vt = str(val); vw = _tw(d, vt, fV)
            _notxt(d, (W - PAD - vw - 8, text_y), vt, fV, C.TXT_HI)
            # 점선 리더
            leader_y = text_y + _th(d, "가", fSt) // 2
            lx2 = PAD + 8 + IS + 12 + _tw(d, sname, fSt) + 8
            rx2 = W - PAD - vw - 16
            if rx2 > lx2:
                for dx in range(lx2, rx2, 7):
                    d.point((dx, leader_y), fill=C.SEP)
            by += 36

        # ── 하단 골드/인벤 ────────────────────────────────────
        _orn(img, d, PAD, H - 60, W - PAD)
        _notxt(d, (PAD + 12, H - 46), f"◆ {gold:,} G", fFt, C.GOLD_HI)
        it = f"{inv_used} / {inv_max} 슬롯"
        iw = _tw(d, it, fFt)
        _notxt(d, (W - PAD - iw - 12, H - 46), it, fFt, C.TXT_MID)
        _orn(img, d, PAD, H - 16, W - PAD, color=C.GOLD_LO)

        _gold_frame(img); return _to_buf(img)

    # ─── 장비창 ────────────────────────────────────────────────
    def render_equipment_card(self, name, slots, attack, defense,
                               magic_attack=0) -> io.BytesIO:
        """
        장비창 카드 렌더링.
        slots: [{"slot_name": str, "item_name": str|None, "grade": str, "stats_text": str}, ...]
        """
        W, H = 600, 480
        img = _make_base(W, H, "equipment")
        d   = ImageDraw.Draw(img)
        fN  = _f(28, True); fSec = _f(17, True)
        fL  = _f(17); fV = _f(19, True); fF = _f(14)
        PAD = 24; HH = 68

        # 헤더
        hdr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        _gv(hdr, 0, 0, W, HH, (*C.BG3, 225), (0, 0, 0, 0))
        img.alpha_composite(hdr); d = ImageDraw.Draw(img)
        _notxt(d, (PAD, 15), f"⚔ {name}의 장비창", fN, C.TXT_HI)
        _orn(img, d, PAD, HH, W - PAD)

        # 콘텐츠 영역
        FH = 46; CT = HH + 12; CB = H - FH - 6
        _rr(img, PAD, CT, W - PAD, CB, 8, fill=(*C.BG2, 115))
        d = ImageDraw.Draw(img)

        cy = CT + 14
        mx_col = PAD + 120

        for slot in slots:
            sname = slot.get("slot_name", "")
            iname = slot.get("item_name")
            grade = slot.get("grade", "Normal")
            stats = slot.get("stats_text", "")

            if cy > CT + 14:
                d.line([(PAD + 18, cy - 5), (W - PAD - 18, cy - 5)],
                       fill=C.SEP, width=1)

            _notxt(d, (PAD + 18, cy), f"[{sname}]", fL, C.GOLD_MID)

            if iname:
                col = C.RARITY.get(grade, (155, 155, 155))
                display = iname
                if stats:
                    display += f"  {stats}"
                _notxt(d, (mx_col, cy), display, fV, col)
            else:
                _notxt(d, (mx_col, cy), "— 비어있음 —", fV, C.TXT_LO)
            cy += 38

        # 전투 스탯 구분선
        cy += 10
        _orn(img, d, PAD + 18, cy, W - PAD - 18, color=C.GOLD_LO)
        cy += 16
        _notxt(d, (PAD + 18, cy), "[ 전투 스탯 ]", fSec, C.GOLD_MID)
        cy += 30
        _notxt(d, (PAD + 18, cy), "공격력:", fL, C.TXT_LBL)
        _notxt(d, (mx_col, cy), str(attack), fV, C.TXT_HI)
        cy += 30
        _notxt(d, (PAD + 18, cy), "방어력:", fL, C.TXT_LBL)
        _notxt(d, (mx_col, cy), str(defense), fV, C.TXT_HI)
        if magic_attack:
            cy += 30
            _notxt(d, (PAD + 18, cy), "마공력:", fL, C.TXT_LBL)
            _notxt(d, (mx_col, cy), str(magic_attack), fV, C.TXT_HI)

        # 푸터
        footer = "✦ 장비 정보 ✦"
        sy = H - FH
        _orn(img, d, PAD, sy, W - PAD, color=C.GOLD_LO)
        fw = _tw(d, footer, fF); fh = _th(d, footer, fF)
        _notxt(d, (W // 2 - fw // 2, sy + (FH - fh) // 2), footer, fF, C.TXT_LO)

        _gold_frame(img); return _to_buf(img)

    # ─── NPC 대화 ────────────────────────────────────────────────
    def render_npc_dialogue(self,
                            npc_name, npc_role, greeting,
                            affinity_pts, affinity_level,
                            portrait_type="npc",
                            portrait_id=None) -> io.BytesIO:
        """
        portrait_type: 'npc' | 'animal' | 'monster'
        portrait_id:   파일명 (확장자 제외). None이면 플레이스홀더
        """
        W = 560; MIN_H = 290
        PW = 200; fN = _f(24, True); fR = _f(16); fD = _f(17); fA = _f(16); fP = _f(14)
        TX = PW + 14; ty = 18; LH = 26

        # ── 동적 높이 계산 ──────────────────────────────────────
        _tmp_img = Image.new("RGBA", (W, 1), (0, 0, 0, 0))
        _tmp_d   = ImageDraw.Draw(_tmp_img)
        name_h   = _th(_tmp_d, npc_name, fN)
        role_h   = _th(_tmp_d, f"[ {npc_role} ]", fR)
        orn_y    = ty + name_h + role_h + 14
        greeting_text = f'"{greeting}"'
        maxw = W - TX - 24
        text_start_y = orn_y + 12
        text_end_y   = _wrap(_tmp_d, greeting_text, fD, TX, text_start_y, maxw, (0, 0, 0, 0), lh=LH)
        # 헤더 + 대사 줄들 + 여백(20) + 호감도 바 영역(58)
        H = max(MIN_H, min(600, text_end_y + 20 + 58))

        img = _make_base(W, H, "npc")
        d   = ImageDraw.Draw(img)
        PX0, PY0 = 14, 14; PX1, PY1 = PW - 4, H - 14
        pw2 = PX1 - PX0 - 2; ph2 = PY1 - PY0 - 2

        # 초상화
        _rr(img, PX0, PY0, PX1, PY1, 8, fill=(*C.BG3, 200))
        port = (_load_portrait(portrait_type, portrait_id, pw2, ph2)
                if portrait_id else None)
        if port:
            mk = Image.new("L", (pw2, ph2), 0)
            ImageDraw.Draw(mk).rounded_rectangle([0, 0, pw2 - 1, ph2 - 1], radius=6, fill=255)
            # 포트레잇 알파를 둥근 사각형으로 클리핑 후 alpha_composite 사용
            # (paste+L마스크는 투명 픽셀을 직접 복사해 체크패턴을 만드는 버그가 있음)
            _r, _g, _b, _a = port.split()
            clipped_a = Image.new("L", (pw2, ph2), 0)
            clipped_a.paste(_a, mask=mk)
            port.putalpha(clipped_a)
            _tmp_port = Image.new("RGBA", img.size, (0, 0, 0, 0))
            _tmp_port.paste(port, (PX0 + 1, PY0 + 1))
            img.alpha_composite(_tmp_port)
        else:
            _ph_portrait(img, d, PX0, PY0, PX1, PY1)

        d = ImageDraw.Draw(img)
        d.rounded_rectangle([PX0, PY0, PX1, PY1], radius=8, outline=C.GOLD_MID, width=2)

        # 대화창
        _notxt(d, (TX, ty), npc_name, fN, C.GOLD_HI)
        _notxt(d, (TX, ty + name_h + 6), f"[ {npc_role} ]", fR, C.TXT_LO)
        _orn(img, d, TX, orn_y, W - 18, color=C.GOLD_LO)
        _wrap(d, greeting_text, fD, TX, orn_y + 12, maxw, C.TXT_HI, lh=LH)

        # 호감도 바 (시안 A)
        AY = H - 58; _orn(img, d, TX, AY, W - 18, color=(*C.TEAL_LO, 180))
        d = ImageDraw.Draw(img)
        aff_y = AY + 10
        _notxt(d, (TX, aff_y), affinity_level, fA, C.TEAL_HI)
        aw = _tw(d, affinity_level, fA)
        _bar_A(img, d, TX + aw + 12, aff_y, W - TX - aw - 72, 18,
               min(affinity_pts, 100), 100,
               (C.TEAL_LO, C.TEAL_HI), show_val=False)
        d = ImageDraw.Draw(img)
        pt2 = f"{affinity_pts}pt"; pw3 = _tw(d, pt2, fP)
        _notxt(d, (W - pw3 - 18, aff_y + 2), pt2, fP, C.TXT_LO)

        _gold_frame(img); return _to_buf(img)

    # ─── 전투 카드 ───────────────────────────────────────────────
    def render_battle_card(self,
                           monster_name, monster_level,
                           monster_hp, monster_max_hp,
                           danger, turn,
                           player_hp, player_max_hp,
                           player_mp, player_max_mp,
                           last_action="", last_dmg=0,
                           is_crit=False, size_label="") -> io.BytesIO:
        W, H = 540, 360
        img = _make_base(W, H, "battle"); d = ImageDraw.Draw(img)
        fB = _f(26, True); fM = _f(18, True); fS = _f(16); fL = _f(14); PAD = 22

        _notxt(d, (PAD, 14), monster_name, fB, C.TXT_HI)
        _notxt(d, (PAD + 2, 50), f"Lv.{monster_level}   {size_label}", fS, C.TXT_LO)

        DCOL = {"위험당함": (220, 55, 45), "보통": (230, 180, 30), "안전": (50, 195, 100)}
        dc = DCOL.get(danger, (155, 155, 155)); dt = f"  {danger}  "
        dw = _tw(d, dt, fS)
        _rr(img, W - dw - PAD - 6, 12, W - PAD + 2, 40, 5, fill=(*dc, 38), outline=dc, lw=1)
        d = ImageDraw.Draw(img); d.text((W - dw - PAD, 16), dt, font=fS, fill=dc)

        rc = C.SYS["battle"]; _orn(img, d, PAD, 68, W - PAD, color=rc)

        # 몬스터 HP (시안 A, 크게)
        _notxt(d, (PAD, 80), "몬스터 HP", fL, C.TXT_LBL)
        _bar_A(img, d, PAD + 98, 78, W - PAD * 2 - 98, 28, monster_hp, monster_max_hp, C.HP)
        d = ImageDraw.Draw(img); _orn(img, d, PAD, 122, W - PAD, color=(68, 22, 28))

        # 플레이어 HP/MP
        _notxt(d, (PAD, 134), "내 HP", fL, C.TXT_LBL)
        _bar_A(img, d, PAD + 76, 132, 240, 22, player_hp, player_max_hp, C.HP)
        d = ImageDraw.Draw(img)
        _notxt(d, (PAD, 164), "내 MP", fL, C.TXT_LBL)
        _bar_A(img, d, PAD + 76, 162, 240, 22, player_mp, player_max_mp, C.MP)
        d = ImageDraw.Draw(img); _orn(img, d, PAD, 200, W - PAD, color=(68, 22, 28))

        # 마지막 액션
        if last_action:
            col = C.GOLD_HI if is_crit else C.TXT_HI
            pre = "[크리티컬]  " if is_crit else ""
            _notxt(d, (PAD, 212), f"{pre}{last_action}  /  {last_dmg} 피해", fM, col)
        tt = f"턴  {turn}"; tw2 = _tw(d, tt, fS)
        _notxt(d, (W - tw2 - PAD, 212), tt, fS, C.TXT_LO)

        _orn(img, d, PAD, H - 56, W - PAD, color=rc)
        g = "/공격 [스킬명]   /도주"; gw = _tw(d, g, fL)
        d.text((W // 2 - gw // 2, H - 42), g, font=fL, fill=C.TXT_LO)

        _gold_frame(img); return _to_buf(img)

    # ─── 장소 배너 ───────────────────────────────────────────────
    def render_location_banner(self,
                                location_name: str,
                                description: str,
                                zone_type: str = "town",
                                zone_id: Optional[str] = None) -> io.BytesIO:
        """
        zone_type: 'town' | 'hunting' | 'gathering' | 'fishing'
        zone_id:   파일명 (확장자 제외, 예: '비전타운', '고블린동굴')
                   None이면 플레이스홀더 표시
        """
        W = 540; SH = 180
        fLoc = _f(34, True); fDesc = _f(17); fSub = _f(14)
        LH = 24  # 설명 텍스트 줄 간격

        # ── 텍스트 패널 높이 동적 계산 ──────────────────────────
        # 임시 이미지에서 줄바꿈 결과를 미리 계산하여 TH 결정
        _tmp_img = Image.new("RGBA", (W, 1), (0, 0, 0, 0))
        _tmp_d   = ImageDraw.Draw(_tmp_img)
        desc_text = description or ""
        # 줄 수 계산
        line_count = 0
        line = ""
        for ch in desc_text:
            test = line + ch
            if _tw(_tmp_d, test, fDesc) > W - 56 and line:
                line_count += 1
                line = ch
            else:
                line = test
        if line:
            line_count += 1
        # 장소명(44) + 밑줄(6) + 설명 줄들 + 하단 여백(44)
        TH = max(130, 44 + 6 + line_count * LH + 44)
        H = SH + TH

        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))

        # ── 상단 씬 이미지 슬롯 ─────────────────────────────
        scene = (_load_banner(zone_type, zone_id, W, SH)
                 if zone_id else None)

        if scene:
            # 하단 페이드 아웃
            fd = Image.new("RGBA", (W, SH), (0, 0, 0, 0))
            _gv(fd, 0, SH * 3 // 5, W, SH, (0, 0, 0, 0), (0, 0, 0, 210))
            scene.alpha_composite(fd)
            img.paste(scene, (0, 0))
        else:
            # 플레이스홀더 (그라디언트 + 안내 텍스트)
            _gv(img, 0, 0, W, SH, C.BG2, C.BG0)
            d2 = ImageDraw.Draw(img)
            d2.rounded_rectangle([16, 16, W - 17, SH - 16], radius=8,
                                  outline=(*C.GOLD_LO, 100), width=1)
            fph = _f(17)
            ph_type = {"town": "마을", "hunting": "사냥터",
                       "gathering": "채집터", "fishing": "낚시터"}.get(zone_type, "")
            ph = f"[ {ph_type} 씬 이미지 슬롯 ]"
            pw = _tw(d2, ph, fph)
            d2.text((W // 2 - pw // 2, SH // 2 - 11), ph, font=fph, fill=C.TXT_LO)

        # 씬 슬롯 테두리 표시
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([14, 14, W - 15, SH - 14], radius=8,
                             outline=(*C.GOLD_LO, 80), width=1)

        # ── 하단 텍스트 패널 ────────────────────────────────
        tp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        _gv(tp, 0, SH, W, H, (*C.BG1, 245), (*C.BG0, 255))
        img.alpha_composite(tp); d = ImageDraw.Draw(img)

        TY = SH + 16
        # 금장 세로선
        d.line([(24, TY + 2), (24, H - 18)], fill=C.GOLD_MID,  width=3)
        d.line([(25, TY + 2), (25, H - 18)], fill=(*C.GOLD_HI, 65), width=1)

        _notxt(d, (42, TY), location_name, fLoc, C.GOLD_HI)
        lw = _tw(d, location_name, fLoc)
        d.line([(42, TY + 48), (42 + lw, TY + 48)], fill=C.GOLD_MID, width=1)
        _wrap(d, desc_text, fDesc, 42, TY + 58, W - 60, C.TXT_MID, lh=LH)

        sub = "✦ 비전 타운   언더다크"; sw = _tw(d, sub, fSub)
        d.text((W - sw - 20, H - 26), sub, font=fSub, fill=C.TXT_LO)

        # 전체 마스크
        mk = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mk).rounded_rectangle([0, 0, W - 1, H - 1], radius=16, fill=255)
        r = Image.new("RGBA", (W, H), (0, 0, 0, 0)); r.paste(img, mask=mk); img = r

        _gold_frame(img); return _to_buf(img)

    # ─── 범용 결과 카드 ────────────────────────────────────────────
    def render_result_card(self, title, subtitle=None, rows=None,
                           system_key="system", grade="Normal",
                           footer="✦ 비전 타운 ✦") -> io.BytesIO:
        """낚시/요리/제련/채집/전투결과 등 범용 결과 카드"""
        rows = rows or []
        return self.render_card(title, rows, grade=grade, subtitle=subtitle,
                                system_key=system_key, footer=footer)

    # ─── 전투 결과 카드 ────────────────────────────────────────────
    def render_battle_result(self, title, is_victory=True,
                             rewards_rows=None, level_up_info=None) -> io.BytesIO:
        """전투 승리/패배 결과"""
        rows = rewards_rows or []
        if level_up_info:
            rows.append({"label": "레벨 업!", "value": level_up_info, "color": C.GOLD_HI})
        grade = "Legendary" if is_victory else "Fail"
        sys_key = "battle"
        footer = "전투 승리!" if is_victory else "전투 패배..."
        return self.render_card(title, rows, grade=grade, subtitle=None,
                                system_key=sys_key, footer=footer)

    # ─── 퀘스트 카드 ──────────────────────────────────────────────
    def render_quest_card(self, quest_name, npc_name="", quest_type="",
                          difficulty="", description="",
                          progress_cur=0, progress_max=0,
                          rewards=None) -> io.BytesIO:
        """퀘스트 정보 카드"""
        rows = []
        if npc_name:
            rows.append({"label": "NPC", "value": npc_name})
        if quest_type:
            rows.append({"label": "유형", "value": quest_type})
        if difficulty:
            rows.append({"label": "난이도", "value": difficulty})
        if description:
            rows.append({"label": "내용", "value": description[:60]})
        if progress_max > 0:
            rows.append({"label": "진행", "value": f"{progress_cur}/{progress_max}"})
        if rewards:
            rw_parts = []
            if rewards.get("gold"): rw_parts.append(f"{rewards['gold']}G")
            if rewards.get("exp"):  rw_parts.append(f"{rewards['exp']}EXP")
            if rewards.get("item"): rw_parts.append(rewards["item"])
            if rw_parts:
                rows.append({"label": "보상", "value": " / ".join(rw_parts)})
        return self.render_card(quest_name, rows, grade="Normal",
                                system_key="quest", footer="퀘스트")

    # ─── 상점 카드 ────────────────────────────────────────────────
    def render_shop_card(self, shop_name, npc_name="",
                         items=None) -> io.BytesIO:
        """상점 목록 카드"""
        rows = []
        if npc_name:
            rows.append({"label": "상인", "value": npc_name})
        for it in (items or [])[:8]:
            name = it.get("name", "?")
            price = it.get("price", 0)
            rows.append({"label": name, "value": f"{price:,}G"})
        return self.render_card(shop_name, rows, grade="Normal",
                                system_key="shop", footer="상점")

    # ─── 제작 결과 카드 ──────────────────────────────────────────
    def render_craft_result(self, recipe_name, result_item_name,
                            result_grade="Normal", ingredients=None,
                            exp_gained=0, rank_up_msg="",
                            system_key="craft",
                            footer="제작 완료") -> io.BytesIO:
        """제작/제련/요리/연금 결과 카드"""
        rows = [
            {"label": "결과물", "value": result_item_name,
             "color": C.RARITY.get(result_grade, C.TXT_HI)},
        ]
        if ingredients:
            for ing_name, cnt in ingredients:
                rows.append({"label": "소모", "value": f"{ing_name} x{cnt}",
                             "color": C.TXT_MID})
        if exp_gained:
            rows.append({"label": "숙련도", "value": f"+{exp_gained}",
                         "color": C.GOLD_HI})
        if rank_up_msg:
            rows.append({"label": "랭크 업!", "value": rank_up_msg,
                         "color": C.GOLD_HI})
        return self.render_card(recipe_name, rows, grade=result_grade,
                                system_key=system_key, footer=footer)

    # ─── 제작 실패 카드 ──────────────────────────────────────────
    def render_craft_fail(self, recipe_name, reason,
                          exp_gained=0, rank_up_msg="",
                          system_key="craft",
                          footer="제작 실패") -> io.BytesIO:
        """제작/제련/요리/연금 실패 카드"""
        rows = [
            {"label": "실패 사유", "value": reason, "color": C.RARITY["Fail"]},
        ]
        if exp_gained:
            rows.append({"label": "숙련도", "value": f"+{exp_gained}",
                         "color": C.GOLD_HI})
        if rank_up_msg:
            rows.append({"label": "랭크 업!", "value": rank_up_msg,
                         "color": C.GOLD_HI})
        return self.render_card(recipe_name, rows, grade="Fail",
                                system_key=system_key, footer=footer)

    # ─── 제작 레시피 목록 카드 ───────────────────────────────────
    def render_recipe_list(self, skill_name, rank, recipes_info,
                           system_key="craft") -> io.BytesIO:
        """레시피 목록 카드 (skill_name: 스킬명, recipes_info: [(name, rank_req, unlocked), ...])"""
        rows = []
        for name, rank_req, unlocked in recipes_info[:12]:
            status = "O" if unlocked else "X"
            col = C.TXT_HI if unlocked else C.TXT_LO
            rows.append({"label": f"[{status}] [{rank_req}]",
                         "value": name, "color": col})
        return self.render_card(
            f"{skill_name} 레시피", rows, grade="Normal",
            subtitle=f"현재 랭크: {rank}",
            system_key=system_key,
            footer=f"{skill_name} 레시피 목록")
