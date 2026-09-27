"""루바토 레퍼토리의 짧은 원곡 선율과 WAV 렌더러.

외부 음원 없이 합성하므로 melody_id를 연주/작곡 시스템에서 그대로 재사용할 수 있다.
"""
from __future__ import annotations
import math, struct, wave
from pathlib import Path

SR=44100
# (note, beats); R = rest
MELODIES={
 "pet_song": {"bpm":124,"notes":[("G4",1),("B4",1),("D5",1),("B4",1),("A4",1),("G4",1),("E4",2),("G4",1),("A4",1),("B4",1),("D5",1),("B4",1),("A4",1),("G4",2)]},
 "spider_rhythm":{"instrument":"lyre","bpm":136,"notes":[("E4",.5),("G4",.5),("A4",1),("E4",.5),("G4",.5),("B4",1),("A4",.5),("B4",.5),("D5",1),("B4",.5),("A4",.5),("G4",1),("E4",2)]},
 "come_back_alive":{"instrument":"lute","bpm":94,"notes":[("D4",1),("F4",1),("A4",2),("G4",1),("F4",1),("D4",2),("F4",1),("G4",1),("A4",1),("C5",1),("A4",2),("G4",1),("F4",1),("D4",2)]},
 "tower_lights":{"instrument":"lute","bpm":88,"notes":[("C4",1),("E4",1),("G4",2),("E4",1),("G4",1),("A4",2),("G4",1),("E4",1),("D4",2),("E4",1),("G4",1),("C5",2)]},
 "shadowlantern":{"instrument":"lyre","bpm":84,"notes":[("D4",1.5),("A4",.5),("C5",1),("A4",1),("F4",2),("R",1),("D4",1),("F4",1),("A4",1),("C5",1),("A4",2),("G4",1),("D4",2)]},
 "eight_shadows":{"instrument":"lute","bpm":86,"notes":[("D3",1),("A3",1),("D4",1),("F4",1),("D4",1),("A3",1),("C4",2),("D4",1),("F4",1),("A4",1),("F4",1),("D4",2),("C4",1),("A3",1),("D4",2)]},
 "lolth_hymn":{"bpm":96,"instrument":"piano","notes":[("D3",1),("A3",1),("D4",1),("D#4",1),("A3",1),("C4",1),("D#4",1),("F#4",1),("D4",2),("A3",1),("D#4",1),("D4",1),("C4",1),("A3",2)]},
 "eilistraee_hymn":{"bpm":108,"instrument":"piano","notes":[("D4",1),("F#4",1),("A4",1),("D5",1),("C#5",1),("A4",1),("F#4",1),("E4",1),("F#4",1),("A4",1),("B4",1),("D5",1),("A4",2),("F#4",2)]},
 "vhaeraun_hymn":{"bpm":104,"instrument":"piano","notes":[("E3",1),("B3",1),("E4",1),("G4",1),("F#4",1),("E4",1),("B3",1),("D4",1),("E3",1),("B3",1),("F#4",1),("G4",1),("B4",1),("F#4",1),("E4",2)]},
}

def hz(note):
    if note=="R": return 0.0
    names={"C":0,"C#":1,"D":2,"D#":3,"E":4,"F":5,"F#":6,"G":7,"G#":8,"A":9,"A#":10,"B":11}
    name=note[:-1];octave=int(note[-1]);midi=12*(octave+1)+names[name]
    return 440.0*2**((midi-69)/12)

def _piano(freq,t):
    if not freq:return 0.0
    # old upright: felted attack, woody body, slightly metallic upper strings
    attack=min(1.0,t/.006); body=math.exp(-1.65*t); upper=math.exp(-3.6*t)
    return attack*(body*(math.sin(2*math.pi*freq*t)+.31*math.sin(4*math.pi*freq*t)) + upper*.16*math.sin(6*math.pi*freq*t))/1.47

def _pluck(freq,t):
    if not freq:return 0.0
    # soft fantasy lyre: crisp pick, warm body, short sparkling upper partials
    body=math.exp(-3.15*t)
    sparkle=math.exp(-7.5*t)
    pick=math.exp(-18*t)*math.sin(2*math.pi*freq*3*t)
    return (body*(math.sin(2*math.pi*freq*t)+.24*math.sin(4*math.pi*freq*t)) + sparkle*.13*math.sin(6*math.pi*freq*t) + .08*pick)/1.34

