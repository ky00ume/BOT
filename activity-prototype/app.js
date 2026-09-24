const room=document.querySelector('#room'),chu=document.querySelector('#chu'),fx=document.querySelector('#fx'),log=document.querySelector('#log');
const COLS=18,ROWS=12,blocked=new Set();let x=9,y=8,facing=0,busy=false;
const objects=[
{x:3,y:3,w:2,h:2,name:'책장',icon:'📚',text:'오래된 책들이 빽빽하게 꽂혀 있습니다. 츄라이더가 숨기 좋아 보이는 틈도 있습니다.'},
{x:14,y:4,w:1,h:1,name:'마제스티의 리라',icon:'🎻',text:'마제스티가 연주하는 리라입니다. 가까이 가면 익숙한 선율이 떠오릅니다.'},
{x:15,y:9,w:1,h:1,name:'전시관 입구',icon:'🏛️',text:'비전의 탑 전시관으로 이어지는 입구입니다.'},
{x:3,y:9,w:1,h:1,name:'촛불',icon:'🕯️',text:'작은 불빛이 3층 큰방을 은은하게 밝히고 있습니다.'}
];
const map=document.createElement('div');map.className='tilemap';room.prepend(map);
const tile=(kind,c,r)=>{const t=document.createElement('i');t.className=`tile ${kind}`;t.dataset.col=c;t.dataset.row=r;map.appendChild(t)};
for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){
 let kind='floor';
 if(r===0)kind='wallTop'; else if(r===1||r===2)kind='wallFace'; else if(r===ROWS-1||c===0||c===COLS-1)kind='wallEdge';
 else if(c>=6&&c<=11&&r>=6&&r<=9)kind=((c+r)%2?'arcaneA':'arcaneB');
 tile(kind,c,r);
 if(r<=2||r===ROWS-1||c===0||c===COLS-1)blocked.add(`${c},${r}`);
}
objects.forEach(o=>{for(let yy=o.y;yy<o.y+o.h;yy++)for(let xx=o.x;xx<o.x+o.w;xx++)blocked.add(`${xx},${yy}`)});
function pctX(v){return v*100/COLS} function pctY(v){return v*100/ROWS}
function draw(){chu.style.left=pctX(x)+'%';chu.style.top=pctY(y)+'%';chu.style.setProperty('--facing',facing+'deg');chu.dataset.x=x;chu.dataset.y=y;chu.dataset.facing=facing}
function stepForFacing(){if(facing===0)return[0,-1];if(facing===90)return[1,0];if(facing===180)return[0,1];return[-1,0]}
function move(dx,dy,deg){if(busy)return;facing=deg;const nx=x+dx,ny=y+dy;if(blocked.has(`${nx},${ny}`)){draw();log.textContent='🧱 이쪽은 막혀 있습니다.';return}x=nx;y=ny;draw();log.textContent='🐾 타닥타닥.'}
function flash(s,t=650){fx.textContent=s;fx.style.left=(pctX(x)+2)+'%';fx.style.top=(pctY(y)-4)+'%';setTimeout(()=>fx.textContent='',t)}
function objectAt(tx,ty){return objects.find(o=>tx>=o.x&&tx<o.x+o.w&&ty>=o.y&&ty<o.y+o.h)}
function inspect(){if(busy)return;const[dx,dy]=stepForFacing(),tx=x+dx,ty=y+dy,found=objectAt(tx,ty);if(found){flash('🔎',850);log.textContent=`${found.icon} ${found.name} · ${found.text}`}else if(blocked.has(`${tx},${ty}`)){flash('🔎',650);log.textContent='🧱 비전의 탑을 두른 오래된 석벽입니다.'}else{flash('?',600);log.textContent='🔎 이쪽에는 특별히 조사할 것이 없습니다.'}}
function act(a){if(busy)return;busy=true;chu.className='';void chu.offsetWidth;let t=650;if(a==='hop'){chu.classList.add('hop');flash('✨');log.textContent='🕷️ 폴짝!'}if(a==='shake'){chu.classList.add('shake');flash('〰️');log.textContent='🕷️ 부르르르.'}if(a==='surprise'){chu.classList.add('surprise');flash('❗');log.textContent='🕷️ 화들짝!'}if(a==='happy'){chu.classList.add('happy');flash('💕');log.textContent='🕷️💕 신났슴미댜.'}if(a==='hide'){chu.classList.add('hiddenChu');flash('…',900);log.textContent='🕷️ 책장 뒤에 숨은 척합니다.';t=900}if(a==='dash'){chu.classList.add('dash');flash('💨');const[dx,dy]=stepForFacing();for(let i=0;i<2;i++){const nx=x+dx,ny=y+dy;if(blocked.has(`${nx},${ny}`))break;x=nx;y=ny}draw();log.textContent='🕷️💨 바라보는 쪽으로 후다닥!'}setTimeout(()=>{chu.className='';busy=false},t)}
function key(e){const k=e.key.toLowerCase();if(['arrowup','arrowdown','arrowleft','arrowright','w','a','s','d',' ','b','h','e'].includes(k))e.preventDefault();if(k==='arrowup'||k==='w')move(0,-1,0);else if(k==='arrowdown'||k==='s')move(0,1,180);else if(k==='arrowleft'||k==='a')move(-1,0,270);else if(k==='arrowright'||k==='d')move(1,0,90);else if(k==='e')inspect();else if(k===' ')act('hop');else if(k==='b')act('shake');else if(k==='h')act('happy')}
document.addEventListener('keydown',key);document.querySelectorAll('[data-move]').forEach(b=>b.addEventListener('click',()=>({up:()=>move(0,-1,0),down:()=>move(0,1,180),left:()=>move(-1,0,270),right:()=>move(1,0,90)})[b.dataset.move]()));document.querySelectorAll('[data-act]').forEach(b=>b.addEventListener('click',()=>act(b.dataset.act)));document.querySelector('[data-inspect]').addEventListener('click',inspect);draw();window.chuDemo={getState:()=>({x,y,facing,busy}),move,act,inspect};