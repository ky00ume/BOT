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

if __name__=="__main__":
    import sys
    if len(sys.argv)==3: render(sys.argv[1],sys.argv[2])
    else:
        out=Path("assets/music")
        for key in MELODIES: render(key,out/f"{key}.wav")
