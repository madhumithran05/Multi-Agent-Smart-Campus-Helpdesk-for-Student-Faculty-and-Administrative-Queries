/* ================= AGENT META (mirrors agents/coordinator.py) ================= */
const AGENTS = {
  coordinator:{name:'Coordinator Agent', hex:'#E8A33D', icon:'◈'},
  student:{name:'Student Agent', hex:'#4FD1C5', icon:'🎓'},
  faculty:{name:'Faculty Agent', hex:'#9B8CFF', icon:'🧑‍🏫'},
  admin:{name:'Administrative Agent', hex:'#F2795C', icon:'🏛'},
  navigation:{name:'Navigation Agent', hex:'#5CA8F2', icon:'⌖'},
  event:{name:'Event Agent', hex:'#A8D65C', icon:'✦'},
};

/* ================= NAV SWITCHING ================= */
const titles = {
  chat:['Ask Quadrant','One question, five specialists, one answer.'],
  network:['Agent Network','Live view of every agent-to-agent handoff.'],
  dashboard:['Admin Dashboard','Real-time analytics across the whole helpdesk.'],
  navigator:['Campus Navigator','Find your way, guided by the Navigation Agent.'],
  events:['Events & Drives','Curated by the Event Agent, based on your interests.'],
  lostfound:['Lost & Found','Report and track items across campus.'],
};
document.querySelectorAll('.navlist button').forEach(btn=>{
  btn.addEventListener('click',()=>{
    document.querySelectorAll('.navlist button').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    const v = btn.dataset.view;
    document.querySelectorAll('.view').forEach(s=>s.classList.remove('active'));
    document.getElementById('view-'+v).classList.add('active');
    document.getElementById('topbarTitle').textContent = titles[v][0];
    document.getElementById('topbarSub').textContent = titles[v][1];
    if(v==='dashboard') loadDashboard();
    if(v==='events') loadEvents();
    if(v==='lostfound') loadLostFound();
    if(v==='navigator') loadBuildings();
  });
});

function toggleNotif(){document.getElementById('notifPanel').classList.toggle('open');}
document.addEventListener('click',e=>{
  const p=document.getElementById('notifPanel');
  if(!p.contains(e.target) && !e.target.closest('.icon-btn')) p.classList.remove('open');
});

/* ================= MODAL ================= */
function openModal(){document.getElementById('modalBg').classList.add('open');}
function closeModal(){document.getElementById('modalBg').classList.remove('open');}
function confirmSOS(){
  closeModal();
  switchToChat();
  appendMsg('coordinator', 'Campus Security alerted — nearest patrol notified of your location. Stay where you are if safe to do so.', false);
}
function switchToChat(){ document.querySelector('.navlist button[data-view="chat"]').click(); }

/* ================= SIDE PANELS (faculty / queue) ================= */
async function renderFaculty(){
  const res = await fetch('/api/faculty'); const faculty = await res.json();
  document.getElementById('facultyStatusList').innerHTML = faculty.map(f=>`
    <div class="agent-status-row">
      <span class="status-dot ${f.status}"></span>
      <span style="flex:1;">${f.name}<br><span style="color:var(--muted-2);font-size:11px;">${f.designation||""} · ${f.dept}</span></span>
      <span style="font-size:11px;color:var(--muted);text-transform:capitalize;">${f.status==='on'?'Available':f.status==='busy'?'In class':f.status==='na'?'Not tracked':'Offline'}</span>
    </div>`).join('');
}
async function renderQueue(){
  const res = await fetch('/api/queue'); const queue = await res.json();
  document.getElementById('queueList').innerHTML = queue.map(q=>`
    <div class="queue-item"><span>${q.label}</span><b>${q.n} waiting</b></div>`).join('');
}
renderFaculty(); renderQueue();
setInterval(renderQueue, 4000);

/* ================= CHAT ENGINE ================= */
const chatScroll = document.getElementById('chatScroll');

