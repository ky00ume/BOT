(()=>{
'use strict';
const SONGS={
 spider_rhythm:{title:'거미는 박자를 모른다',instrument:'LYRE',instrumentKo:'리라',bpm:136,audio:'assets/spider_rhythm.wav',lanes:[164.81,196,220,246.94,293.66,329.63,392,493.88],lyrics:['다리가 둘이면 하나 둘','다리가 넷이면 하나 둘 셋 넷','그런데 여덟 개가 우다다 오면','잠깐만, 처음부터 다시'],chartStyle:'spider'},
 eight_shadows:{title:'여덟 개의 그림자',instrument:'LUTE',instrumentKo:'류트',bpm:86,audio:'assets/eight_shadows.wav',lanes:[146.83,174.61,196,220,261.63,293.66,349.23,440],lyrics:['길 하나에 그림자는 여덟','어느 것이 먼저 닿아도','나는 뒤따라 걷지 않아','내 노래로 옆을 걸을 거야','듣고 있는지 묻지 않을게','대답 같은 것도 필요 없어','네가 저만큼 앞에 있다면','나는 여기서 계속 부를 테니'],chartStyle:'shadows'},
 shadowlantern:{title:'그림자등불',instrument:'LYRE',instrumentKo:'리라',bpm:84,audio:'assets/shadowlantern.wav',lanes:[146.83,174.61,220,261.63,293.66,349.23,440,523.25],lyrics:['손에 든 빛이 길을 비추면','그 빛은 누구의 것이 될까','쥔 사람의 것일까','따라가는 사람의 것일까','나는 등불을 들지 않을래','대신 네가 보이는 데 있을게','길을 잃으면 이름을 부르고','대답이 없으면 한 번 더 부를게'],chartStyle:'lantern'},
 come_back_alive:{title:'살아 돌아온 사람에게',instrument:'LUTE',instrumentKo:'류트',bpm:94,audio:'assets/come_back_alive.wav',lanes:[146.83,174.61,196,220,261.63,293.66,349.23,440],lyrics:['영웅이라 부르지 않아도 돼','멋진 이야기가 아니어도 돼','흙투성이 신발을 끌고 와서','여기 있다고 말해주면 돼','이긴 날은 크게 부르고','진 날에는 조금 작게 부르자','오늘 돌아온 사람에게는','내일 부를 노래가 있으니까'],chartStyle:'return'},
 tower_lights:{title:'탑에 불이 켜지는 시간',instrument:'LUTE',instrumentKo:'류트',bpm:88,audio:'assets/tower_lights.wav',lanes:[130.81,164.81,196,220,261.63,329.63,392,523.25],lyrics:['높은 창에 불이 하나','아래층에도 불이 하나','누가 돌아왔는지 묻지 않아도','오늘은 방들이 따뜻하네','먼저 온 사람은 기다리고','늦게 온 사람은 문을 열고','그렇게 하나씩 돌아오다 보면','커다란 탑도 집이 되네'],chartStyle:'tower'},
 pet_song:{title:'복복송',instrument:'LUTE',instrumentKo:'류트',bpm:124,audio:'assets/pet_song.wav',lanes:[164.81,196,220,246.94,293.66,329.63,392,493.88],lyrics:['복복 한 번, 복복 두 번','세 번째부터 세지 마세요','츄라이더가 납작해져도','행복한 거니까 계속하세요'],chartStyle:'pet'},
 lolth_hymn:{title:'거미줄 아래의 여덟 번째 기도',instrument:'PIANO',instrumentKo:'오래된 피아노',bpm:96,audio:'assets/lolth_hymn.wav',lanes:[146.83,174.61,220,233.08,261.63,293.66,369.99,440],lyrics:['여덟 번 얽힌 길 아래','낮은 기도는 이름을 감추고','한 줄이 다른 줄을 붙들 때','거미줄은 다시 문이 된다'],chartStyle:'lolth'},
 eilistraee_hymn:{title:'달빛 아래 맨발의 춤',instrument:'PIANO',instrumentKo:'오래된 피아노',bpm:108,audio:'assets/eilistraee_hymn.wav',lanes:[146.83,185,220,293.66,369.99,440,493.88,587.33],lyrics:['달빛이 칼끝에서 흘러','맨발의 원을 은빛으로 그리고','노래가 발보다 먼저 웃으면','밤은 잠시 길을 내어 준다'],chartStyle:'eilistraee'},
 vhaeraun_hymn:{title:'가면 뒤에 남긴 길',instrument:'PIANO',instrumentKo:'오래된 피아노',bpm:104,audio:'assets/vhaeraun_hymn.wav',lanes:[164.81,196,246.94,293.66,329.63,392,493.88,659.25],lyrics:['가면 아래 이름을 접어 두고','발소리 없는 계단을 오른다','보이지 않는 손이 길을 바꾸면','남은 그림자만 먼저 지나간다'],chartStyle:'vhaeraun'}
};
const params=new URLSearchParams(location.search);let songId=SONGS[params.get('song')]?params.get('song'):'spider_rhythm',SONG=SONGS[songId],BPM=SONG.bpm,BEAT=60000/BPM;
const MODES={
 easy:{keys:['d','f','j','k'],label:'EASY · 4K',pattern:[0,1,2,3,1,2,0,3,0,2,1,3,0,1,2,3,1,3,0,2,0,1,3,2,1,2,0,3,0,2,3,1]},
 hard:{keys:['a','s','d','f','h','j','k','l'],label:'EXPERT · 8K',pattern:[0,4,2,6,1,5,3,7,0,3,4,7,1,2,5,6,0,4,1,5,2,6,3,7,0,2,4,6,1,3,5,7,0,7,2,5,1,6,3,4,0,4,2,6,1,5,3,7,0,3,5,7,1,2,4,6,0,4,1,5,2,6,3,7]}
};
const els={stage:q('#stage'),lanes:q('#lanes'),judge:q('#judge'),countdown:q('#countdown'),score:q('#score'),combo:q('#combo'),status:q('#status'),accuracy:q('#accuracy'),song:q('#song'),start:q('#start'),speed:q('#speed'),runes:q('#runes'),phase:q('#phase'),memory:q('#memory'),playcombo:q('#playcombo'),result:q('#result'),resultRank:q('#resultRank'),resultScore:q('#resultScore'),resultAcc:q('#resultAcc'),resultPerfect:q('#resultPerfect'),resultGreat:q('#resultGreat'),resultGood:q('#resultGood'),resultMiss:q('#resultMiss'),resultCombo:q('#resultCombo'),resultRunes:q('#resultRunes'),resultClear:q('#resultClear'),resultRubato:q('#resultRubato'),resultAgain:q('#resultAgain'),songSelect:q('#songSelect'),songTitle:q('#songTitle'),instrumentLabel:q('#instrumentLabel'),lyrics:q('#lyrics'),lyricPrev:q('#lyricPrev'),lyricCurrent:q('#lyricCurrent'),lyricNext:q('#lyricNext')};
let mode=new URLSearchParams(location.search).get('drill')==='1'?'hard':'easy',chart=[],running=false,starting=false,runId=0,startAt=0,raf=0,combo=0,score=0,hits=0,judged=0,totalErr=0,runes=0,phase='theme',memory=[],improvStart=0,improvEnd=0,callPlayed=false,responseRule='mirror',assist=0,recent=[],counts={perfect:0,great:0,good:0,miss:0},maxCombo=0;
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
 const b=BEAT/speed,notes=[];let at=900/speed;
 const phrase=(pattern,bars=4)=>{notes.push(...pattern);at+=b*bars};
 // ~60 seconds at 136 BPM. Density grows in musical phrases rather than by adding random keys.
 phrase([...Patterns.tap(at,2),...Patterns.tap(at+b,5),...Patterns.chord(at+b*2,[2,5]),...Patterns.chord(at+b*3,[1,6])]);
 phrase(Patterns.jack(at,1,8,b/2));
 phrase(Patterns.trill(at,2,5,8,b/2));
 phrase(Patterns.stair(at,[0,1,2,3,4,5,6,7],b/2));
 phrase(Patterns.stair(at,[7,6,5,4,3,2,1,0],b/2));
 phrase(Patterns.roll(at,[0,2,4,6,7,5,3,1],8,b/2));
 phrase(Patterns.cross(at,[0,1,2,3],[7,6,5,4],8,b/2));
 notes.push(...Patterns.hold(at,1,b*4));notes.push(...Patterns.stair(at+b,[4,5,6,7,6,5],b/2));at+=b*4;
 notes.push(...Patterns.multiHold(at,[0,7],b*4));notes.push(...Patterns.trill(at+b,2,5,6,b/2));at+=b*4;
 phrase(Patterns.release(at,3,b*3));
 phrase(Patterns.charge(at,4,b*3));
 phrase(Patterns.rearticulate(at,2,b*2,b/2));
 phrase(Patterns.holdTrillReleaseChord(at,2,[5,6],[1,6],b*3,b/4));
 // Development: denser harmony and hand interaction.
 phrase([...Patterns.chord(at,[0,4]),...Patterns.chord(at+b,[1,5]),...Patterns.chord(at+b*2,[2,6]),...Patterns.chord(at+b*3,[3,7])]);
 notes.push(...Patterns.hold(at,0,b*4));notes.push(...Patterns.trill(at+b/2,4,6,12,b/4));at+=b*4;
 notes.push(...Patterns.hold(at,7,b*4));notes.push(...Patterns.trill(at+b/2,1,3,12,b/4));at+=b*4;
 phrase(Patterns.roll(at,[0,4,1,5,2,6,3,7],16,b/4));
 phrase([...Patterns.chord(at,[0,7]),...Patterns.chord(at+b,[1,6]),...Patterns.chord(at+b*2,[2,5]),...Patterns.chord(at+b*3,[3,4])]);
 notes.push(...Patterns.multiHold(at,[0,7],b*4));notes.push(...Patterns.trill(at+b/2,3,4,12,b/4));at+=b*4;
 // Coda cycle: repeat recognizable motifs with increasing chord density to carry the drill to ~60s.
 for(let cycle=0;cycle<3;cycle++){
  phrase(Patterns.trill(at,1+cycle,6-cycle,8,b/2));
  phrase(Patterns.roll(at,[0,2,4,6,7,5,3,1],8,b/2));
  phrase([...Patterns.chord(at,[0,4]),...Patterns.chord(at+b,[1,5]),...Patterns.chord(at+b*2,[2,6]),...Patterns.chord(at+b*3,[3,7])]);
 }
 phrase(Patterns.holdTrillReleaseChord(at,2,[5,6],[1,6],b*3,b/4));
 phrase(Patterns.stair(at,[0,1,2,3,4,5,6,7],b/2));
 phrase(Patterns.cross(at,[0,1,2,3],[7,6,5,4],8,b/2));
 phrase([...Patterns.chord(at,[0,7]),...Patterns.chord(at+b,[1,6]),...Patterns.chord(at+b*2,[2,5]),...Patterns.chord(at+b*3,[3,4])]);
 notes.push(...Patterns.multiHold(at,[0,7],b*4));notes.push(...Patterns.trill(at+b/2,3,4,12,b/4));at+=b*4;
 notes.push(...Patterns.chord(at,[1,3,4,6]));
 return notes.sort((a,b)=>a.t-b.t||a.lane-b.lane);
}
function buildSongChart(speed=1){
 const b=BEAT/speed,n=[];let at=900/speed;const add=x=>n.push(...x),bar=(x,beats=4)=>{add(x);at+=b*beats};
 if(SONG.chartStyle==='spider'){
  for(let c=0;c<7;c++){bar(Patterns.trill(at,2,5,8,b/2));bar(Patterns.roll(at,[0,2,4,6,7,5,3,1],8,b/2));if(c%2){bar(Patterns.cross(at,[0,1,2,3],[7,6,5,4],8,b/2));}}
  bar(Patterns.holdTrillReleaseChord(at,2,[5,6],[1,6],b*3,b/4));
 }else if(SONG.chartStyle==='shadows'){
  for(let c=0;c<6;c++){bar(Patterns.cross(at,[0,1,2,3],[4,5,6,7],8,b/2));bar(Patterns.stair(at,c%2?[7,6,5,4,3,2,1,0]:[0,1,2,3,4,5,6,7],b/2));bar([...Patterns.chord(at,[0,4]),...Patterns.chord(at+b*2,[3,7])]);}
 }else if(SONG.chartStyle==='lantern'){
  for(let c=0;c<6;c++){add(Patterns.hold(at,c%2?2:5,b*3));add(Patterns.stair(at+b/2,c%2?[7,6,4,3,1]:[0,1,3,4,6],b/2));at+=b*4;bar(Patterns.roll(at,[1,3,5,7,6,4,2,0],8,b/2));}
 }else if(SONG.chartStyle==='return'){
  for(let c=0;c<6;c++){bar([...Patterns.chord(at,[1,4]),...Patterns.chord(at+b,[2,5]),...Patterns.chord(at+b*2,[3,6]),...Patterns.chord(at+b*3,[0,7])]);bar(Patterns.stair(at,[0,2,4,6,7,5,3,1],b/2));bar(Patterns.multiHold(at,[1,6],b*3));}
 }else if(SONG.chartStyle==='tower'){
  for(let c=0;c<6;c++){bar(Patterns.stair(at,[0,1,2,3,4,5,6,7],b/2));bar([...Patterns.chord(at,[0,1]),...Patterns.chord(at+b,[2,3]),...Patterns.chord(at+b*2,[4,5]),...Patterns.chord(at+b*3,[6,7])]);bar(Patterns.stair(at,[7,5,3,1],b));}
 }else if(SONG.chartStyle==='pet'){
  for(let c=0;c<8;c++){bar(Patterns.jack(at,c%2?2:5,8,b/2));bar(Patterns.trill(at,1,6,8,b/2));if(c%2)bar([...Patterns.chord(at,[2,5]),...Patterns.chord(at+b*2,[1,6])]);}
 }else if(SONG.chartStyle==='lolth'){
  for(let cycle=0;cycle<6;cycle++){bar(Patterns.roll(at,[0,4,1,5,2,6,3,7],8,b/2));bar([...Patterns.chord(at,[0,4]),...Patterns.chord(at+b,[1,5]),...Patterns.chord(at+b*2,[2,6]),...Patterns.chord(at+b*3,[3,7])]);if(cycle%2===1){add(Patterns.multiHold(at,[0,7],b*3));add(Patterns.trill(at+b/2,2,5,10,b/4));at+=b*4}}
  bar(Patterns.holdTrillReleaseChord(at,2,[5,6],[1,6],b*3,b/4));bar(Patterns.chord(at,[0,2,5,7]));
 }else if(SONG.chartStyle==='eilistraee'){
  for(let cycle=0;cycle<6;cycle++){bar(Patterns.stair(at,cycle%2?[7,6,5,4,3,2,1,0]:[0,1,2,3,4,5,6,7],b/2));bar(Patterns.cross(at,[0,1,2,3],[4,5,6,7],8,b/2));bar(Patterns.roll(at,[2,4,6,7,5,3,1,0],8,b/2));}
  bar([...Patterns.chord(at,[1,4]),...Patterns.chord(at+b,[2,5]),...Patterns.chord(at+b*2,[3,6]),...Patterns.chord(at+b*3,[4,7])]);
 }else{
  for(let cycle=0;cycle<6;cycle++){add(Patterns.hold(at,cycle%2?1:0,b*4));add(Patterns.stair(at+b/2,cycle%2?[6,4,7,5,3,2]:[4,6,5,7,3,2],b/2));at+=b*4;bar(Patterns.cross(at,[0,1,2],[7,6,5],8,b/2));bar(Patterns.trill(at,2,6,8,b/2));}
  bar(Patterns.holdTrillReleaseChord(at,1,[5,7],[2,6],b*3,b/4));
 }
 return n.sort((a,b)=>a.t-b.t||a.lane-b.lane);
}
function buildChart(){
 const speed=playbackSpeed(),interval=mode==='easy'?BEAT:BEAT/2;
 if(SONG.chartStyle&&mode==='hard'){chart=buildSongChart(speed);improvStart=improvEnd=Infinity;return;}
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
function buildLanes(){els.lanes.innerHTML='';els.lanes.className='lanes '+(mode==='hard'?'hard':'');els.stage.querySelector('.receptors')?.remove();const deck=document.createElement('div');deck.className='receptors';MODES[mode].keys.forEach(k=>{const lane=document.createElement('div');lane.className='lane';els.lanes.appendChild(lane);const r=document.createElement('div');r.className='receptor';r.textContent=k.toUpperCase();deck.appendChild(r)});els.stage.appendChild(deck)}
function reset(){cancelAnimationFrame(raf);els.song.pause();els.song.currentTime=0;running=false;combo=score=hits=judged=totalErr=runes=0;phase='theme';memory=[];callPlayed=false;responseRule=['echo','mirror','harmony'][Math.floor(Math.random()*3)];assist=0;recent=[];counts={perfect:0,great:0,good:0,miss:0};maxCombo=0;els.result.classList.remove('show');els.result.setAttribute('aria-hidden','true');pressedKeys.clear();activeHolds.clear();els.stage.classList.remove('improv','awakened');buildChart();buildLanes();updateHud();els.judge.textContent='READY';els.judge.className='judge';els.phase.textContent='주제';els.memory.textContent=mode==='hard'?'즉흥 프레이즈를 기다리는 중':'정석 연주';renderRunes()}
const RUNE_SIGILS=[{glyph:'⚡',name:'폭풍'},{glyph:'≋',name:'천둥'},{glyph:'🔥',name:'지옥불'},{glyph:'✦',name:'비전'}];function renderRunes(){els.runes.innerHTML='';RUNE_SIGILS.forEach((sigil,i)=>{const r=document.createElement('i');r.textContent=sigil.glyph;r.title=sigil.name;r.setAttribute('aria-label',sigil.name);r.dataset.rune=sigil.name;r.className=i<runes?'lit':'';els.runes.appendChild(r)})}
function updateHud(){els.score.textContent=String(score).padStart(6,'0');els.combo.textContent=`COMBO ${combo}`;els.playcombo.querySelector('b').textContent=combo;els.playcombo.classList.toggle('live',combo>1);els.accuracy.textContent=judged?`ACC ${(Math.max(0,100-totalErr/judged/1.3)).toFixed(2)}%`:'ACC --%'}
function flash(t,c){els.judge.textContent=t;els.judge.className='judge '+c}
function now(){return performance.now()-startAt}
function grade(err){if(err<=windows.perfect)return{pts:1000,text:'PERFECT',cls:'perfect'};if(err<=windows.great)return{pts:700,text:'GREAT',cls:'great'};return{pts:400,text:'GOOD',cls:'good'}}
function award(err){adapt(true);const result=grade(err);judged++;totalErr+=err;combo++;counts[result.cls]++;maxCombo=Math.max(maxCombo,combo);score+=result.pts+Math.min(combo,100)*5;flash(result.text,result.cls);if(mode==='hard'&&result.cls==='perfect'&&runes<4&&combo%6===0){runes++;renderRunes();if(runes===4){flash('RUNE AWAKENED','perfect');els.stage.classList.add('awakened')}}updateHud()}
function adapt(ok){if(mode!=='hard')return;recent.push(ok);if(recent.length>10)recent.shift();const rate=recent.filter(Boolean).length/recent.length,old=assist;if(recent.length>=5){if(rate<.45)assist=2;else if(rate<.7)assist=1;else if(rate>.9)assist=0}if(old!==assist)els.status.textContent=assist===2?'루바토가 박자를 넓게 받아줍니다':assist===1?'루바토가 손을 맞춰 줍니다':`${MODES[mode].label} · 연주 기억/룬 변주 활성`}function miss(text='MISS'){judged++;counts.miss++;totalErr+=130;combo=0;adapt(false);flash(text,'miss');updateHud()}
function enterImprov(){phase='improv';els.phase.textContent='자유 즉흥';els.memory.textContent='원하는 키를 눌러 8음을 남기세요';els.stage.classList.add('improv');chart.forEach(n=>{if(n.type==='normal'&&n.t>=improvStart&&n.t<improvEnd){n.hit=true;if(n.el)n.el.remove()}})}
let instrumentCtx=null;const heldVoices=new Map();
// E-minor / G-major palette from 〈거미는 박자를 모른다〉 (E G A B D); arranged low→high for 8K hand voicing.
let LANE_FREQ=SONG.lanes;
function audioCtx(){const C=window.AudioContext||window.webkitAudioContext;if(!C)return null;if(!instrumentCtx)instrumentCtx=new C();if(instrumentCtx.state==='suspended')instrumentCtx.resume();return instrumentCtx}
function pluckLane(lane,hold=false){const ctx=audioCtx();if(!ctx)return;stopLane(lane,.025);const o=ctx.createOscillator(),g=ctx.createGain(),f=ctx.createBiquadFilter(),t=ctx.currentTime;o.type=SONG.instrument==='LUTE'?'sawtooth':'triangle';o.frequency.value=LANE_FREQ[lane];f.type='lowpass';f.frequency.value=SONG.instrument==='LUTE'?1450:SONG.instrument==='PIANO'?1900:2400;g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.065,t+.008);if(hold){g.gain.exponentialRampToValueAtTime(.025,t+.18)}else{g.gain.exponentialRampToValueAtTime(.0001,t+.32)}o.connect(f).connect(g).connect(ctx.destination);o.start(t);if(hold){heldVoices.set(lane,{o,g,ctx})}else{o.stop(t+.34)}}
function stopLane(lane,fade=.08){const v=heldVoices.get(lane);if(!v)return;const t=v.ctx.currentTime;try{v.g.gain.cancelScheduledValues(t);v.g.gain.setValueAtTime(Math.max(.0001,v.g.gain.value),t);v.g.gain.exponentialRampToValueAtTime(.0001,t+fade);v.o.stop(t+fade+.02)}catch{}heldVoices.delete(lane)}
function stopAllVoices(){[...heldVoices.keys()].forEach(l=>stopLane(l,.03))}
function playRubatoCall(){if(callPlayed)return;callPlayed=true;const C=window.AudioContext||window.webkitAudioContext,ctx=new C(),seq=[0,2,4,7,5,3,6,1],base=329.63;seq.forEach((lane,i)=>{const o=ctx.createOscillator(),g=ctx.createGain(),t=ctx.currentTime+i*.16;o.type='triangle';o.frequency.value=base*Math.pow(2,lane/12);g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.07,t+.015);g.gain.exponentialRampToValueAtTime(.0001,t+.13);o.connect(g).connect(ctx.destination);o.start(t);o.stop(t+.14)});els.memory.textContent='루바토의 프레이즈를 듣고 응답하세요';flash('RUBATO CALL','perfect')}
function enterResponse(){phase='response';playRubatoCall();els.phase.textContent='응답 연주';els.stage.classList.remove('improv');const response=chart.filter(n=>n.type==='response'),names={echo:'그대로 복창',mirror:'좌우 반전',harmony:'화음 응답'};if(memory.length){const min=memory[0].dt,max=memory[memory.length-1].dt,span=max-min;response.forEach((n,i)=>{const m=memory[i%memory.length];n.lane=responseRule==='echo'?m.lane:responseRule==='mirror'?7-m.lane:(m.lane+2)%8;const normalized=span>0?(m.dt-min)/span:i/Math.max(1,response.length-1);n.t=response[0].t+normalized*(response[response.length-1].t-response[0].t)});if(assist>=2&&responseRule==='harmony')responseRule='echo';if(assist>=1)response.forEach((n,i)=>{if(i%3===2)n.skip=true});if(responseRule==='harmony'&&assist===0){const extras=response.slice(0,4).map(n=>makeNote(n.t,(n.lane+4)%8,'response'));chart.push(...extras);chart.sort((a,b)=>a.t-b.t)}els.memory.textContent=`루바토의 요구 · ${names[responseRule]}`;flash(names[responseRule].toUpperCase(),'perfect')}else els.memory.textContent='기억된 음이 없어 기본 응답'}
function phaseUpdate(t){if(mode!=='hard')return;if(phase==='theme'&&t>=improvStart)enterImprov();if(phase==='improv'&&t>=improvEnd)enterResponse()}
function updateLyrics(t){const lines=SONG.lyrics||[];if(!lines.length)return;const end=chart.length?chart.at(-1).t+900:1,idx=Math.min(lines.length-1,Math.floor(Math.max(0,t)/end*lines.length));els.lyricPrev.textContent=idx?lines[idx-1]:'';els.lyricCurrent.textContent=lines[idx]||'';els.lyricNext.textContent=lines[idx+1]||'';}
function frame(){if(!running)return;const t=now(),h=els.stage.clientHeight,judgeY=h-49;updateLyrics(t);phaseUpdate(t);chart.forEach(n=>{
 if(n.holdState==='holding'&&t>n.t+n.duration+windows.good){n.holdState='failed';activeHolds.delete(n.lane);miss('HOLD MISS')}
 if(n.hit||n.miss||n.skip)return;const dt=n.t-t;if(dt < -windows.good){n.miss=true;if(n.holdState)n.holdState='failed';miss(n.type==='response'?'RESPONSE MISS':'MISS');if(n.el)n.el.remove();return}if(dt>travel||dt<-windows.good)return;
 if(!n.el){n.el=document.createElement('div');n.el.className=`note ${n.type}${n.duration?' hold-note':''}`;els.lanes.children[n.lane].appendChild(n.el)}
 const y=judgeY-(dt/travel)*(judgeY-20),height=n.duration?Math.max(14,n.duration/travel*(judgeY-20)):14;n.el.style.height=`${height}px`;n.el.style.top=`${y-height+14}px`;
 });if(t>chart.at(-1).t+900){finish();return}raf=requestAnimationFrame(frame)}