def _voice_for(instrument):
    return _piano if instrument=="piano" else _pluck

def _arranged_notes(melody_id, target_seconds=55.0):
    m=MELODIES[melody_id]; motif=m["notes"]; beat=60/m["bpm"]
    # Keep the authored motif recognizable, then vary register/rest placement by cycling it.
    # This is intentionally deterministic so chart/audio duration stays reproducible.
    out=[]; elapsed=0.0; cycle=0
    while elapsed < target_seconds:
        for note,beats in motif:
            if elapsed >= target_seconds: break
            out.append((note,beats)); elapsed += beat*beats + .025
        cycle += 1
        if elapsed < target_seconds and cycle%2==0:
            out.append(("R",.5)); elapsed += beat*.5 + .025
    return out

def render(melody_id,out_path,target_seconds=55.0):
    m=MELODIES[melody_id]; beat=60/m["bpm"]; samples=[]; instrument=m.get("instrument","lyre"); voice=_voice_for(instrument)
    for note,beats in _arranged_notes(melody_id,target_seconds):
        dur=beat*beats; f=hz(note); n=int(SR*dur)
        for i in range(n):
            t=i/SR; x=voice(f,t)
            # lute is warmer/darker than lyre; piano keeps its own old-upright envelope.
            gain=.36 if instrument=="lute" else .42
            rel=min(1.0,(n-i)/(SR*.025))
            samples.append(int(max(-1,min(1,x*gain*rel))*32767))
        samples.extend([0]*int(SR*.025))
    path=Path(out_path);path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR)
        w.writeframes(struct.pack("<"+"h"*len(samples),*samples))
    return path

# v2 composition grammar: functional/modal harmony first, rhythm chart second.
# Chord symbols are MIDI-note voicings; melody uses scale-degree-ish MIDI notes.
COMPOSITIONS={
 "spider_rhythm":{"bpm":136,"style":"jazz","prog":[[52,55,59,62],[57,60,64,67],[50,54,57,60],[59,62,66,69]],"mel":[64,67,69,71,69,67,66,64]},
 "eight_shadows":{"bpm":86,"style":"lute","prog":[[50,57,62,65],[48,55,60,64],[46,53,58,62],[45,52,57,60]],"mel":[62,65,69,65,64,62,60,57]},
 "shadowlantern":{"bpm":84,"style":"modal","prog":[[50,57,62,65],[53,60,65,69],[48,55,60,64],[50,57,62,65]],"mel":[62,69,72,69,65,64,62,60]},
 "come_back_alive":{"bpm":94,"style":"ballad","prog":[[50,57,62,66],[55,59,62,67],[57,61,64,69],[50,57,62,66]],"mel":[62,66,69,71,69,66,64,62]},
 "tower_lights":{"bpm":88,"style":"newage","prog":[[48,55,60,64],[43,50,55,59],[45,52,57,60],[41,48,53,57]],"mel":[60,64,67,72,69,67,64,62]},
 "pet_song":{"bpm":124,"style":"minuet","prog":[[55,59,62,67],[50,57,62,66],[48,55,60,64],[50,57,62,66]],"mel":[67,71,74,71,69,67,64,62]},
 "lolth_hymn":{"bpm":96,"style":"baroque","prog":[[50,57,62,65],[46,53,58,62],[48,55,60,64],[45,52,57,61]],"mel":[62,65,69,67,65,62,60,61]},
 "eilistraee_hymn":{"bpm":108,"style":"impressionist","prog":[[50,57,62,66,69],[55,62,67,71,74],[52,59,64,69,71],[57,64,69,73,76]],"mel":[62,66,69,74,73,69,66,64]},
 "vhaeraun_hymn":{"bpm":104,"style":"darkjazz","prog":[[52,59,64,67],[48,55,60,64],[45,52,57,60],[47,54,59,63]],"mel":[64,67,71,69,67,64,62,63]},
}

def _midi_hz(n): return 440.0*2**((n-69)/12)