function avatarFor(who){
  if(who==='user') return `<div class="msg-avatar" style="background:var(--bg-raised);color:var(--text);">You</div>`;
  const a = AGENTS[who];
  return `<div class="msg-avatar" style="background:${a.hex}22;color:${a.hex};border:1px solid ${a.hex}55;">${a.icon}</div>`;
}
function appendMsg(who, text, isUser, collab){
  const wrap = document.createElement('div');
  wrap.className = 'msg ' + (isUser?'user':'') + (collab?' collab':'');
  const tagHtml = isUser? '' : `<div class="msg-agent-tag" style="color:${AGENTS[who].hex}">${AGENTS[who].icon} ${AGENTS[who].name}</div>`;
  wrap.innerHTML = `${avatarFor(isUser?'user':who)}<div class="msg-body">${tagHtml}${text}</div>`;
  chatScroll.appendChild(wrap);
  chatScroll.scrollTop = chatScroll.scrollHeight;
}
function appendTyping(who){
  const wrap = document.createElement('div');
  wrap.className = 'msg';
  wrap.innerHTML = `${avatarFor(who)}<div class="msg-body"><div class="msg-agent-tag" style="color:${AGENTS[who].hex}">${AGENTS[who].icon} ${AGENTS[who].name}</div><div class="typing"><span></span><span></span><span></span></div></div>`;
  chatScroll.appendChild(wrap);
  chatScroll.scrollTop = chatScroll.scrollHeight;
  return wrap;
}

appendMsg('coordinator', "Hi! I'm the Coordinator Agent. Ask me anything — attendance, faculty availability, fees, directions, or events — and I'll bring in the right specialist.", false);

function escapeHtml(s){ const d=document.createElement('div'); d.textContent=s; return d.innerHTML; }

function sendMessage(){
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if(!text) return;
  appendMsg('user', escapeHtml(text), true);
  input.value = '';
  runQuery(text);
}
function askSuggested(text){
  appendMsg('user', escapeHtml(text), true);
  runQuery(text);
}

async function runQuery(text){
  const typingCo = appendTyping('coordinator');
  let result;
  try{
    const res = await fetch('/api/query', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({text})
    });
    result = await res.json();
  }catch(err){
    typingCo.remove();
    appendMsg('coordinator', "I couldn't reach the backend just now — please check the Flask server is running.", false);
    return;
  }

  typingCo.remove();
  const agentsHit = result.agents;
  const names = agentsHit.map(a=>AGENTS[a].name).join(' + ');
  appendMsg('coordinator', agentsHit.length>1
    ? `This needs input from <b>${names}</b>. Routing now and combining their answers…`
    : `Routing this to the <b>${names}</b>…`, false);

  logNetwork(`<b>Coordinator</b> → routing to <b>${names}</b>`);
  pulseNetwork(agentsHit);

  agentsHit.forEach((agentKey, i)=>{
    setTimeout(()=>{
      const typ = appendTyping(agentKey);
      setTimeout(()=>{
        typ.remove();
        appendMsg(agentKey, result.responses[agentKey], false, agentsHit.length>1);
        logNetwork(`<b>${AGENTS[agentKey].name}</b> → response sent to Coordinator`);
      }, 650 + Math.random()*450);
    }, i*650);
  });

  if(agentsHit.length>1){
    const totalDelay = agentsHit.length*650 + 900;
    setTimeout(()=>{
      appendMsg('coordinator', `Combined answer ready above from ${agentsHit.length} agents — let me know if you'd like more detail from any of them.`, false);
      logNetwork(`<b>Coordinator</b> → merged multi-agent response delivered`);
    }, totalDelay);
  }
}

/* ================= VOICE ================= */
let recognizing = false, recognition;
function toggleMic(){
  const btn = document.getElementById('micBtn');
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if(!SpeechRec){
    appendMsg('coordinator', "Voice input isn't supported in this browser, but text works everywhere I do!", false);
    return;
  }
  if(recognizing){ recognition.stop(); return; }
  recognition = new SpeechRec();
  recognition.lang = 'en-IN';
  recognition.onstart = ()=>{ recognizing=true; btn.classList.add('listening'); };
  recognition.onend = ()=>{ recognizing=false; btn.classList.remove('listening'); };
  recognition.onresult = (e)=>{
    const t = e.results[0][0].transcript;
    document.getElementById('chatInput').value = t;
    sendMessage();
  };
  recognition.start();
}