function press(key){if(!running)return;const lane=MODES[mode].keys.indexOf(key);if(lane<0)return;pressedKeys.add(key);els.lanes.children[lane].classList.add('pressed');els.stage.querySelector('.receptors')?.children[lane]?.classList.add('active');const t=now();
 if(mode==='hard'&&phase==='improv'){if(memory.length<8){memory.push({lane,dt:t-improvStart});els.memory.textContent=`기억한 프레이즈 ${memory.length}/8`;if(memory.length===8)flash('MEMORY SEALED','perfect')}return}
 let best=null,err=Infinity;chart.forEach(n=>{if(n.lane!==lane||n.hit||n.miss||n.skip)return;const e=Math.abs(n.t-t);if(e<err){err=e;best=n}});
 const adaptiveGood=windows.good+(assist*45);if(!best||err>adaptiveGood){combo=0;flash(phase==='response'?'RESPONSE':'MISS',phase==='response'?'great':'miss');updateHud();return}
 best.hit=true;hits++;pluckLane(lane,!!best.duration);award(err);if(best.duration){best.holdState='holding';activeHolds.set(lane,best);flash(best.charge?'CHARGE':best.releaseOnly?'RELEASE HOLD':'HOLD','great')}if(best.el){best.el.classList.add('hit');if(!best.duration)setTimeout(()=>best.el?.remove(),130)}
}
function release(key){const lane=MODES[mode].keys.indexOf(key);if(lane<0)return;pressedKeys.delete(key);els.lanes.children[lane]?.classList.remove('pressed');els.stage.querySelector('.receptors')?.children[lane]?.classList.remove('active');const note=activeHolds.get(lane);if(!note)return;activeHolds.delete(lane);stopLane(lane);if(note.holdState!=='holding')return;const err=Math.abs(now()-(note.t+note.duration));if(err<=windows.good){note.holdState='complete';award(err);if(note.releaseOnly)flash('RELEASE','perfect');else if(note.charge)flash('CHARGE RELEASE','perfect');if(note.el)note.el.classList.add('hold-complete')}else{note.holdState='failed';miss('HOLD MISS')}}
async function start(){reset();els.stage.focus();const drill=mode==='hard'&&new URLSearchParams(location.search).get('drill')==='1';els.status.textContent=drill?'EXPERT · 1분 패턴 테스트곡':`${MODES[mode].label} · ${mode==='hard'?'화음·홀드·즉흥 기억/응답 활성':'정석 연주'}`;for(const n of ['3','2','1']){els.countdown.textContent=n;await new Promise(r=>setTimeout(r,450))}els.countdown.textContent='';try{els.song.playbackRate=playbackSpeed();await els.song.play()}catch(e){els.status.textContent='오디오 재생을 시작하지 못했습니다. 다시 눌러 주세요.';return}startAt=performance.now()+900;running=true;document.body.classList.add('playing');raf=requestAnimationFrame(frame)}
function finish(){running=false;document.body.classList.remove('playing');cancelAnimationFrame(raf);els.song.pause();stopAllVoices();els.stage.classList.remove('improv');const acc=judged?Math.max(0,100-totalErr/judged/1.3):0;const rank=acc>=99?'S+':acc>=95?'S':acc>=90?'A':acc>=80?'B':acc>=70?'C':'D';const fullPerfect=counts.miss===0&&counts.good===0&&counts.great===0&&judged>0,fullCombo=counts.miss===0&&judged>0;els.resultRank.textContent=rank;els.resultScore.textContent=String(score).padStart(6,'0');els.resultAcc.textContent=`${acc.toFixed(2)}%`;els.resultPerfect.textContent=counts.perfect;els.resultGreat.textContent=counts.great;els.resultGood.textContent=counts.good;els.resultMiss.textContent=counts.miss;els.resultCombo.textContent=maxCombo;els.resultRunes.textContent=`${runes} / 4`;els.resultClear.textContent=fullPerfect?'ALL PERFECT':fullCombo?'FULL COMBO':acc>=85?'CLEAR':'FINISH';const comments=[];if(runes===4)comments.push('네 개의 룬이 모두 응답했습니다.');if(memory.length)comments.push(`즉흥 프레이즈 ${memory.length}음을 기억했습니다.`);comments.push(acc>=95?'루바토가 만족스럽게 화음을 되짚습니다.':acc>=85?'루바토가 다음 프레이즈를 기다립니다.':'루바토가 박자를 조금 더 넓게 받아 줍니다.');els.resultRubato.textContent=comments.join(' ');els.result.classList.add('show');els.result.setAttribute('aria-hidden','false');els.status.textContent=`완주 · ${acc.toFixed(2)}% · ${rank}`;}
document.querySelectorAll('.difficulty').forEach(b=>b.classList.toggle('active',b.dataset.mode===mode));document.querySelectorAll('.difficulty').forEach(b=>b.addEventListener('click',()=>{mode=b.dataset.mode;document.querySelectorAll('.difficulty').forEach(x=>x.classList.toggle('active',x===b));reset()}));
function applySong(id){songId=id;SONG=SONGS[id];BPM=SONG.bpm;BEAT=60000/BPM;LANE_FREQ=SONG.lanes;els.songTitle.textContent=`〈${SONG.title}〉`;els.instrumentLabel.textContent=`루바토의 ${SONG.instrumentKo} · ${SONG.instrument}`;els.song.src=SONG.audio;const u=new URL(location.href);u.searchParams.set('song',id);history.replaceState(null,'',u);reset();}
Object.entries(SONGS).forEach(([id,x])=>{const o=document.createElement('option');o.value=id;o.textContent=`${x.title} · ${x.instrument}`;o.selected=id===songId;els.songSelect.appendChild(o)});els.songSelect.addEventListener('change',()=>applySong(els.songSelect.value));applySong(songId);
els.start.addEventListener('click',start);els.resultAgain.addEventListener('click',start);document.addEventListener('keydown',e=>{const k=e.key.toLowerCase();if(MODES[mode].keys.includes(k)){e.preventDefault();if(!e.repeat)press(k)}});document.addEventListener('keyup',e=>release(e.key.toLowerCase()));
reset();window.rhythmDemo={getState:()=>({mode,phase,score,combo,hits,judged,runes,memory:memory.length,duration:chart.length?chart.at(-1).t+900:0,notes:chart.map(n=>({t:n.t,lane:n.lane,type:n.type,duration:n.duration,releaseOnly:n.releaseOnly,charge:n.charge,hit:n.hit,holdState:n.holdState}))}),press,release,Patterns};
})();