def _tone(freq,t,style):
    if style=="impressionist":
        attack=min(1.0,t/.018); body=math.exp(-1.25*t); return attack*body*(math.sin(2*math.pi*freq*t)+.12*math.sin(4*math.pi*freq*t))/1.12*.72
    if style=="newage": return _piano(freq,t)*.72
    if style in {"baroque","darkjazz","jazz","ballad","minuet"}: return _piano(freq,t)*.66
    return _pluck(freq,t)*.72

FORM_BY_STYLE={
 "jazz":["intro","a1","answer","bridge","lift","a2","bridge","climax","answer","return"],
 "lute":["intro","a1","a2","answer","bridge","a1","lift","climax","return"],
 "modal":["intro","bridge","a1","answer","a2","bridge","lift","return"],
 "ballad":["intro","a1","answer","bridge","a2","lift","climax","return"],
 "newage":["intro","a1","bridge","answer","a2","lift","bridge","climax","return"],
 "minuet":["intro","a1","answer","a2","bridge","a1","lift","answer","return"],
 "baroque":["intro","a1","a2","answer","bridge","lift","a1","climax","return"],
 "impressionist":["intro","a1","bridge","answer","lift","a2","bridge","climax","return"],
 "darkjazz":["intro","bridge","a1","answer","a2","lift","bridge","climax","answer","return"],
}


NATURAL_DUET_STYLES={"jazz","lute","modal","ballad","newage","minuet","baroque","impressionist","darkjazz"}

# Per-song form/phrase identities. Fractions are cumulative body positions.
# The shared renderer supplies instrumentation only; the musical route is authored here per piece.
SONG_SHAPES={
 "spider_rhythm":{"form":[(.10,"intro"),(.28,"a"),(.43,"b"),(.56,"a"),(.72,"lift"),(.86,"b"),(1.0,"return")],"phrases":[0,4,1,5,2,4,6,1],"cadence_beats":4.4},
 "eight_shadows":{"form":[(.14,"intro"),(.34,"a"),(.48,"a"),(.62,"b"),(.78,"lift"),(.90,"a"),(1.0,"return")],"phrases":[2,0,3,1,5,0,6],"cadence_beats":5.0},
 "shadowlantern":{"form":[(.18,"intro"),(.36,"a"),(.52,"b"),(.68,"a"),(.82,"b"),(1.0,"return")],"phrases":[3,0,2,5,3,1,6],"cadence_beats":5.8},
 "come_back_alive":{"form":[(.12,"intro"),(.32,"a"),(.49,"b"),(.63,"a"),(.78,"lift"),(.90,"b"),(1.0,"return")],"phrases":[0,1,5,2,4,6,1],"cadence_beats":5.3},
 "tower_lights":{"form":[(.17,"intro"),(.35,"a"),(.50,"b"),(.66,"a"),(.79,"lift"),(.91,"b"),(1.0,"return")],"phrases":[3,2,0,5,1,6,3],"cadence_beats":6.0},
 "pet_song":{"form":[(.08,"intro"),(.27,"a"),(.43,"b"),(.58,"a"),(.72,"b"),(.86,"lift"),(1.0,"return")],"phrases":[4,0,1,4,5,2,6,0],"cadence_beats":4.0},
 "lolth_hymn":{"form":[(.15,"intro"),(.31,"a"),(.45,"b"),(.59,"a"),(.73,"b"),(.87,"lift"),(1.0,"return")],"phrases":[2,5,1,3,5,6,2],"cadence_beats":5.6,"lift_octave":False},
 "eilistraee_hymn":{"form":[(.16,"intro"),(.34,"a"),(.48,"b"),(.61,"a"),(.76,"lift"),(.89,"b"),(1.0,"return")],"phrases":[3,0,2,1,6,4,3],"cadence_beats":6.2,"lift_octave":False},
 "vhaeraun_hymn":{"form":[(.11,"intro"),(.26,"b"),(.43,"a"),(.56,"b"),(.70,"a"),(.84,"lift"),(1.0,"return")],"phrases":[5,2,0,5,1,6,4,2],"cadence_beats":4.8,"lift_octave":False},
}