/* ================= AGENT NETWORK SVG ================= */
const netSvg = document.getElementById('networkSvg');
const netPositions = {
  coordinator:{x:320,y:250},
  student:{x:150,y:100}, faculty:{x:500,y:100},
  admin:{x:560,y:330}, navigation:{x:320,y:460}, event:{x:80,y:330},
};
function buildNetwork(){
  let svg = '';
  Object.keys(netPositions).forEach(k=>{
    if(k==='coordinator') return;
    const p1 = netPositions.coordinator, p2 = netPositions[k];
    svg += `<line id="edge-${k}" x1="${p1.x}" y1="${p1.y}" x2="${p2.x}" y2="${p2.y}" stroke="rgba(255,255,255,0.12)" stroke-width="1.5"/>`;
  });
  Object.keys(netPositions).forEach(k=>{
    const p = netPositions[k]; const a = AGENTS[k];
    const r = k==='coordinator'?38:30;
    svg += `<g id="node-${k}">
      <circle cx="${p.x}" cy="${p.y}" r="${r}" fill="${a.hex}22" stroke="${a.hex}" stroke-width="2"/>
      <text x="${p.x}" y="${p.y+5}" text-anchor="middle" font-size="20">${a.icon}</text>
      <text x="${p.x}" y="${p.y+r+16}" text-anchor="middle" class="node-label">${a.name.replace(' Agent','')}</text>
    </g>`;
  });
  netSvg.innerHTML = svg;
}
buildNetwork();

function pulseNetwork(targets){
  targets.forEach((t,i)=>{
    setTimeout(()=>{
      const edge = document.getElementById('edge-'+t);
      if(!edge) return;
      edge.setAttribute('stroke', AGENTS[t].hex);
      edge.setAttribute('stroke-width','3');
      const p1 = netPositions.coordinator, p2 = netPositions[t];
      const dot = document.createElementNS('http://www.w3.org/2000/svg','circle');
      dot.setAttribute('r','5'); dot.setAttribute('fill', AGENTS[t].hex);
      dot.setAttribute('cx',p1.x); dot.setAttribute('cy',p1.y);
      netSvg.appendChild(dot);
      let t0=null;
      function anim(ts){
        if(!t0) t0=ts;
        const prog = Math.min((ts-t0)/900,1);
        dot.setAttribute('cx', p1.x + (p2.x-p1.x)*prog);
        dot.setAttribute('cy', p1.y + (p2.y-p1.y)*prog);
        if(prog<1) requestAnimationFrame(anim);
        else { dot.remove(); setTimeout(()=>{edge.setAttribute('stroke','rgba(255,255,255,0.12)');edge.setAttribute('stroke-width','1.5');},400); }
      }
      requestAnimationFrame(anim);
    }, i*250);
  });
}
function logNetwork(html){
  const feed = document.getElementById('logFeed');
  const line = document.createElement('div');
  line.className = 'log-line new';
  const time = new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'});
  line.innerHTML = `<span style="color:var(--muted-2)">${time}</span> — ${html}`;
  feed.prepend(line);
  if(feed.children.length>40) feed.lastChild.remove();
}
logNetwork('System ready — all 5 agents online.');

/* ================= DASHBOARD ================= */
Chart.defaults.color = '#8B93A7';
Chart.defaults.font.family = "'Inter',sans-serif";
Chart.defaults.font.size = 11;
let chartAgents, chartComplaints, chartResponse;

