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
 "lolth_hymn":{"bpm":96,"style":"baroque","prog":[[50,57,62,65],[51,57,63,66],[48,55,60,63],[45,52,57,60]],"mel":[62,63,66,65,62,60,57,58]},
 "eilistraee_hymn":{"bpm":108,"style":"impressionist","prog":[[50,57,62,66,69],[55,62,67,71,74],[52,59,64,69,71],[57,64,69,73,76]],"mel":[74,78,81,86,85,81,78,76]},
 "vhaeraun_hymn":{"bpm":104,"style":"darkjazz","prog":[[52,59,62,67],[50,57,60,64],[48,55,59,63],[47,54,57,62]],"mel":[64,67,66,64,71,69,67,66]},
}

def _midi_hz(n): return 440.0*2**((n-69)/12)

def _tone(freq,t,style):
    if style in {"newage","impressionist"}: return _piano(freq,t)*.72
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

def render_composition(melody_id,out_path,target_seconds=56.0):
    """Render a continuous short-form piece with song-specific section pacing and a resolved tail."""
    c=COMPOSITIONS[melody_id]; beat=60/c["bpm"]; total=int(SR*target_seconds); mix=[0.0]*total; bar=beat*4
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
          'lift':[(m[2]+12,.0,.45),(m[3]+12,.55,.45),(m[4]+12,1.1,.7),(m[5]+12,2,.45),(m[6]+12,2.6,.85)],
          'climax':[(m[0]+12,.0,.45),(m[2]+12,.5,.45),(m[4]+12,1,.5),(m[3]+12,1.6,.45),(m[6]+12,2.15,.5),(m[7]+12,2.75,1.0)],
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
