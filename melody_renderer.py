"""루바토 레퍼토리의 짧은 원곡 선율과 WAV 렌더러.

외부 음원 없이 합성하므로 melody_id를 연주/작곡 시스템에서 그대로 재사용할 수 있다.
"""
from __future__ import annotations
import math, struct, wave
from pathlib import Path

SR=44100
# (note, beats); R = rest
MELODIES={
 "pet_song": {"bpm":112,"notes":[("G4",1),("B4",1),("D5",1),("B4",1),("A4",1),("G4",1),("E4",2),("G4",1),("A4",1),("B4",1),("D5",1),("B4",1),("A4",1),("G4",2)]},
 "spider_rhythm":{"bpm":126,"notes":[("E4",.5),("G4",.5),("A4",1),("E4",.5),("G4",.5),("B4",1),("A4",.5),("B4",.5),("D5",1),("B4",.5),("A4",.5),("G4",1),("E4",2)]},
 "come_back_alive":{"bpm":82,"notes":[("D4",1),("F4",1),("A4",2),("G4",1),("F4",1),("D4",2),("F4",1),("G4",1),("A4",1),("C5",1),("A4",2),("G4",1),("F4",1),("D4",2)]},
 "tower_lights":{"bpm":76,"notes":[("C4",1),("E4",1),("G4",2),("E4",1),("G4",1),("A4",2),("G4",1),("E4",1),("D4",2),("E4",1),("G4",1),("C5",2)]},
 "shadowlantern":{"bpm":70,"notes":[("D4",1.5),("A4",.5),("C5",1),("A4",1),("F4",2),("R",1),("D4",1),("F4",1),("A4",1),("C5",1),("A4",2),("G4",1),("D4",2)]},
 "eight_shadows":{"bpm":72,"notes":[("D3",1),("A3",1),("D4",1),("F4",1),("D4",1),("A3",1),("C4",2),("D4",1),("F4",1),("A4",1),("F4",1),("D4",2),("C4",1),("A3",1),("D4",2)]},
}

def hz(note):
    if note=="R": return 0.0
    names={"C":0,"C#":1,"D":2,"D#":3,"E":4,"F":5,"F#":6,"G":7,"G#":8,"A":9,"A#":10,"B":11}
    name=note[:-1];octave=int(note[-1]);midi=12*(octave+1)+names[name]
    return 440.0*2**((midi-69)/12)

def _pluck(freq,t):
    if not freq:return 0.0
    # soft synthetic lyre: fast pluck + two gentle harmonics
    env=math.exp(-3.7*t)
    return env*(math.sin(2*math.pi*freq*t)+.28*math.sin(4*math.pi*freq*t)+.10*math.sin(6*math.pi*freq*t))/.0 if False else env*(math.sin(2*math.pi*freq*t)+.28*math.sin(4*math.pi*freq*t)+.10*math.sin(6*math.pi*freq*t))/1.38

def render(melody_id,out_path):
    m=MELODIES[melody_id]; beat=60/m["bpm"]; samples=[]
    for note,beats in m["notes"]:
        dur=beat*beats; f=hz(note); n=int(SR*dur)
        for i in range(n):
            t=i/SR; x=_pluck(f,t)
            # short release to avoid clicks
            rel=min(1.0,(n-i)/(SR*.025))
            samples.append(int(max(-1,min(1,x*.42*rel))*32767))
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