async function loadDashboard(){
  const res = await fetch('/api/dashboard'); const d = await res.json();

  document.getElementById('statGrid').innerHTML = `
    <div class="card stat-card">
      <div class="stat-top"><div class="stat-icon" style="background:var(--amber-dim);color:var(--amber);">Σ</div><span class="stat-delta up">▲ 12%</span></div>
      <div class="stat-val">${d.total_queries.toLocaleString()}</div><div class="stat-label">Total queries this week</div>
    </div>
    <div class="card stat-card">
      <div class="stat-top"><div class="stat-icon" style="background:var(--coral-dim);color:var(--coral);">◎</div><span class="stat-delta down">▼ 6%</span></div>
      <div class="stat-val">${d.open_complaints}</div><div class="stat-label">Open complaint tickets</div>
    </div>
    <div class="card stat-card">
      <div class="stat-top"><div class="stat-icon" style="background:var(--teal-dim);color:var(--teal);">⏱</div><span class="stat-delta up">▲ 0.4s</span></div>
      <div class="stat-val">${d.avg_response_time}s</div><div class="stat-label">Avg agent response time</div>
    </div>
    <div class="card stat-card">
      <div class="stat-top"><div class="stat-icon" style="background:var(--lime-dim);color:var(--lime);">✓</div><span class="stat-delta up">▲ 2%</span></div>
      <div class="stat-val">${d.resolution_rate}%</div><div class="stat-label">Query resolution rate</div>
    </div>`;

  const perfRows = d.agent_performance.map(a=>`
    <tr><td>${a.agent}</td><td>${a.queries}</td>
      <td><span class="bar-track"><span class="bar-fill" style="width:${a.accuracy}%;background:${a.color};"></span></span>${a.accuracy}%</td>
      <td>${a.avg_time}</td></tr>`).join('');
  document.getElementById('perfTable').innerHTML = '<tr><th>Agent</th><th>Queries</th><th>Accuracy</th><th>Avg time</th></tr>' + perfRows;

  const agentLabels = ['Student','Faculty','Admin','Navigation','Event'];
  const agentKeys = ['student','faculty','admin','navigation','event'];
  const agentData = agentKeys.map(k=>d.agent_counts[k]||0);

  if(chartAgents) chartAgents.destroy();
  chartAgents = new Chart(document.getElementById('chartAgentQueries'), {
    type:'bar',
    data:{ labels:agentLabels, datasets:[{ data:agentData,
      backgroundColor:['#4FD1C5','#9B8CFF','#F2795C','#5CA8F2','#A8D65C'], borderRadius:8, maxBarThickness:38 }]},
    options:{ plugins:{legend:{display:false}}, scales:{ x:{grid:{display:false}}, y:{grid:{color:'rgba(255,255,255,0.06)'}} } }
  });

  if(chartComplaints) chartComplaints.destroy();
  chartComplaints = new Chart(document.getElementById('chartComplaints'), {
    type:'doughnut',
    data:{ labels:['Resolved','In Progress','Open'],
      datasets:[{ data:[d.complaint_status.resolved, d.complaint_status.in_progress, d.complaint_status.open],
        backgroundColor:['#6FCF97','#E8A33D','#EB5757'], borderWidth:0 }]},
    options:{ plugins:{legend:{position:'bottom',labels:{boxWidth:10,padding:14}}}, cutout:'68%' }
  });

  if(chartResponse) chartResponse.destroy();
  chartResponse = new Chart(document.getElementById('chartResponse'), {
    type:'line',
    data:{ labels:d.response_trend.labels,
      datasets:[{ data:d.response_trend.values, borderColor:'#E8A33D', backgroundColor:'rgba(232,163,61,0.12)', tension:0.4, fill:true, pointRadius:3 }]},
    options:{ plugins:{legend:{display:false}}, scales:{ x:{grid:{display:false}}, y:{grid:{color:'rgba(255,255,255,0.06)'}} } }
  });
}

/* ================= NAVIGATOR MAP (real BIT campus, Leaflet) ================= */
let BUILDINGS = [];
let CAMPUS = null;
let leafMap = null, routeLine = null, markers = {};

