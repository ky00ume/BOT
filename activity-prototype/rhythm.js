(()=>{
'use strict';
const BPM=136,BEAT=60000/BPM;
const MODES={
 easy:{keys:['d','f','j','k'],label:'EASY · 4K',pattern:[0,1,2,3,1,2,0,3,0,2,1,3,0,1,2,3,1,3,0,2,0,1,3,2,1,2,0,3,0,2,3,1]},
 hard:{keys:['a','s','d','f','h','j','k','l'],label:'EXPERT · 8K',pattern:[0,4,2,6,1,5,3,7,0,3,4,7,1,2,5,6,0,4,1,5,2,6,3,7,0,2,4,6,1,3,5,7,0,7,2,5,1,6,3,4,0,4,2,6,1,5,3,7,0,3,5,7,1,2,4,6,0,4,1,5,2,6,3,7]}
};
const els={stage:q('#stage'),lanes:q('#lanes'),judge:q('#judge'),countdown:q('#countdown'),score:q('#score'),combo:q('#combo'),status:q('#status'),accuracy:q('#accuracy'),song:q('#song'),start:q('#start'),speed:q('#speed'),runes:q('#runes'),phase:q('#phase'),memory:q('#memory')};
let mode=new URLSearchParams(location.search).get('drill')==='1'?'hard':'easy',chart=[],running=false,starting=false,runId=0,startAt=0,raf=0,combo=0,score=0,hits=0,judged=0,totalErr=0,runes=0,phase='theme',memory=[],improvStart=0,improvEnd=0,callPlayed=false,responseRule='mirror',assist=0,recent=[];
const pressedKeys=new Set(),activeHolds=new Map(),travel=1800,windows={perfect:45,great:85,good:130};
function q(s){return document.querySelector(s)}
function playbackSpeed(){return Number(els.speed.value)||1}
function makeNote(t,lane,type='normal',duration=0,meta={}){return{t,lane,type,duration,releaseOnly:!!meta.releaseOnly,charge:!!meta.charge,hit:false,miss:false,holdState:duration?'pending':null,el:null}}
const Patterns={
 tap:(t,lane)=>[makeNote(t,lane)],
 chord:(t,lanes)=>lanes.map(l=>makeNote(t,l)),
 hold:(t,lane,duration,meta={})=>[makeNote(t,lane,'normal',duration,meta)],
 multiHold:(t,lanes,duration)=>lanes.map(l=>makeNote(t,l,'normal',duration)),
 release:(t,lane,duration)=>[makeNote(t,lane,'normal',duration,{releaseOnly:true})],
 charge:(t,lane,duration)=>[makeNote(t,lane,'normal',duration,{charge:true})],
 jack:(t,lane,count,step)=>Array.from({length:count},(_,i)=>makeNote(t+i*step,lane)),
 trill:(t,a,b,count,step)=>Array.from({length:count},(_,i)=>makeNote(t+i*step,i%2?a:b)),
 stair:(t,lanes,step)=>lanes.map((l,i)=>makeNote(t+i*step,l)),
 roll:(t,lanes,count,step)=>Array.from({length:count},(_,i)=>makeNote(t+i*step,lanes[i%lanes.length])),
 cross:(t,left,right,count,step)=>Array.from({length:count},(_,i)=>makeNote(t+i*step,i%2?right[i%right.length]:left[i%left.length])),
 rearticulate:(t,lane,hold,step)=>[makeNote(t,lane,'normal',hold),makeNote(t+hold+step,lane)],
 // Signature phrase: left-hand hold, right-hand trill, then release into a two-hand chord.
 holdTrillReleaseChord:(t,holdLane,trillLanes,chordLanes,duration,step)=>[
  makeNote(t,holdLane,'normal',duration,{releaseOnly:true}),
  ...Array.from({length:6},(_,i)=>makeNote(t+step*(i+1),trillLanes[i%trillLanes.length])),
  ...chordLanes.map(l=>makeNote(t+duration,l))
 ]
};
function buildPatternDrill(speed=1){
 const b=BEAT/speed,q=b/2,notes=[];let at=900/speed;
 const add=(pattern,gap=b*.75)=>{notes.push(...pattern);const end=Math.max(...pattern.map(n=>n.t+(n.duration||0)));at=end+gap};
 add(Patterns.tap(at,2));
 add(Patterns.chord(at,[1,6]));
 add(Patterns.hold(at,2,b*2));
 add(Patterns.multiHold(at,[1,6],b*2));
 add(Patterns.jack(at,0,8,q));
 add(Patterns.trill(at,2,5,10,q));
 add(Patterns.stair(at,[0,1,2,3,4,5,6,7],q));
 add(Patterns.roll(at,[0,2,4,6,7,5,3,1],12,q));
 add(Patterns.cross(at,[0,1,2,3],[7,6,5,4],12,q));
 add(Patterns.release(at,3,b*2));
 add(Patterns.charge(at,4,b*2.5));
 add(Patterns.rearticulate(at,2,b*1.5,q));
 add(Patterns.holdTrillReleaseChord(at,2,[5,6],[1,6],b*2,q/2),b);
 // Closing exam: two sustained hands with taps between them, then a final chord.
 notes.push(...Patterns.multiHold(at,[0,7],b*3));
 notes.push(...Patterns.trill(at+q,2,5,8,q/2));
 notes.push(...Patterns.chord(at+b*3,[1,3,4,6]));
 return notes.sort((a,b)=>a.t-b.t||a.lane-b.lane);
}
function buildChart(){
 const speed=playbackSpeed(),interval=mode==='easy'?BEAT:BEAT/2;
 if(mode==='hard'&&new URLSearchParams(location.search).get('drill')==='1'){
  chart=buildPatternDrill(speed);improvStart=improvEnd=Infinity;return;
 }

 const base=MODES[mode].pattern.map((lane,i)=>makeNote((900+i*interval)/speed,lane));
 if(mode==='hard'){
  // Expert combines simultaneous two-lane chords with sustained notes; EASY stays a clean 4K chart.
  [8,24,40,56].forEach(i=>base.push(makeNote((900+i*interval)/speed,(MODES.hard.pattern[i]+4)%8)));
  [5,17,33,49].forEach(i=>{base[i].duration=BEAT*1.5/speed;base[i].holdState='pending'});
 }
 if(mode==='hard'){
  const t=(900+60*interval)/speed,step=BEAT/4/speed;
  base.push(...Patterns.jack(t,0,4,step));
  base.push(...Patterns.trill(t+BEAT/speed,2,5,6,step));
  base.push(...Patterns.stair(t+BEAT*2.5/speed,[0,1,2,3,4,5,6,7],step));
  base.push(...Patterns.roll(t+BEAT*4.5/speed,[0,2,4,6],8,step));
  base.push(...Patterns.cross(t+BEAT*6.5/speed,[0,1,2,3],[7,6,5,4],8,step));
  base.push(...Patterns.multiHold(t+BEAT*8.5/speed,[1,6],BEAT/speed));
  base.push(...Patterns.release(t+BEAT*10/speed,3,BEAT/speed));
  base.push(...Patterns.charge(t+BEAT*11.5/speed,4,BEAT*1.5/speed));
  base.push(...Patterns.rearticulate(t+BEAT*13.5/speed,2,BEAT*.75/speed,step));
  // One deliberately vicious phrase: hold D, trill J/K, release D exactly as S+K lands.
  base.push(...Patterns.holdTrillReleaseChord(t+BEAT*15/speed,2,[5,6],[1,6],BEAT*2/speed,step));
 }
 base.sort((a,b)=>a.t-b.t||a.lane-b.lane);chart=base;
 if(mode==='hard'){
  const end=Math.max(...base.map(n=>n.t)),recall=[];
  for(let i=0;i<8;i++)recall.push(makeNote(end+BEAT/speed+i*interval/speed,i%8,'response'));
  chart=chart.concat(recall);
  const original=MODES.hard.pattern.length,step=interval/speed;
  improvStart=(900+Math.floor(original*.55)*interval)/speed;
  improvEnd=(900+Math.floor(original*.72)*interval)/speed;
  // An eight-note response slot follows the main phrase; recorded improv changes its lane and rhythm.
  const responseStart=recall[0].t,responseSpan=recall[recall.length-1].t-responseStart;
  recall.forEach((n,i)=>{n.t=responseStart+i*responseSpan/7});
 }
}
function buildLanes(){els.lanes.innerHTML='';els.lanes.className='lanes '+(mode==='hard'?'hard':'');MODES[mode].keys.forEach(k=>{const lane=document.createElement('div');lane.className='lane';lane.innerHTML=`<span class="lane-key">${k.toUpperCase()}</span>`;els.lanes.appendChild(lane)})}
function reset(){cancelAnimationFrame(raf);els.song.pause();els.song.currentTime=0;running=false;combo=score=hits=judged=totalErr=runes=0;phase='theme';memory=[];callPlayed=false;responseRule=['echo','mirror','harmony'][Math.floor(Math.random()*3)];assist=0;recent=[];pressedKeys.clear();activeHolds.clear();els.stage.classList.remove('improv','awakened');buildChart();buildLanes();updateHud();els.judge.textContent='READY';els.judge.className='judge';els.phase.textContent='주제';els.memory.textContent=mode==='hard'?'즉흥 프레이즈를 기다리는 중':'정석 연주';renderRunes()}
function renderRunes(){els.runes.innerHTML='';for(let i=0;i<4;i++){const r=document.createElement('i');r.textContent='◇';r.className=i<runes?'lit':'';els.runes.appendChild(r)}}
function updateHud(){els.score.textContent=String(score).padStart(6,'0');els.combo.textContent=`COMBO ${combo}`;els.accuracy.textContent=judged?`ACC ${(Math.max(0,100-totalErr/judged/1.3)).toFixed(2)}%`:'ACC --%'}
function flash(t,c){els.judge.textContent=t;els.judge.className='judge '+c}
function now(){return performance.now()-startAt}
function grade(err){if(err<=windows.perfect)return{pts:1000,text:'PERFECT',cls:'perfect'};if(err<=windows.great)return{pts:700,text:'GREAT',cls:'great'};return{pts:400,text:'GOOD',cls:'good'}}
function award(err){adapt(true);const result=grade(err);judged++;totalErr+=err;combo++;score+=result.pts+Math.min(combo,100)*5;flash(result.text,result.cls);if(mode==='hard'&&result.cls==='perfect'&&runes<4&&combo%6===0){runes++;renderRunes();if(runes===4){flash('RUNE AWAKENED','perfect');els.stage.classList.add('awakened')}}updateHud()}
function adapt(ok){if(mode!=='hard')return;recent.push(ok);if(recent.length>10)recent.shift();const rate=recent.filter(Boolean).length/recent.length,old=assist;if(recent.length>=5){if(rate<.45)assist=2;else if(rate<.7)assist=1;else if(rate>.9)assist=0}if(old!==assist)els.status.textContent=assist===2?'루바토가 박자를 넓게 받아줍니다':assist===1?'루바토가 손을 맞춰 줍니다':`${MODES[mode].label} · 연주 기억/룬 변주 활성`}function miss(text='MISS'){judged++;totalErr+=130;combo=0;adapt(false);flash(text,'miss');updateHud()}
function enterImprov(){phase='improv';els.phase.textContent='자유 즉흥';els.memory.textContent='원하는 키를 눌러 8음을 남기세요';els.stage.classList.add('improv');chart.forEach(n=>{if(n.type==='normal'&&n.t>=improvStart&&n.t<improvEnd){n.hit=true;if(n.el)n.el.remove()}})}
function playRubatoCall(){if(callPlayed)return;callPlayed=true;const C=window.AudioContext||window.webkitAudioContext,ctx=new C(),seq=[0,2,4,7,5,3,6,1],base=329.63;seq.forEach((lane,i)=>{const o=ctx.createOscillator(),g=ctx.createGain(),t=ctx.currentTime+i*.16;o.type='triangle';o.frequency.value=base*Math.pow(2,lane/12);g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.07,t+.015);g.gain.exponentialRampToValueAtTime(.0001,t+.13);o.connect(g).connect(ctx.destination);o.start(t);o.stop(t+.14)});els.memory.textContent='루바토의 프레이즈를 듣고 응답하세요';flash('RUBATO CALL','perfect')}
function enterResponse(){phase='response';playRubatoCall();els.phase.textContent='응답 연주';els.stage.classList.remove('improv');const response=chart.filter(n=>n.type==='response'),names={echo:'그대로 복창',mirror:'좌우 반전',harmony:'화음 응답'};if(memory.length){const min=memory[0].dt,max=memory[memory.length-1].dt,span=max-min;response.forEach((n,i)=>{const m=memory[i%memory.length];n.lane=responseRule==='echo'?m.lane:responseRule==='mirror'?7-m.lane:(m.lane+2)%8;const normalized=span>0?(m.dt-min)/span:i/Math.max(1,response.length-1);n.t=response[0].t+normalized*(response[response.length-1].t-response[0].t)});if(assist>=2&&responseRule==='harmony')responseRule='echo';if(assist>=1)response.forEach((n,i)=>{if(i%3===2)n.skip=true});if(responseRule==='harmony'&&assist===0){const extras=response.slice(0,4).map(n=>makeNote(n.t,(n.lane+4)%8,'response'));chart.push(...extras);chart.sort((a,b)=>a.t-b.t)}els.memory.textContent=`루바토의 요구 · ${names[responseRule]}`;flash(names[responseRule].toUpperCase(),'perfect')}else els.memory.textContent='기억된 음이 없어 기본 응답'}
function phaseUpdate(t){if(mode!=='hard')return;if(phase==='theme'&&t>=improvStart)enterImprov();if(phase==='improv'&&t>=improvEnd)enterResponse()}
function frame(){if(!running)return;const t=now(),h=els.stage.clientHeight,judgeY=h-49;phaseUpdate(t);chart.forEach(n=>{
 if(n.holdState==='holding'&&t>n.t+n.duration+windows.good){n.holdState='failed';activeHolds.delete(n.lane);miss('HOLD MISS')}
 if(n.hit||n.miss||n.skip)return;const dt=n.t-t;if(dt < -windows.good){n.miss=true;if(n.holdState)n.holdState='failed';miss(n.type==='response'?'RESPONSE MISS':'MISS');if(n.el)n.el.remove();return}if(dt>travel||dt<-windows.good)return;
 if(!n.el){n.el=document.createElement('div');n.el.className=`note ${n.type}${n.duration?' hold-note':''}`;els.lanes.children[n.lane].appendChild(n.el)}
 const y=judgeY-(dt/travel)*(judgeY-20),height=n.duration?Math.max(14,n.duration/travel*(judgeY-20)):14;n.el.style.height=`${height}px`;n.el.style.top=`${y-height+14}px`;
 });if(t>chart.at(-1).t+900){finish();return}raf=requestAnimationFrame(frame)}
function press(key){if(!running)return;const lane=MODES[mode].keys.indexOf(key);if(lane<0)return;pressedKeys.add(key);els.lanes.children[lane].classList.add('pressed');const t=now();
 if(mode==='hard'&&phase==='improv'){if(memory.length<8){memory.push({lane,dt:t-improvStart});els.memory.textContent=`기억한 프레이즈 ${memory.length}/8`;if(memory.length===8)flash('MEMORY SEALED','perfect')}return}
 let best=null,err=Infinity;chart.forEach(n=>{if(n.lane!==lane||n.hit||n.miss||n.skip)return;const e=Math.abs(n.t-t);if(e<err){err=e;best=n}});
 const adaptiveGood=windows.good+(assist*45);if(!best||err>adaptiveGood){combo=0;flash(phase==='response'?'RESPONSE':'MISS',phase==='response'?'great':'miss');updateHud();return}
 best.hit=true;hits++;award(err);if(best.duration){best.holdState='holding';activeHolds.set(lane,best);flash(best.charge?'CHARGE':best.releaseOnly?'RELEASE HOLD':'HOLD','great')}if(best.el){best.el.classList.add('hit');if(!best.duration)setTimeout(()=>best.el?.remove(),130)}
}
function release(key){const lane=MODES[mode].keys.indexOf(key);if(lane<0)return;pressedKeys.delete(key);els.lanes.children[lane]?.classList.remove('pressed');const note=activeHolds.get(lane);if(!note)return;activeHolds.delete(lane);if(note.holdState!=='holding')return;const err=Math.abs(now()-(note.t+note.duration));if(err<=windows.good){note.holdState='complete';award(err);if(note.releaseOnly)flash('RELEASE','perfect');else if(note.charge)flash('CHARGE RELEASE','perfect');if(note.el)note.el.classList.add('hold-complete')}else{note.holdState='failed';miss('HOLD MISS')}}
async function start(){reset();els.stage.focus();const drill=mode==='hard'&&new URLSearchParams(location.search).get('drill')==='1';els.status.textContent=drill?'EXPERT · 1분 패턴 테스트곡':`${MODES[mode].label} · ${mode==='hard'?'화음·홀드·즉흥 기억/응답 활성':'정석 연주'}`;for(const n of ['3','2','1']){els.countdown.textContent=n;await new Promise(r=>setTimeout(r,450))}els.countdown.textContent='';try{els.song.playbackRate=playbackSpeed();await els.song.play()}catch(e){els.status.textContent='오디오 재생을 시작하지 못했습니다. 다시 눌러 주세요.';return}startAt=performance.now()+900;running=true;raf=requestAnimationFrame(frame)}
function finish(){running=false;cancelAnimationFrame(raf);els.song.pause();els.stage.classList.remove('improv');const acc=judged?Math.max(0,100-totalErr/judged/1.3):0;flash(acc>=95?'FULL GROOVE':acc>=85?'CLEAR':'FINISH',acc>=85?'perfect':'great');els.status.textContent=`완주 · ${hits}/${chart.length} HIT · ${acc.toFixed(2)}% · 룬 ${runes}/4${memory.length?` · 기억 ${memory.length}음`:''}`}
document.querySelectorAll('.difficulty').forEach(b=>b.classList.toggle('active',b.dataset.mode===mode));document.querySelectorAll('.difficulty').forEach(b=>b.addEventListener('click',()=>{mode=b.dataset.mode;document.querySelectorAll('.difficulty').forEach(x=>x.classList.toggle('active',x===b));reset()}));
els.start.addEventListener('click',start);document.addEventListener('keydown',e=>{const k=e.key.toLowerCase();if(MODES[mode].keys.includes(k)){e.preventDefault();if(!e.repeat)press(k)}});document.addEventListener('keyup',e=>release(e.key.toLowerCase()));
reset();window.rhythmDemo={getState:()=>({mode,phase,score,combo,hits,judged,runes,memory:memory.length,notes:chart.map(n=>({t:n.t,lane:n.lane,type:n.type,duration:n.duration,releaseOnly:n.releaseOnly,charge:n.charge,hit:n.hit,holdState:n.holdState}))}),press,release,Patterns};
})();