# Seven rhythm shapes; song-specific routes above choose how they recur.
PHRASE_PATTERNS={
 0:[(0,0,.8),(1,.9,.55),(2,1.65,.75),(3,2.65,.9)],
 1:[(4,0,.65),(3,.8,.5),(2,1.45,.65),(1,2.25,.5),(0,3.0,.85)],
 2:[(0,0,1.15),(2,1.35,.65),(4,2.15,1.35)],
 3:[(5,.25,.9),(6,1.45,.65),(7,2.35,1.25)],
 4:[(0,0,.45),(3,.55,.55),(5,1.25,.65),(7,2.05,.45),(4,2.65,1.0)],
 5:[(2,0,.55),(1,.7,.45),(4,1.35,.7),(3,2.2,.45),(6,2.8,.8)],
 6:[(0,0,.5),(2,.55,.5),(4,1.1,.55),(6,1.75,.55),(7,2.4,1.25)],
}

def _render_natural_duet(melody_id,c,out_path,target_seconds=56.0):
    """Render a song-specific duet on a strict beat grid with a resolved tail."""
    shape=SONG_SHAPES[melody_id]; beat=60/c["bpm"]; bar=beat*4; total=int(SR*target_seconds); mix=[0.0]*total
    def add(midi,start,dur,gain,voice):
        if start>=target_seconds or dur<=0:return
        a=max(0,int(start*SR)); z=min(total,a+int(dur*SR)); f=_midi_hz(midi)
        for i in range(a,z):
            t=(i-a)/SR; rel=min(1.0,(z-i)/(SR*.055)); mix[i]+=voice(f,t)*gain*rel
    def accompaniment(ch,start,section,bi):
        energy={"intro":.66,"a":.88,"b":.78,"lift":1.0,"return":.72}[section]
        backing=_pluck if c['style'] in {'lute','modal'} else _piano
        bass_start=start+(beat*.25 if c['style'] in {'jazz','darkjazz'} and bi%2 else 0); add(ch[0]-12+(12 if bi%7==6 and section=='lift' else 0),bass_start,beat*(1.35 if section=='b' else 1.75),.092*energy,backing)
        upper=ch[1:]
        if section in {"intro","return"}:
            for j,n in enumerate(upper[:3]): add(n,start+(1+j)*beat,beat*.72,.058*energy,backing)
        elif c['style'] in {'jazz','darkjazz'}:
            # Off-beat answers keep the two jazz pieces moving without four-on-the-floor repetition.
            for j,n in enumerate((upper+upper[:1])[:4]): add(n,start+((.5 if bi%2==0 else .75)+j)*beat,beat*(.44 if bi%3==1 else .52),.052*energy,backing)
        elif section=='b':
            for j,n in enumerate(upper[:3]): add(n,start+((1.25 if bi%2 else 1.5)+j*(.65 if bi%3 else .75))*beat,beat*(.54 if bi%2 else .62),.050*energy,backing)
        else:
            seq=(upper[:3]+upper[1:3]) if len(upper)>=3 else upper
            for j,n in enumerate(seq[:5]): add(n,start+((.75 if bi%3==2 else 1)+j*(.5 if bi%2==0 else .6))*beat,beat*(.36 if bi%2 else .40),.049*energy,backing)
    def section_for(pos):
        for edge,name in shape['form']:
            if pos < edge:return name
        return 'return'
    def melody_line(pattern,section,bi):
        m=c['mel']; line=[]
        for j,(idx,off,dur) in enumerate(PHRASE_PATTERNS[pattern]):
            n=m[idx%len(m)]
            if section=='intro': n-=12
            elif section=='lift' and shape.get('lift_octave',True) and j in {1,3}: n+=12
            elif section=='return' and j>=3: n=m[0]
            line.append((n,off,dur))
        # Adjacent repetitions answer instead of cloning: octave/register only, no chromatic mutation.
        if bi%3==2 and section not in {'intro','return'}:
            line=[(n-(12 if j==0 else 0),off+.08*(j%2),dur*1.04) for j,(n,off,dur) in enumerate(line)]
        return line
    cadence=max(0,target_seconds-max(4.0,beat*shape['cadence_beats']))
    bars=max(1,int(cadence/bar))
    for bi in range(bars):
        start=bi*bar
        if start>=cadence:break
        pos=(bi+.5)/bars; section=section_for(pos)
        # Chord order also differs by phrase family, avoiding identical 1-2-3-4 loops across songs.
        cycle=bi//len(shape['phrases']); base=shape['phrases'][bi%len(shape['phrases'])]
        sec_shift={'intro':0,'a':1,'b':3,'lift':5,'return':2}[section]
        pidx=(base+cycle+sec_shift)%len(PHRASE_PATTERNS)
        ch=c['prog'][(bi+(pidx%3)+cycle)%len(c['prog'])]
        accompaniment(ch,start,section,bi)
        gain=.10 if section in {'intro','return'} else (.14 if section=='lift' else .12)
        for n,off,dur in melody_line(pidx,section,bi): add(n,start+off*beat,dur*beat,gain,_pluck)
    # Dedicated dominant -> tonic cadence; final 0.9 s is master-faded, never hard-clipped.
    dom=c['prog'][-1]; tonic=c['prog'][0]
    for n in dom[1:]: add(n,cadence,beat*.9,.052,_piano)
    add(c['mel'][-2],cadence,beat*.82,.10,_pluck)
    res=cadence+beat*1.18
    tail=max(beat*2.25,target_seconds-res-.08)
    for n in tonic:add(n,res,tail,.066,_piano)
    add(c['mel'][0],res,tail,.12,_pluck)
    peak=max(1e-9,max(abs(x) for x in mix)); scale=.76/peak
    fade_start=max(0,total-int(SR*.9)); vals=[]
    for i,x in enumerate(mix):
        fade=1.0 if i<fade_start else max(0.0,(total-1-i)/max(1,total-1-fade_start))
        vals.append(int(max(-1,min(1,x*scale*fade))*32767))
    path=Path(out_path);path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes(struct.pack('<'+'h'*len(vals),*vals))
    return path