async function loadBuildings(){
  if(BUILDINGS.length){ setTimeout(()=>leafMap && leafMap.invalidateSize(), 50); return; }
  const [bRes, cRes] = await Promise.all([fetch('/api/buildings'), fetch('/api/campus')]);
  BUILDINGS = await bRes.json(); CAMPUS = await cRes.json();
  buildMap();
  document.getElementById('quickDest').innerHTML = BUILDINGS.filter(b=>b.id!=='gate').map(b=>
    `<button class="suggest-chip" style="text-align:left;" onclick="selectBuildingById('${b.id}')">${b.name}</button>`).join('');
}
function buildMap(){
  leafMap = L.map('campusMap', {zoomControl:true}).setView([CAMPUS.lat, CAMPUS.lng], CAMPUS.zoom);
  const street = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:20, maxNativeZoom:19, attribution:'&copy; OpenStreetMap contributors'});
  const imagery = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {maxZoom:20, maxNativeZoom:18, attribution:'Imagery &copy; Esri, Maxar, Earthstar Geographics'});
  const labels = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {maxZoom:20, maxNativeZoom:18, attribution:'Labels &copy; Esri'});
  const roads = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}', {maxZoom:20, maxNativeZoom:18});
  const hybrid = L.layerGroup([imagery, roads, labels]);
  const satellite = L.layerGroup([L.tileLayer(imagery._url, {maxZoom:20, maxNativeZoom:18})]);
  hybrid.addTo(leafMap);
  L.control.layers({'🛰️ Satellite + roads':hybrid, '🛰️ Satellite only':satellite, '🗺️ Street map':street}, null, {collapsed:false}).addTo(leafMap);
  L.control.scale({imperial:false}).addTo(leafMap);
  BUILDINGS.forEach(b=>{
    const icon = L.divIcon({className:'', html:`<div class="bld-pin" id="pin-${b.id}" style="background:${b.color}"></div>`, iconSize:[18,18], iconAnchor:[9,9]});
    const m = L.marker([b.lat,b.lng], {icon}).addTo(leafMap);
    m.bindTooltip(b.name, {permanent:true, direction:'top', offset:[0,-8], className:'bld-label'});
    m.on('click', ()=>selectBuildingById(b.id));
    markers[b.id] = m;
  });
  const bounds = L.latLngBounds(BUILDINGS.map(b=>[b.lat,b.lng]));
  leafMap.fitBounds(bounds.pad(0.25));
  leafMap.on('click', e=>{
    L.popup().setLatLng(e.latlng).setContent(`<b>Coordinates</b><br>${e.latlng.lat.toFixed(5)}, ${e.latlng.lng.toFixed(5)}`).openOn(leafMap);
  });
  setTimeout(()=>leafMap.invalidateSize(), 100);
}
function selectBuildingById(id){
  const b = BUILDINGS.find(x=>x.id===id);
  if(b) showRoute(b);
}
function showRoute(b){
  document.querySelectorAll('.bld-pin').forEach(el=>el.classList.remove('active'));
  const pin = document.getElementById('pin-'+b.id);
  if(pin) pin.classList.add('active');
  drawRoute(b);
  const gmaps = `https://www.google.com/maps/dir/?api=1&destination=${b.lat},${b.lng}&travelmode=walking`;
  const gate = BUILDINGS.find(x=>x.id==='gate');
  const km = leafMap.distance([gate.lat,gate.lng],[b.lat,b.lng]);
  const mins = Math.max(1, Math.round(km/80)); // ~80 m/min walking
  document.getElementById('routeResult').classList.add('show');
  document.getElementById('routeResult').innerHTML = `<b style="color:var(--amber)">Route locked:</b> Main Gate → ${b.name}<br><span style="color:var(--muted)">≈ ${Math.round(km)} m · ${mins} min walk · shown on the map in amber.</span><br><a href="${gmaps}" target="_blank" rel="noopener">Open in Google Maps ↗</a>`;
}
function drawRoute(b){
  if(routeLine) routeLine.remove();
  const gate = BUILDINGS.find(x=>x.id==='gate');
  routeLine = L.polyline([[gate.lat,gate.lng],[b.lat,b.lng]], {color:'#E8A33D', weight:4, dashArray:'8 8'}).addTo(leafMap);
  leafMap.fitBounds(routeLine.getBounds().pad(0.4));
}
async function searchRoute(){
  const q = document.getElementById('navSearch').value.trim();
  if(!q) return;
  const res = await fetch('/api/route', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({destination:q})});
  const b = await res.json();
  if(b && b.id) showRoute(b);
}