def render_composition(melody_id,out_path,target_seconds=56.0):
    """Render a continuous short-form piece with song-specific section pacing and a resolved tail."""
    c=COMPOSITIONS[melody_id]
    if c["style"] in NATURAL_DUET_STYLES:
        return _render_natural_duet(melody_id,c,out_path,target_seconds)
    beat=60/c["bpm"]; total=int(SR*target_seconds); mix=[0.0]*total; bar=beat*4
    def add_note(midi,start,dur,gain):
        if start>=target_seconds or dur<=0:return
        a=max(0,int(start*SR));z=min(total,a+int(dur*SR));f=_midi_hz(midi)
        for i in range(a,z):
            t=(i-a)/SR; rel=min(1.0,(z-i)/(SR*.06)); mix[i]+=_tone(f,t,c["style"])*gain*rel
    def harmony(chord,start,energy,texture,variant):
        bass=chord[0]-12+(12 if variant%4==3 else 0);add_note(bass,start,bar*.82,.13*energy)
        upper=chord[1:]
        if variant%2: upper=upper[1:]+upper[:1]
        if texture=='air':
            for j,n in enumerate(upper):add_note(n,start+(j*.72+1)*beat,beat*(1.0+.12*(variant%2)),.075*energy)
        elif texture=='drive':
            for q in range(4):
                for n in upper[:2]:add_note(n,start+q*beat,beat*.42,.062*energy)
        else:
            seq=upper+upper[-2:0:-1]
            for j,n in enumerate(seq):add_note(n,start+j*beat*.5,beat*.65,.073*energy)
    def line_for(role,bi):
        m=c['mel'];v=bi%4
        variants={
          'intro':[(m[0]-12,1.0,1.5),(m[2]-12,2.75,.7)],
          'a1':[(m[0],.25,.65),(m[1],1,.55),(m[2],1.75,.8),(m[3],2.75,.7)],
          'a2':[(m[2],.0,.5),(m[3],.65,.6),(m[4],1.5,.55),(m[2],2.15,.5),(m[1],3,.75)],
          'answer':[(m[4],.0,.7),(m[3],.85,.5),(m[2],1.5,.65),(m[1],2.35,.5),(m[0],3,.85)],
          'bridge':[(m[5]-12,.25,.9),(m[6]-12,1.4,.65),(m[7]-12,2.25,1.2)],
          'lift':[(m[2]+(0 if c['style'] in {'impressionist','baroque','darkjazz'} else 12),.0,.45),(m[3]+(0 if c['style'] in {'impressionist','baroque','darkjazz'} else 12),.55,.45),(m[4]+(0 if c['style'] in {'impressionist','baroque','darkjazz'} else 12),1.1,.7),(m[5]+(0 if c['style'] in {'impressionist','baroque','darkjazz'} else 12),2,.45),(m[6]+(0 if c['style'] in {'impressionist','baroque','darkjazz'} else 12),2.6,.85)],
          'climax':[(m[0]+(0 if c['style'] in {'impressionist','baroque','darkjazz'} else 12),.0,.45),(m[2]+(0 if c['style'] in {'impressionist','baroque','darkjazz'} else 12),.5,.45),(m[4]+(0 if c['style'] in {'impressionist','baroque','darkjazz'} else 12),1,.5),(m[3]+(0 if c['style'] in {'impressionist','baroque','darkjazz'} else 12),1.6,.45),(m[6]+(0 if c['style'] in {'impressionist','baroque','darkjazz'} else 12),2.15,.5),(m[7]+(0 if c['style'] in {'impressionist','baroque','darkjazz'} else 12),2.75,1.0)],
          'return':[(m[0],.0,.7),(m[1],.9,.55),(m[2],1.6,.6),(m[4],2.4,.55),(m[0],3.15,.7)],
        }
        line=list(variants[role])
        # Adjacent bars within a section answer each other instead of cloning the same phrase.
        if role not in {'intro','return'}:
            if v==1: line=[(n+(12 if j in (1,3) else 0),off+.08*(j%2),dur*.92) for j,(n,off,dur) in enumerate(line)]
            elif v==2: line=[(n-(12 if j==0 else 0),max(0,off-.08*(j%2)),dur*1.06) for j,(n,off,dur) in enumerate(reversed(line))]
            elif v==3: line=[(n+(2 if j%2==0 else -1),off+.12,dur*.86) for j,(n,off,dur) in enumerate(line)]
        return line
    route=FORM_BY_STYLE[c['style']]
    cadence=max(0,target_seconds-max(3.4,beat*4.2))
    body_bars=max(1,int(math.ceil(cadence/bar)))
    for bi in range(body_bars):
        start=bi*bar
        if start>=cadence: break
        pos=(bi+.5)/body_bars; ri=min(len(route)-1,int(pos*len(route)));role=route[ri]
        chord=c['prog'][(bi+(ri%2))%len(c['prog'])]
        energy={'intro':.52,'bridge':.66,'lift':.96,'climax':1.12,'return':.76}.get(role,.84)
        texture='air' if role in {'intro','bridge','return'} else ('drive' if role in {'lift','climax'} else 'flow')
        harmony(chord,start,energy,texture,bi)
        for n,off,dur in line_for(role,bi):add_note(n,start+off*beat,dur*beat,.19*energy)
    # Clear dominant -> tonic ending, then a short master fade so the WAV boundary never sounds chopped.
    dom=c['prog'][-1]; tonic=c['prog'][0]
    for n in dom[1:]:add_note(n,cadence,beat*.72,.07)
    add_note(c['mel'][-2],cadence,beat*.75,.18)
    res=cadence+beat*.92
    tail_dur=max(beat*2.15,target_seconds-res-.08)
    for n in tonic:add_note(n,res,tail_dur,.09)
    add_note(c['mel'][0],res,tail_dur,.23)
    peak=max(1e-9,max(abs(x) for x in mix));scale=.78/peak
    fade_start=max(0,total-int(SR*.85))
    vals=[]
    for i,x in enumerate(mix):
        fade=1.0 if i<fade_start else max(0.0,(total-1-i)/max(1,total-1-fade_start))
        vals.append(int(max(-1,min(1,x*scale*fade))*32767))
    path=Path(out_path);path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes(struct.pack('<'+'h'*len(vals),*vals))
    return path

if __name__=="__main__":
    import sys
    if len(sys.argv)==3: (render_composition(sys.argv[1],sys.argv[2]) if sys.argv[1] in COMPOSITIONS else render(sys.argv[1],sys.argv[2]))
    else:
        out=Path("assets/music")
        for key in MELODIES: render(key,out/f"{key}.wav")