/* ================= EVENTS ================= */
const interests = ['All','Hackathon','Workshop','Placement','Seminar'];
let activeInterest = 'All';
let EVENTS = [];
async function loadEvents(){
  if(!EVENTS.length){ const res = await fetch('/api/events'); EVENTS = await res.json(); }
  renderChips(); renderEvents();
}
function renderChips(){
  document.getElementById('interestChips').innerHTML = interests.map(i=>
    `<button class="chip ${i===activeInterest?'on':''}" onclick="setInterest('${i}')">${i}</button>`).join('');
}
function setInterest(i){ activeInterest = i; renderChips(); renderEvents(); }
function renderEvents(){
  const list = activeInterest==='All' ? EVENTS : EVENTS.filter(e=>e.tag===activeInterest);
  document.getElementById('eventGrid').innerHTML = list.map(e=>{
    const c = e.tag==='Hackathon'?'lime':e.tag==='Workshop'?'teal':e.tag==='Placement'?'coral':'violet';
    return `<div class="card event-card">
      <div class="event-top">
        <div class="event-date">${e.date}</div>
        <div class="event-title">${e.title}</div>
        <div class="event-desc">${e.desc}</div>
      </div>
      <div class="event-foot">
        <span>${e.loc}${e.link ? ` · <a href="${e.link}" target="_blank" rel="noopener" style="color:var(--teal);text-decoration:none;">Details ↗</a>` : ''}</span>
        <span class="tag" style="background:var(--${c}-dim);color:var(--${c});">${e.tag}</span>
      </div>
    </div>`;
  }).join('');
}

/* ================= LOST & FOUND ================= */
async function loadLostFound(){
  const res = await fetch('/api/lostfound'); const items = await res.json();
  renderLF(items);
}
function renderLF(items){
  document.getElementById('lfList').innerHTML = items.map((it,idx)=>`
    <div class="card lf-item">
      <div class="lf-item-left">
        <div class="lf-icon" style="background:${it.type==='Lost'?'var(--coral-dim)':'var(--teal-dim)'};color:${it.type==='Lost'?'var(--coral)':'var(--teal)'};">${it.type==='Lost'?'?':'◎'}</div>
        <div>
          <div class="lf-name">${it.name}</div>
          <div class="lf-meta">${it.type} · ${it.loc}${it.notes? ' · '+it.notes:''}</div>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:10px;">
        <span class="status-pill ${it.status}">${it.status==='open'?'Open':'Resolved'}</span>
        <button class="icon-btn" style="width:30px;height:30px;font-size:12px;" onclick="toggleLF(${idx})">✓</button>
      </div>
    </div>`).join('');
}
async function toggleLF(i){
  const res = await fetch(`/api/lostfound/${i}/toggle`, {method:'POST'});
  if(res.ok) loadLostFound();
}
async function submitLostFound(){
  const name = document.getElementById('lfName').value.trim();
  if(!name) return;
  const payload = {
    name, type:document.getElementById('lfType').value,
    loc:document.getElementById('lfLoc').value, notes:document.getElementById('lfNotes').value
  };
  const res = await fetch('/api/lostfound', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
  const data = await res.json();
  document.getElementById('lfName').value=''; document.getElementById('lfLoc').value=''; document.getElementById('lfNotes').value='';
  loadLostFound();
  switchToChat();
  setTimeout(()=>appendMsg('admin', `Ticket <b>#${data.ticket.id}</b> created for "${escapeHtml(name)}" and posted to Lost &amp; Found.`, false), 300);
}

/* ================= INITIAL LOAD =================
   Dashboard/Events/Lost&Found/Navigator are lazy-loaded the first time
   their tab is opened (see the navlist click handler above) so Chart.js
   never has to measure a hidden, zero-width canvas. */
