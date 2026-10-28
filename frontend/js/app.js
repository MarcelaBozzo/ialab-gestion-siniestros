/* ============ FECHAS Y UTILIDADES ============ */
const TODAY=new Date(2026,9,13); // fecha fija del prototipo
const pad=n=>String(n).padStart(2,'0');
const fmtD=d=>`${pad(d.getDate())}/${pad(d.getMonth()+1)}/${d.getFullYear()}`;
const parseD=s=>{const[d,m,y]=s.split('/').map(Number);return new Date(y,m-1,d)};
const addDays=(d,n)=>{const r=new Date(d);r.setDate(r.getDate()+n);return r};
const addBizDays=(d,n)=>{const r=new Date(d);while(n>0){r.setDate(r.getDate()+1);const w=r.getDay();if(w!==0&&w!==6)n--}return r};
const diffDays=(a,b)=>Math.round((b-a)/864e5);
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const norm=s=>s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
const clp=n=>new Intl.NumberFormat('es-CL',{style:'currency',currency:'CLP',maximumFractionDigits:0}).format(n);
const clock=()=>new Date().toLocaleTimeString('es-CL',{hour:'2-digit',minute:'2-digit'});
const now=()=>'Hoy '+clock();
const normRut=v=>String(v||'').toUpperCase().replace(/[^0-9K]/g,'');
function mdConfirm({title,text,ok='Confirmar',icon='help'}){return new Promise(res=>{
  const d=$('dlg'),s=$('dlgScrim'),prev=document.activeElement;$('dlgTitle').textContent=title;$('dlgText').textContent=text;$('dlgOk').textContent=ok;$('dlgIcon').textContent=icon;
  ['main','.topbar'].forEach(q=>document.querySelector(q).setAttribute('inert',''));d.hidden=false;s.hidden=false;$('dlgCancel').focus();
  const close=v=>{d.hidden=true;s.hidden=true;['main','.topbar'].forEach(q=>document.querySelector(q).removeAttribute('inert'));d.onkeydown=null;prev?.focus?.();res(v)};
  $('dlgOk').onclick=()=>close(true);$('dlgCancel').onclick=()=>close(false);s.onclick=()=>close(false);
  d.onkeydown=e=>{if(e.key==='Escape'){e.stopPropagation();close(false)}if(e.key==='Tab'){const a=$('dlgCancel'),b=$('dlgOk');if(e.shiftKey&&document.activeElement===a){e.preventDefault();b.focus()}else if(!e.shiftKey&&document.activeElement===b){e.preventDefault();a.focus()}}}})}
function announce(t){$('announce').textContent='';setTimeout(()=>$('announce').textContent=t,50)}
function toast(t){const el=$('toast');el.textContent=t;el.classList.add('show');clearTimeout(toast.t);toast.t=setTimeout(()=>el.classList.remove('show'),2400);announce(t)}
function log(c,actor,title,detail){c.history.unshift({actor,title,detail,time:now()})}
const ICON={
 warn:'<span class="mi" aria-hidden="true">warning</span>',
 info:'<span class="mi" aria-hidden="true">info</span>',
 ok:'<span class="mi" aria-hidden="true">check_circle</span>',
 wait:'<span class="mi" aria-hidden="true">schedule</span>',
 lock:'<span class="mi" aria-hidden="true">lock</span>',
 doc:'<span class="mi" aria-hidden="true">description</span>',
 img:'<span class="mi" aria-hidden="true">image</span>',
 spark:'<span class="mi" aria-hidden="true">auto_awesome</span>'
};

/* ============ DATOS SIMULADOS (ficticios) ============ */
const CLAUSE={code:'STD-COV-01',name:'Daños por colisión',doc:'AUTO_STANDARD_2026',page:2};
const POLICIES={'POL-123456':{plate:'ABCD12'},'POL-518772':{},'POL-217455':{},'POL-220301':{},'POL-402910':{},'POL-624118':{}};
const CLAIMS=[
 {number:'CLM-000123',rut:'99.900.001-0',stage:'expediente',block:'conflict',eventDate:'05/09/2026',reported:'06/09/2026',location:'Av. Providencia, Santiago',policy:'POL-123456',vehicle:'Toyota Corolla 2022',plate:'ABCD12',altPlate:'ABODI2',
  summary:'Colisión ocurrida el 5 de septiembre de 2026 en Av. Providencia, Santiago, asociada a la póliza POL-123456 y a un Toyota Corolla 2022. La patente aparece con valores distintos en dos documentos.',
  calc:{loss:1650000,pct:10,min:150000},tpl:{result:'cover',via:'rapida',viaReason:'Documentación completa, monto bajo el umbral de vía rápida y sin señales de alerta.',alerts:[]},
  docs:[{name:'denuncia_sintetica_poc6.pdf',type:'Denuncia del siniestro',state:'ok',fields:[['Fecha del evento','05/09/2026'],['Lugar','Av. Providencia, Santiago'],['Patente','ABCD12'],['RUT del declarante','99.900.001-0'],['Correo declarado','alejandro.t@correo-declarado.cl']]},
        {name:'scan_poc6_valido.png',type:'Antecedente escaneado (imagen)',state:'review',fields:[['Patente','ABODI2']]},
        {name:'scan_poc6_valido.pdf',type:'Antecedente documental',state:'ok',fields:[['N° de póliza','POL-123456']]}],
  declared:{email:'alejandro.t@correo-declarado.cl',src:'denuncia_sintetica_poc6.pdf'},
  reply:{name:'padron_vehiculo_ABCD12.pdf',type:'Padrón del vehículo',fields:[['Patente','ABCD12'],['Vehículo','Toyota Corolla 2022']]}},
 {number:'CLM-000217',rut:'99.900.002-9',stage:'expediente',block:'missing',eventDate:null,reported:'01/10/2026',location:null,policy:null,vehicle:'Hyundai Accent 2020',plate:'GHTR55',
  summary:'El expediente informa una colisión del vehículo patente GHTR55. La fecha del evento y el número de póliza no aparecen en los documentos disponibles.',
  calc:{loss:980000,pct:10,min:150000},tpl:{result:'cover',via:'rapida',viaReason:'Monto bajo el umbral de vía rápida y relato consistente con el daño informado.',alerts:[]},
  docs:[{name:'declaracion_colision.pdf',type:'Declaración del siniestro',state:'ok',fields:[['Patente','GHTR55'],['Fecha del evento','No encontrada'],['N° de póliza','No encontrado']]}],
  reply:{name:'antecedentes_asegurado_217.pdf',type:'Constancia y certificado de cobertura',fields:[['Fecha del evento','28/09/2026'],['Lugar','Ñuñoa, Santiago'],['N° de póliza','POL-217455']],apply:{eventDate:'28/09/2026',location:'Ñuñoa, Santiago',policy:'POL-217455'}}},
 {number:'CLM-000301',rut:'99.900.003-7',stage:'calculo',eventDate:'18/09/2026',reported:'18/09/2026',location:'Santiago',policy:'POL-220301',vehicle:'Kia Rio 2021',plate:'JKLR44',
  summary:'El expediente contiene una pérdida estimada de $2.000.000 y los parámetros de la póliza necesarios para calcular el deducible y la reserva preliminar.',
  calc:{loss:2000000,pct:10,min:150000},tpl:{result:'cover',via:'rapida',viaReason:'Presupuesto de reparación consistente con el daño descrito en la denuncia.',alerts:[]},
  docs:[{name:'estimacion_reparacion.pdf',type:'Presupuesto de reparación',state:'ok',fields:[['Pérdida estimada','$2.000.000']]},{name:'denuncia_siniestro.pdf',type:'Denuncia del siniestro',state:'ok',fields:[['Fecha del evento','18/09/2026'],['Patente','JKLR44']]}]},
 {number:'CLM-000402',rut:'99.900.004-5',stage:'expediente',block:'evidence',eventDate:'22/09/2026',reported:'23/09/2026',location:'Santiago',policy:'POL-402910',vehicle:'Mazda 3 2023',plate:'PRTX91',
  summary:'Colisión con daño en parachoques trasero. El expediente tiene documentos válidos como evidencia; un documento adicional fue excluido por seguridad y no se utiliza.',
  calc:{loss:850000,pct:10,min:150000},tpl:{result:'cover',via:'rapida',viaReason:'Monto bajo y documentación completa.',alerts:[]},
  docs:[{name:'denuncia_cliente.pdf',type:'Denuncia del siniestro',state:'ok',fields:[['Fecha del evento','22/09/2026'],['Patente','PRTX91']]},{name:'licencia_conducir.jpg',type:'Licencia de conducir',state:'ok',fields:[['Tipo de documento','Licencia de conducir']]},{name:'presupuesto_402.pdf',type:'Presupuesto de reparación',state:'ok',fields:[['Pérdida estimada','$850.000']]},{name:'anexo_relato_402.pdf',type:'Antecedente adjunto',state:'blocked',fields:[]}]},
 {number:'CLM-000518',rut:'99.900.001-0',stage:'propuesta',eventDate:'27/09/2026',reported:'27/09/2026',location:'Las Condes, Santiago',policy:'POL-518772',vehicle:'Chevrolet Sail 2022',plate:'LVBN73',
  summary:'Según la evidencia disponible, el expediente tiene los datos obligatorios y no se detectaron inconsistencias en los campos comparados. El cálculo fue validado y el asistente preparó una propuesta asistida de cobertura para tu revisión.',
  calc:{loss:1200000,pct:10,min:150000},tpl:{result:'cover',via:'rapida',viaReason:'Parte policial y fotografías consistentes con el relato; monto bajo el umbral de vía rápida.',alerts:[]},
  docs:[{name:'denuncia_518.pdf',type:'Denuncia del siniestro',state:'ok',fields:[['Fecha del evento','27/09/2026']]},{name:'parte_policial_518.pdf',type:'Parte policial',state:'ok',fields:[['Lugar','Las Condes, Santiago']]},{name:'fotografia_dano_518.jpg',type:'Fotografía del daño',state:'ok',fields:[['Tipo de documento','Fotografía']]},{name:'presupuesto_518.pdf',type:'Presupuesto de reparación',state:'ok',fields:[['Pérdida estimada','$1.200.000']]}]},
 {number:'CLM-000624',rut:'99.900.006-1',stage:'propuesta',eventDate:'10/09/2026',reported:'30/09/2026',location:'Santiago',policy:'POL-624118',vehicle:'Nissan Versa 2019',plate:'HTPL62',
  summary:'Colisión informada 20 días después del evento. Según la información recuperada, el asistente sugiere investigación como vía de gestión en lugar de vía rápida.',
  calc:{loss:3400000,pct:10,min:150000},tpl:{result:'investigation',via:'investigacion',viaReason:'Se detectaron señales de alerta en los documentos que justifican no utilizar la vía rápida.',alerts:[{t:'La denuncia se realizó 20 días después de la fecha del evento.',src:'denuncia_624.pdf'},{t:'El informe de revisión menciona daños que no se describen en el relato del asegurado.',src:'informe_revision_624.pdf'}]},
  docs:[{name:'denuncia_624.pdf',type:'Denuncia del siniestro',state:'ok',fields:[['Fecha del evento','10/09/2026'],['Fecha de denuncia','30/09/2026'],['Correo declarado','declarante.624@ejemplo.cl']]},{name:'informe_revision_624.pdf',type:'Informe de revisión',state:'ok',fields:[['Observación','Daños en costado izquierdo no descritos en el relato']]}],
  declared:{email:'declarante.624@ejemplo.cl',src:'denuncia_624.pdf'}}
];
/* Sistema de clientes simulado (PoC 10 API REST · PoC 11 MCP). Solo lectura. Datos ficticios. */
const CUST_DB={
 '99.900.001-0':{id:'CUST-000123',email:'a.torres@ejemplo.cl',phone_number:'+56 9 5555 0123',address:'Av. Ejemplo 1234, Santiago'},
 '99.900.002-9':{id:'CUST-000217',email:'cliente.217@ejemplo.cl',phone_number:'+56 9 5555 0217',address:'Ñuñoa, Santiago'},
 '99.900.003-7':{id:'CUST-000301',email:'cliente.301@ejemplo.cl',phone_number:'+56 9 5555 0301',address:'Santiago Centro',failOnce:true},
 '99.900.004-5':{id:'CUST-000402',email:'cliente.402@ejemplo.cl',phone_number:'+56 9 5555 0402',address:'Providencia, Santiago'}
};
const FIELD={email:'Correo',phone_number:'Teléfono',address:'Dirección'};
const SRC_CUST='Sistema de clientes · MCP solo lectura · simulado';
const RESULT={cover:{label:'Cubierto',cls:'ok'},nocover:{label:'No cubierto',cls:'warn'},investigation:{label:'Derivar a investigación',cls:'warn'}};
const STAGES=[['expediente','Expediente'],['calculo','Cálculo'],['propuesta','Propuesta asistida de cobertura'],['comunicacion','Comunicación'],['cerrado','Resuelto']];

function computeCalc(c){const k=c.calc,ded=Math.min(k.loss,Math.max(k.loss*k.pct/100,k.min));c.calcResult={...k,deductible:ded,reserve:Math.max(k.loss-ded,0)}}
function makeProposal(c){c.proposal={...c.tpl,coverage:CLAUSE.name,clause:CLAUSE}}
CLAIMS.forEach(c=>{
  c.sessions=[{id:1,title:'Revisión inicial',chat:[]}];c.sessionId=1;c.sessionSeq=1;
  c.history=[{actor:'Sistema',title:'Denuncia recibida',detail:`Plazo configurado para demostración: informe de liquidación al ${fmtD(addDays(parseD(c.reported),45))}.`,time:c.reported},
             {actor:'Sistema',title:'Documentos procesados',detail:`${c.docs.length} documento(s) incorporado(s) al expediente.`,time:c.reported}];
  const idx=STAGES.findIndex(s=>s[0]===c.stage);
  if(c.stage==='calculo'){computeCalc(c);c.history.unshift({actor:'Sistema',title:'Cálculo determinístico ejecutado',detail:`Deducible ${clp(c.calcResult.deductible)} · Reserva ${clp(c.calcResult.reserve)}. Regla configurada para demostración. Pendiente de validación del analista.`,time:'Ayer'})}
  if(idx>=2){computeCalc(c);c.calcConfirmed=true;c.history.unshift({actor:'Sistema',title:'Cálculo determinístico ejecutado',detail:`Deducible ${clp(c.calcResult.deductible)} · Reserva ${clp(c.calcResult.reserve)}.`,time:'Ayer'});c.history.unshift({actor:'Analista',title:'Reserva validada por analista',detail:clp(c.calcResult.reserve),time:'Ayer'})}
  if(idx>=2){makeProposal(c);c.history.unshift({actor:'Asistente',title:'Propuesta asistida generada',detail:`Resultado sugerido: ${RESULT[c.proposal.result].label}${c.proposal.result==='investigation'?'':` · cita ${CLAUSE.code}`}. Pendiente de revisión del analista.`,time:'Ayer'})}
  if(idx>=3){c.decision={action:'accept',result:'cover',reason:''};c.history.unshift({actor:'Analista',title:'Propuesta aceptada por analista',detail:'Sin cambios. Resultado decidido: Cubierto',time:'Ayer'})}
  if(c.block==='conflict')c.history.unshift({actor:'Sistema',title:'Discrepancia detectada',detail:'La patente difiere entre denuncia_sintetica_poc6.pdf (ABCD12) y scan_poc6_valido.png (ABODI2).',time:c.reported});
  if(c.block==='missing')c.history.unshift({actor:'Sistema',title:'Datos obligatorios no encontrados',detail:'Faltan fecha del evento y número de póliza.',time:c.reported});
  c.docs.filter(d=>d.state==='blocked').forEach(d=>c.history.unshift({actor:'Sistema',title:'Documento excluido de la evidencia',detail:`${d.name}: se detectó contenido que intenta modificar el comportamiento del asistente. No se usó en el resumen, las respuestas ni los datos del expediente.`,time:c.reported}));
});

/* ============ ESTADO DERIVADO ============ */
const STATES={review:{label:'Requiere revisión',cls:'warn'},todo:{label:'Por gestionar',cls:'info'},waiting:{label:'Esperando antecedentes',cls:'neutral'},derived:{label:'Derivado a investigación',cls:'neutral'},closed:{label:'Resuelto',cls:'ok'}};
function stateOf(c){
  if(c.stage==='cerrado')return 'closed';if(c.stage==='investigacion')return 'derived';
  if(c.stage==='expediente')return c.block==='waiting'?'waiting':'review';
  if(c.stage==='propuesta'&&c.proposal?.result==='investigation')return 'review';
  return 'todo';
}
function nextOf(c){
  switch(c.stage){
    case 'expediente':return c.block==='conflict'?'Resolver discrepancia de patente':c.block==='missing'?'Revisar antecedentes faltantes':c.block==='extracted'?'Confirmar datos críticos extraídos':c.block==='evidence'?'Revisar evidencia disponible':'Esperando antecedentes (simulado)';
    case 'calculo':return c.calcResult?'Revisar cálculo de deducible y reserva':'Revisar cálculo determinístico';
    case 'propuesta':return c.proposal.result==='investigation'?'Revisar sugerencia de investigación':'Revisar propuesta asistida';
    case 'comunicacion':return 'Revisar borrador y simular envío';
    case 'investigacion':return 'Sin acciones pendientes';
    default:return 'Sin acciones pendientes';
  }
}
function slaOf(c){
  if(c.stage==='cerrado')return {text:`Impugnación hasta ${fmtD(c.appealUntil)}`,sub:'Plazo configurado para la demo: 10 días hábiles',warn:false};
  if(c.stage==='investigacion')return {text:'Derivado a investigación',sub:'Fin del alcance de la demostración',warn:false};
  const due=addDays(parseD(c.reported),45),left=diffDays(TODAY,due);
  return {text:left>=0?`Quedan ${left} días`:`Vencido hace ${-left} días`,sub:`Informe de liquidación: ${fmtD(due)}`,warn:left<=10};
}

/* ============ NOTIFICACIONES ============ */
let notifs=[
 {id:1,claim:'CLM-000123',actor:'Sistema',title:'Plazo de liquidación por vencer',detail:'Quedan 8 días para el plazo de liquidación configurado en la demo.',time:'Hoy 08:00',target:'task',read:false},
 {id:2,claim:'CLM-000123',actor:'Sistema',title:'Discrepancia detectada',detail:'La patente difiere entre dos documentos del expediente.',time:'Ayer',target:'task',read:false},
 {id:3,claim:'CLM-000217',actor:'Sistema',title:'Datos obligatorios no encontrados',detail:'Faltan la fecha del evento y el número de póliza.',time:'01/10',target:'task',read:false},
 {id:4,claim:'CLM-000518',actor:'Asistente',title:'Propuesta asistida lista',detail:'Resultado sugerido: Cubierto, con cita a la cláusula STD-COV-01. Requiere tu revisión.',time:'Ayer',target:'task',read:false},
 {id:5,claim:'CLM-000624',actor:'Asistente',title:'Vía de gestión sugerida: investigación',detail:'Denuncia tardía y daños no descritos en el relato.',time:'Ayer',target:'task',read:true}
];
let notifSeq=5,notifFilter='unread';
function pushNotif(n){notifs.unshift({id:++notifSeq,time:now(),read:false,target:'task',...n});renderNotif();if(!$('listView').hidden)renderWelcome();announce(`Nueva notificación: ${n.title}, ${n.claim}`)}
function renderNotif(){
  const unread=notifs.filter(n=>!n.read).length,b=$('notifBadge');
  b.textContent=unread>9?'9+':unread;b.hidden=!unread;
  $('notifBtn').setAttribute('aria-label',unread?`Notificaciones, ${unread} sin leer`:'Notificaciones');
  document.querySelectorAll('[data-nf]').forEach(x=>x.setAttribute('aria-pressed',x.dataset.nf===notifFilter));
  const list=notifFilter==='unread'?notifs.filter(n=>!n.read):notifs;
  $('notifSub').textContent=unread?`${unread} sin leer`:'Estás al día';
  const item=n=>`<li><button type="button" class="notif-item ${n.read?'read':''}" onclick="openNotif(${n.id})">
    <span class="dot" aria-hidden="true"></span>
    <span><strong>${esc(n.title)}${n.read?'':'<span class="sr-only"> (sin leer)</span>'}</strong><p>${esc(n.detail)}</p>
    <span class="notif-meta"><span class="actor ${n.actor}">${n.actor}</span>${esc(n.claim)}</span></span>
    <time>${esc(n.time)}</time></button></li>`;
  const today=list.filter(n=>/^Hoy/.test(n.time)),older=list.filter(n=>!/^Hoy/.test(n.time));
  const grp=(t,a)=>a.length?`<li class="notif-group" role="presentation">${t}</li>${a.map(item).join('')}`:'';
  $('notifList').innerHTML=list.length?grp('Hoy',today)+grp('Anteriores',older):`<li class="notif-empty">${notifFilter==='unread'?'Estás al día. No tienes notificaciones sin leer.':'No hay notificaciones.'}</li>`;
}
function toggleNotif(force){const p=$('notifPanel'),bd=$('notifBackdrop'),isOpen=!p.hidden,open=force??!isOpen;if(open===isOpen)return;
  $('notifBtn').setAttribute('aria-expanded',open);['main','.topbar'].forEach(sel=>{const el=document.querySelector(sel);if(open)el.setAttribute('inert','');else el.removeAttribute('inert')});
  if(open){renderNotif();p.hidden=false;bd.hidden=false;requestAnimationFrame(()=>{p.classList.add('open');bd.classList.add('show')});setTimeout(()=>p.querySelector('.notif-close').focus(),30)}
  else{p.classList.remove('open');bd.classList.remove('show');setTimeout(()=>{p.hidden=true;bd.hidden=true},220);if(force!==false||document.activeElement===document.body||p.contains(document.activeElement))$('notifBtn').focus()}}
function setNotifFilter(f){notifFilter=f;renderNotif()}
function markAllRead(){notifs.forEach(n=>n.read=true);renderNotif();announce('Todas las notificaciones marcadas como leídas')}
function openNotif(id){const n=notifs.find(x=>x.id===id);n.read=true;renderNotif();toggleNotif(false);setTimeout(()=>openNotifTarget(n),0)}
function openNotifTarget(n){openClaim(n.claim);
  if(n.target==='docs')selectTab('docs',true);else if(n.target==='history')selectTab('history',true);
  else{$('task').scrollIntoView({block:'start'});$('taskTitle').setAttribute('tabindex','-1');$('taskTitle').focus()}}
document.addEventListener('keydown',e=>{const p=$('notifPanel');if(p.hidden)return;
  if(e.key==='Escape'){toggleNotif(false);return}
  if(e.key==='Tab'){const f=[...p.querySelectorAll('button')].filter(b=>b.offsetParent!==null||true);const first=f[0],last=f[f.length-1];
    if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}}});

/* ============ BANDEJA ============ */
let filter='all',query='';
function renderFilters(){
  const counts={all:CLAIMS.length,review:0,todo:0,waiting:0,closed:0,sla:0};CLAIMS.forEach(c=>{const s=stateOf(c);counts[s==='derived'?'closed':s]++;if(isUrgent(c))counts.sla++});
  const defs=[['all','Todos'],['review','Requieren revisión'],['todo','Por gestionar'],['waiting','Esperando'],['sla','Plazo ≤ 10 días'],['closed','Resueltos y derivados']];
  $('filters').innerHTML=defs.map(([k,l])=>`<button type="button" class="filter" aria-pressed="${filter===k}" onclick="setFilter('${k}')">${l}<span class="count" aria-label="${counts[k]} casos">${counts[k]}</span></button>`).join('');
}
const USER={first:'Daniela',full:'Daniela Muñoz'};
function isUrgent(c){return !['closed','derived'].includes(stateOf(c))&&slaOf(c).warn}
function renderWelcome(){
  const hr=new Date().getHours(),g=hr<12?'Buenos días':hr<20?'Buenas tardes':'Buenas noches';
  const dl=TODAY.toLocaleDateString('es-CL',{weekday:'long',day:'numeric',month:'long'}).replace(',','');$('todayLabel').textContent=dl.charAt(0).toUpperCase()+dl.slice(1);
  $('listTitle').textContent=`${g}, ${USER.first}`;
  const n=k=>CLAIMS.filter(c=>stateOf(c)===k).length,rev=n('review'),wait=n('waiting'),urg=CLAIMS.filter(isUrgent).length,unread=notifs.filter(x=>!x.read).length;
  $('welcomeLead').textContent=rev?`Tienes ${rev} caso${rev>1?'s':''} que necesita${rev>1?'n':''} tu revisión${unread?` y ${unread} ${unread>1?'notificaciones':'notificación'} sin leer`:''}. Te sugerimos comenzar por los de plazo más próximo.`:'No tienes casos bloqueados. Buen momento para avanzar los que están por gestionar.';
  const tile=(k,v,l,s)=>`<button type="button" class="kpi" onclick="setFilter('${k}');document.querySelector('.table-card').scrollIntoView({block:'start',behavior:'smooth'})" aria-label="${v} ${l}. ${s.replace(' →','')}"><b aria-hidden="true">${v}</b><span aria-hidden="true">${l}</span><small aria-hidden="true">${s}</small></button>`;
  $('kpis').innerHTML=tile('review',rev,rev===1?'requiere tu revisión':'requieren tu revisión','Ver casos bloqueados →')+tile('sla',urg,urg===1?'plazo vence en 10 días o menos':'plazos vencen en 10 días o menos','Priorizar por plazo →')+tile('waiting',wait,'esperando antecedentes','Ver casos en espera →');
}
function toggleUserMenu(force){const m=$('userMenu'),open=force??m.hidden;m.hidden=!open;$('userBtn').setAttribute('aria-expanded',open);if(open)m.querySelector('[role=menuitem]').focus()}
document.addEventListener('click',e=>{if(!$('userMenu').hidden&&!$('userWrap').contains(e.target))toggleUserMenu(false)});
$('userMenu').addEventListener('keydown',e=>{if(e.key==='Escape'){toggleUserMenu(false);$('userBtn').focus()}if(e.key==='Tab')toggleUserMenu(false)});
function logout(){toggleUserMenu(false);if(!$('notifPanel').hidden)toggleNotif(false);
  document.querySelector('main').hidden=true;document.querySelector('.top-right').hidden=true;$('logoutView').hidden=false;document.title='Sesión cerrada · Gestión de siniestros';$('logoutTitle').focus()}
function login(){$('logoutView').hidden=true;document.querySelector('main').hidden=false;document.querySelector('.top-right').hidden=false;
  $('detailView').hidden=true;$('listView').hidden=false;filter='all';renderList();document.title='Gestión de siniestros';$('listTitle').focus();announce(`Bienvenida de vuelta, ${USER.first}`)}
function setFilter(k){filter=k;renderList();announce(`${visible().length} siniestros`)}
function visible(){
  const order={review:0,todo:1,waiting:2,derived:3,closed:3},q=query.toUpperCase(),r=normRut(query);
  return CLAIMS.filter(c=>{const st=stateOf(c);if(filter==='sla'){if(!isUrgent(c))return false}else if(filter==='closed'){if(st!=='closed'&&st!=='derived')return false}else if(filter!=='all'&&st!==filter)return false;if(!q)return true;return c.number.includes(q)||(r.length>=4&&normRut(c.rut).includes(r))})
    .sort((a,b)=>order[stateOf(a)]-order[stateOf(b)]||parseD(a.reported)-parseD(b.reported));
}
function renderList(){
  renderWelcome();renderFilters();const items=visible();
  $('rows').innerHTML=items.map(c=>{const s=STATES[stateOf(c)],sla=slaOf(c);return `<tr data-id="${c.number}">
    <td data-label="Siniestro"><button type="button" class="claim-link" onclick="openClaim('${c.number}')">${c.number}</button></td>
    <td data-label="RUT declarante">${esc(c.rut)}</td>
    <td data-label="Estado"><span class="badge ${s.cls}">${s.label}</span></td>
    <td data-label="Próximo paso" class="next">${esc(nextOf(c))}</td>
    <td data-label="Plazo"><span class="sla ${sla.warn?'warn':''}">${esc(sla.text)}<small>${esc(sla.sub)}</small></span></td>
    <td class="chev" aria-hidden="true"><span class="mi">chevron_right</span></td></tr>`}).join('');
  $('empty').hidden=items.length>0;
}
$('rows').addEventListener('click',e=>{if(e.target.closest('button'))return;const tr=e.target.closest('tr');if(tr)openClaim(tr.dataset.id)});
function onSearch(e){e.preventDefault();query=$('q').value.trim();const ex=CLAIMS.find(c=>c.number===query.toUpperCase());if(ex){openClaim(ex.number);return}renderList();announce(`${visible().length} resultado(s)`)}
$('q').addEventListener('input',e=>{if(!e.target.value){query='';renderList()}});

/* ============ DETALLE ============ */
let active=null;
function openClaim(id){active=CLAIMS.find(c=>c.number===id);if(!active)return;$('listView').hidden=true;$('detailView').hidden=false;try{window.scrollTo(0,0)}catch(e){}
  selectTab('summary');renderDetail();renderChat();$('claimTitle').focus();document.title=`${id} · Gestión de siniestros`}
function goList(){$('detailView').hidden=true;$('listView').hidden=false;document.title='Gestión de siniestros';renderList();(document.querySelector(`tr[data-id="${active?.number}"] .claim-link`)||$('listTitle')).focus()}
function refresh(){if(!$('detailView').hidden&&active)renderDetail();else renderList()}

function renderDetail(){
  const c=active,s=STATES[stateOf(c)],sla=slaOf(c);
  $('claimTitle').textContent=c.number;const b=$('claimState');b.className=`badge ${s.cls}`;b.textContent=s.label;
  const sl=$('claimSla');sl.className=`sla ${sla.warn?'warn':''}`;sl.innerHTML=`${esc(sla.text)}<small>${esc(sla.sub)}</small>${['cerrado','investigacion'].includes(c.stage)?'':'<small>Plazo configurado para demostración</small>'}`;
  const conflict=c.block==='conflict';
  const mi=(l,v)=>`<div><dt>${l}</dt><dd class="${v?'':'missing'}">${v?esc(v):'No informada'}</dd></div>`;
  $('meta').innerHTML=mi('Fecha del evento',c.eventDate)+mi('Fecha de denuncia',c.reported)+mi('Póliza',c.policy)+mi('Patente',conflict?`${c.plate} / ${c.altPlate}`:c.plate)+mi('Vehículo',c.vehicle);
  renderMilestones(c);
  renderTask();
  $('summary').textContent=c.summary;
  const row=(l,v,src,cls)=>`<div class="data-row"><dt>${l}</dt><dd class="${cls||''}">${v}</dd><div class="data-src">${src||''}</div></div>`;
  const f=(v,src)=>v?[esc(v),src,'']:['No encontrado en documentos','','missing'];
  $('dataList').innerHTML=row('Fecha del evento',...f(c.eventDate,c.eventFromReply?'Antecedentes del asegurado':'Denuncia del siniestro'))+
    row('Lugar',...f(c.location,'Denuncia del siniestro'))+row('N° de póliza',...f(c.policy,c.eventFromReply?'Certificado de cobertura':'Expediente'))+row('Vehículo',...f(c.vehicle,'Expediente'))+
    (conflict?row('Patente',`${esc(c.plate)} / ${esc(c.altPlate)} <button class="btn sm" type="button" style="margin-left:8px" onclick="focusTask()">Resolver</button>`,'2 documentos con valores distintos','conflict'):row('Patente',esc(c.plate),c.resolution?'Confirmada por analista':'Denuncia del siniestro'))+
    (c.calcConfirmed?row('Reserva preliminar',clp(c.calcResult.reserve),`Regla determinística · deducible ${clp(c.calcResult.deductible)} · validada por analista`):'');
  renderCustomer();renderDocs();renderTimeline();
}
function renderMilestones(c){
  const inv=c.stage==='investigacion';
  const exp=c.stage!=='expediente'?['done','Expediente completo','Documentos y datos obligatorios disponibles']
    :['blocked','Expediente completo',c.block==='conflict'?'Discrepancia de patente por resolver':c.block==='missing'?'Faltan fecha del evento y póliza':c.block==='extracted'?'Datos extraídos pendientes de confirmación':c.block==='evidence'?'Documento excluido por seguridad: revisar evidencia':'Esperando antecedentes del asegurado (simulado)'];
  const res=c.calcConfirmed?['done','Reserva validada',`${clp(c.calcResult.reserve)} · deducible ${clp(c.calcResult.deductible)}`]:['todo','Reserva validada',c.calcResult?'Cálculo listo para validar':'Pendiente'];
  const dec=c.decision?['done','Decisión de cobertura',`${RESULT[c.decision.result].label}${c.decision.action==='accept'?' · propuesta aceptada':c.decision.action==='modify'?' · propuesta modificada':' · propuesta rechazada'}`]:['todo','Decisión de cobertura',c.proposal?'Propuesta lista para revisar':'Pendiente'];
  const com=inv?['na','Comunicación al asegurado','No aplica: caso derivado a investigación']:c.stage==='cerrado'?['done','Comunicación al asegurado',`Envío simulado · impugnación (demo) hasta ${fmtD(c.appealUntil)}`]:['todo','Comunicación al asegurado','Pendiente'];
  const lab={done:'completado',blocked:'bloqueado',todo:'pendiente',na:'no aplica'},ico={done:'✓',blocked:'!',todo:'',na:'–'};
  $('milestones').innerHTML=[exp,res,dec,com].map(([st,t,d])=>`<li class="${st}"><span class="ms-icon" aria-hidden="true">${ico[st]}</span><span><strong>${t}<span class="sr-only">: ${lab[st]}</span></strong><span class="d">${esc(d)}</span></span></li>`).join('');
}
function focusTask(){$('task').scrollIntoView({block:'start',behavior:'smooth'});setTimeout(()=>($('task').querySelector('input,textarea,.btn.primary')||$('taskTitle')).focus(),250)}

/* ---------- Siguiente paso ---------- */
function renderTask(){
  const t=taskFor(active);
  $('task').className=`task ${t.tone}`;
  $('task').innerHTML=`<div class="task-top"><span class="task-icon">${ICON[t.icon||t.tone]}</span><div style="flex:1;min-width:0"><p class="task-label">${t.label}</p><h2 id="taskTitle">${t.title}</h2><div class="task-body">${t.body||''}</div>${t.extra||''}</div></div>${t.actions?`<div class="task-actions">${t.actions}</div>`:''}`;
}
function taskFor(c){
  const L='Siguiente paso';
  if(c.stage==='expediente'){
    if(c.requesting)return {tone:'warn',label:L,title:'Solicitar antecedentes al asegurado',body:'<p>Revisa y edita la solicitud preparada por el asistente. En esta demostración el envío es simulado: no se conecta con un canal real.</p>',extra:requestForm(c)};
    if(c.block==='extracted'){const p=c.pendingExtract;return {tone:'warn',label:L,title:'Confirma los datos extraídos del documento recibido',
      body:`<p>Estos datos se extrajeron de <strong>${esc(p.doc)}</strong>. El expediente se actualizará solo cuando los confirmes.</p>`,
      extra:`<dl class="proposal"><div class="proposal-head"><strong>Datos extraídos</strong><span class="badge warn">Requiere revisión del analista</span></div>${p.fields.map(f=>`<div class="proposal-row"><dt>${esc(f[0])}</dt><dd><strong>${esc(f[1])}</strong><span class="tag kind">Hecho · ${esc(p.doc)}</span></dd></div>`).join('')}</dl>`,
      actions:`<button class="btn primary" type="button" onclick="confirmExtracted()">Confirmar datos extraídos</button><button class="btn" type="button" onclick="openExtractedDoc()">Ver documento</button><button class="btn ghost" type="button" onclick="rejectExtracted()">Los datos no son correctos</button>`}}
    if(c.block==='conflict')return {tone:'warn',label:L,title:'La patente no coincide entre documentos',
      body:`<p>Se encontraron <strong>${esc(c.plate)}</strong> y <strong>${esc(c.altPlate)}</strong>. El sistema no elige un valor: confirma cuál es correcto o pide un documento oficial.</p>${c.padron?'<p><strong>Llegó el padrón del vehículo</strong>, revísalo antes de confirmar.</p>':''}`,
      extra:c.resolving?resolveForm(c):'',actions:c.resolving?'':`<button class="btn primary" type="button" onclick="openForm('resolving')">Resolver discrepancia</button><button class="btn ghost" type="button" onclick="selectTab('docs',true)">Ver documentos</button>`};
    if(c.block==='evidence'){const ok=c.docs.filter(d=>d.state!=='blocked'),bl=c.docs.filter(d=>d.state==='blocked');return {tone:'warn',label:L,title:'Revisa la evidencia disponible',
      body:`<p>Se procesaron ${c.docs.length} documentos. <strong>${bl.length} fue excluido de la evidencia</strong> porque contiene contenido que intenta modificar el comportamiento del asistente.</p><p>Ese documento no se usó para responder, no modificó datos del expediente y no se usará en la propuesta asistida.</p>`,
      extra:`<dl class="proposal"><div class="proposal-head"><strong>Evidencia del expediente</strong><span class="badge warn">Requiere revisión del analista</span></div>${ok.map(d=>`<div class="proposal-row"><dt>${esc(d.type)}</dt><dd>${esc(d.name)}<span class="badge ok kind">Utilizable</span></dd></div>`).join('')}${bl.map(d=>`<div class="proposal-row"><dt>${esc(d.type)}</dt><dd>${esc(d.name)}<span class="badge error kind">Excluido de la evidencia</span></dd></div>`).join('')}</dl>`,
      actions:`<button class="btn primary" type="button" onclick="confirmEvidence()">Confirmar evidencia disponible</button><button class="btn ghost" type="button" onclick="openBlockedDoc()">Revisar documento excluido</button>`}}
    if(c.block==='missing')return {tone:'warn',label:L,title:'Revisa los antecedentes faltantes',
      body:'<p>No encontramos estos datos en el expediente:</p><ul><li><strong>Fecha del evento</strong></li><li><strong>Número de póliza</strong></li></ul><p>Los datos del siniestro deben venir de un documento que los respalde, por lo que no se ingresan a mano.</p>',
      actions:`<button class="btn primary" type="button" onclick="openForm('requesting')">Preparar solicitud de antecedentes</button><button class="btn ghost" type="button" onclick="pickFile()">Ya tengo el documento: adjuntar</button>`};
    if(c.block==='waiting')return {tone:'info',icon:'wait',label:'En espera',title:'Esperando antecedentes del asegurado',
      body:`<p>Simulaste el envío de la solicitud el ${esc(c.request.sentAt)}:</p><ul>${c.request.docs.map(d=>`<li>${esc(d)}</li>`).join('')}</ul><p>En esta demostración, usa "Simular respuesta (demo)" para representar la respuesta del asegurado, o adjunta un documento. El plazo configurado para la demo sigue corriendo.</p>`,
      actions:`<button class="btn" type="button" onclick="pickFile()">Adjuntar documento recibido</button><button class="btn ghost" type="button" onclick="simulateReply('${c.number}')">Simular respuesta (demo)</button>`};
  }
  if(c.stage==='calculo'){
    if(c.calcResult)return {tone:'info',label:L,title:'Revisa el cálculo antes de validarlo',body:calcBox(c.calcResult),actions:`<button class="btn primary" type="button" onclick="confirmCalc()">Validar reserva preliminar</button>`};
    return {tone:'info',label:L,title:'Calcular deducible y reserva preliminar',body:'<p>Los parámetros están en el expediente y la póliza. Cálculo realizado mediante regla determinística, no mediante razonamiento generativo de IA.</p>',actions:`<button class="btn primary" type="button" onclick="runCalc()">Calcular</button>`};
  }
  if(c.stage==='propuesta'){
    const inv=c.proposal.result==='investigation';
    return {tone:inv?'warn':'info',label:L,title:inv?'El asistente sugiere derivar a investigación':'Revisa la propuesta asistida de cobertura',
      body:'<p>El asistente generó esta propuesta con la evidencia disponible; no es una resolución. Acepta, modifica o rechaza: la decisión es tuya y queda registrada con su justificación.</p>',
      extra:proposalBox(c)+(c.deciding?decisionForm(c):''),
      actions:c.deciding?'':`<button class="btn primary" type="button" onclick="acceptProposal()">${inv?'Aceptar y derivar':'Aceptar propuesta'}</button><button class="btn" type="button" onclick="openForm('deciding','modify')">Modificar</button><button class="btn ghost" type="button" onclick="openForm('deciding','reject')">Rechazar propuesta</button>`};
  }
  if(c.stage==='comunicacion'){
    return {tone:'info',label:L,title:'Revisa la comunicación y simula su envío',
      body:`<p>Resultado decidido por el analista: <span class="badge ${RESULT[c.decision.result].cls}">${RESULT[c.decision.result].label}</span><span class="actor Analista kind">Decisión del analista</span></p><p>El asistente preparó el borrador. Revísalo y edítalo antes de simular el envío.</p>${recipientHtml(c)}`,
      extra:`<div class="field"><label for="draft">Borrador de la comunicación <span class="opt">· generado por el asistente, editable</span></label>
        <textarea class="draft" id="draft" aria-describedby="draftHelp">${esc(c.draft??(c.draft=draftFor(c)))}</textarea>
        <p class="help" id="draftHelp">Incluye resultado, montos, fundamento y plazo de impugnación configurado para la demo (10 días hábiles). Borrador de apoyo: su generación integrada aún está en validación (HU-10, parcial).</p><p class="error" id="sendError" hidden></p></div>`,
      actions:`<button class="btn primary" type="button" onclick="sendCommunication()">Simular envío</button>`};
  }
  if(c.stage==='investigacion')return {tone:'warn',icon:'info',label:'Estado',title:'Derivado a investigación',body:`<p>Derivado por el analista el ${esc(c.closedAt)}. Justificación: “${esc(c.decision.reason||'Acepta la vía de gestión sugerida por las señales de alerta')}”.</p><p>El alcance de esta demostración termina en la derivación.</p>`,actions:`<button class="btn" type="button" onclick="selectTab('history',true)">Ver en historial</button>`};
  return {tone:'ok',label:'Estado',title:'Flujo completado en la demostración',body:`<p>Simulaste el envío de la resolución el ${esc(c.closedAt)} (destinatario: ${esc(c.recipient.email)}, ${c.recipient.from==='sys'?'obtenido del sistema de clientes simulado':'correo declarado en el expediente'}). No se conectó con un canal real ni con los sistemas oficiales de cierre del siniestro.</p><p>Plazo de impugnación configurado para la demo: 10 días hábiles, hasta el <strong>${fmtD(c.appealUntil)}</strong>.</p>`,actions:`<button class="btn" type="button" onclick="selectTab('history',true)">Ver en historial</button>`};
}
function calcBox(r){return `<div class="calc-grid"><div><span>Pérdida estimada</span><b>${clp(r.loss)}</b></div><div><span>Deducible</span><b>${clp(r.deductible)}</b></div><div><span>Reserva preliminar</span><b>${clp(r.reserve)}</b></div></div>
  <p class="calc-note"><span class="tag corp">Regla determinística</span> Cálculo realizado mediante regla determinística. Deducible = mayor entre ${r.pct}% de la pérdida (${clp(r.loss*r.pct/100)}) y el mínimo de ${clp(r.min)}. Reserva = pérdida − deducible.</p><p class="calc-note">Regla configurada para demostración.</p>`}
const KIND={fact:'<span class="tag kind">Hecho</span>',rule:'<span class="tag corp kind">Regla determinística</span>',ai:'<span class="tag ai kind">Propuesta IA</span>'};
function proposalBox(c){const p=c.proposal,r=c.calcResult;return `<dl class="proposal">
  <div class="proposal-head"><strong>Propuesta asistida de cobertura</strong><span class="badge warn">Requiere revisión del analista</span></div>
  <div class="proposal-row"><dt>Resultado propuesto</dt><dd><span class="badge ${RESULT[p.result].cls}">${RESULT[p.result].label}</span>${KIND.ai}</dd></div>
  ${p.result==='investigation'?'':`<div class="proposal-row"><dt>Fundamento</dt><dd>Cláusula <strong>${p.clause.code}</strong> · ${p.clause.name}${KIND.fact}<br><span class="tag corp">Condicionado ${p.clause.doc} · pág. ${p.clause.page}</span> <span class="tag">Fuente simulada</span></dd></div>`}
  ${p.result==='investigation'?'':`<div class="proposal-row"><dt>Evidencia utilizada</dt><dd>${c.docs.filter(d=>d.state!=='blocked').map(d=>`<span class="tag">${esc(d.name)}</span>`).join(' ')} <span class="tag corp">Policy Core · Fuente simulada</span></dd></div>`}
  <div class="proposal-row"><dt>Vía de gestión sugerida</dt><dd><strong>${p.via==='rapida'?'Vía rápida':'Investigación'}</strong>${KIND.ai}<br>${esc(p.viaReason)}</dd></div>
  ${p.alerts.length?`<div class="proposal-row"><dt>Señales de alerta</dt><dd>${KIND.fact.replace('kind','kind" style="margin-left:0')}<ul>${p.alerts.map(a=>`<li>${esc(a.t)} <span class="tag">${esc(a.src)}</span></li>`).join('')}</ul></dd></div>`:''}
  <div class="proposal-row"><dt>Montos</dt><dd>Deducible ${clp(r.deductible)} · Reserva preliminar <strong>${clp(r.reserve)}</strong>${KIND.rule}<br><span class="help">Calculados con regla configurada para demostración y validados por el analista.</span></dd></div>
  <div class="ai-note">${ICON.spark} Propuesta asistida generada por IA. No es una resolución: la decisión corresponde al analista.</div>
  <p class="help" style="margin:8px 0 0">Visión funcional: la propuesta de cobertura (HU-07) y la vía de gestión (HU-09) aún no están validadas en las PoC 1–11.</p></dl>`}
function decisionForm(c){
  const rej=c.deciding==='reject';
  const opts=Object.entries(RESULT).filter(([k])=>rej||k!==c.proposal.result).map(([k,v])=>`<label class="option"><input type="radio" name="result" value="${k}"><span style="font-weight:600">${v.label}</span></label>`).join('');
  return `<form class="subform" id="decisionForm" onsubmit="submitDecision(event)" novalidate>
    <h3>${rej?'Rechazar la propuesta y definir el resultado':'Modificar el resultado propuesto'}</h3>
    <fieldset aria-describedby="resultError" style="border:0;padding:0;margin:0"><legend class="sr-only">Resultado</legend>${opts}<p class="error" id="resultError" hidden>Selecciona un resultado.</p></fieldset>
    <div class="field"><label for="reason">${rej?'¿Por qué descartas la propuesta?':'¿Por qué modificas el resultado?'} <span class="opt">(obligatorio)</span></label>
      <textarea id="reason" aria-describedby="reasonHelp reasonError"></textarea><p class="help" id="reasonHelp">Se registra en el historial y sirve para mejorar las propuestas.</p><p class="error" id="reasonError" hidden>Escribe una justificación.</p></div>
    <div class="resolve-actions"><button class="btn primary" type="submit">Confirmar decisión</button><button class="btn ghost" type="button" onclick="closeForms()">Cancelar</button></div></form>`;
}
function resolveForm(c){
  const pol=POLICIES[c.policy];
  const opt=(v,src,hint)=>`<label class="option"><input type="radio" name="plate" value="${esc(v)}"><span><span class="option-value">${esc(v)}</span><span class="option-src" style="display:block">${src}</span>${hint?`<span class="option-hint" style="display:block">${hint}</span>`:''}</span></label>`;
  const h1=[pol?.plate===c.plate?`Coincide con la póliza ${esc(c.policy)}`:'',c.padron?'y con el padrón recibido':''].join(' ').trim();
  return `<form class="resolve" id="resolveForm" onsubmit="confirmResolve(event)" novalidate>
    <fieldset aria-describedby="plateError"><legend>¿Cuál es la patente correcta?</legend>
      ${opt(c.plate,'Fuente: denuncia_sintetica_poc6.pdf · Denuncia del siniestro',h1)}
      ${opt(c.altPlate,'Fuente: scan_poc6_valido.png · Valor leído desde imagen escaneada','')}
      ${c.padron?'':`<label class="option"><input type="radio" name="plate" value="__none"><span><span style="font-weight:600">No puedo confirmarlo</span><span class="option-src" style="display:block">Solicitar el padrón del vehículo al asegurado</span></span></label>`}
      <p class="error" id="plateError" hidden>Selecciona una opción.</p></fieldset>
    <div class="field"><label for="reason">Justificación <span class="opt">(obligatoria)</span></label>
      <textarea id="reason" aria-describedby="reasonHelp reasonError"></textarea><p class="help" id="reasonHelp">Queda registrada en el historial del caso.</p><p class="error" id="reasonError" hidden>Escribe una justificación para registrar tu decisión.</p></div>
    <div class="resolve-actions"><button class="btn primary" type="submit">Confirmar decisión</button><button class="btn ghost" type="button" onclick="closeForms()">Cancelar</button></div></form>`;
}
function requestForm(c){
  const docs=c.block==='conflict'?['Padrón o certificado de inscripción del vehículo']:['Documento con la fecha del siniestro (denuncia o constancia de Carabineros)','Póliza o certificado de cobertura vigente'];
  const msg=`Estimado/a asegurado/a:\n\nPara continuar con la evaluación del siniestro N° ${c.number}, necesitamos que nos envíe los siguientes antecedentes:\n\n${docs.map(d=>'• '+d).join('\n')}\n\nPuede responder a este mensaje adjuntando los documentos.\n\nSaludos cordiales,\nÁrea de Siniestros`;
  return `<form class="subform" id="requestForm" onsubmit="sendRequest(event)" novalidate>
    <fieldset style="border:0;padding:0;margin:0" aria-describedby="docsError"><legend style="font-weight:700;font-size:15px;margin-bottom:4px">Documentos a solicitar</legend>
      ${docs.map((d,i)=>`<label class="check"><input type="checkbox" name="rdoc" value="${esc(d)}" checked> ${esc(d)}</label>`).join('')}
      <p class="error" id="docsError" hidden>Selecciona al menos un documento.</p></fieldset>
    <div class="field"><label for="reqMsg">Mensaje <span class="opt">· borrador del asistente, editable</span></label><textarea class="draft" id="reqMsg" style="min-height:200px">${esc(msg)}</textarea></div>
    <p class="help">El envío de esta solicitud es simulado para la demostración.</p>
    <div class="resolve-actions"><button class="btn primary" type="submit">Simular envío de solicitud</button><button class="btn ghost" type="button" onclick="closeForms()">Cancelar</button></div></form>`;
}
function draftFor(c){
  const r=c.calcResult,d=c.decision;
  const head=`Estimado/a asegurado/a:\n\nLe informamos el resultado de la evaluación del siniestro N° ${c.number}, ocurrido el ${c.eventDate}, asociado a la póliza ${c.policy}.\n\n`;
  const body=d.result==='cover'?`Resultado: el siniestro se encuentra cubierto bajo la cobertura "${CLAUSE.name}".\nMonto estimado de la pérdida: ${clp(r.loss)}\nDeducible aplicado: ${clp(r.deductible)}\nMonto estimado tras deducible: ${clp(r.reserve)}\n\nFundamento: cláusula ${CLAUSE.code} del condicionado ${CLAUSE.doc}.`
    :`Resultado: el siniestro no se encuentra cubierto.\nFundamento: ${d.reason}`;
  return head+body+`\n\nSi no está de acuerdo con esta resolución, puede impugnarla dentro de los 10 días hábiles siguientes a su recepción.\n\nSaludos cordiales,\nÁrea de Siniestros`;
}

/* ---------- Acciones del analista (HITL) ---------- */
function openForm(key,val){const c=active;['resolving','requesting','deciding'].forEach(k=>c[k]=false);c[key]=val||true;
  if(key==='requesting'){c.requesting=true}renderTask();focusTask()}
function closeForms(){const c=active;['resolving','requesting','deciding'].forEach(k=>c[k]=false);renderTask();($('task').querySelector('.btn.primary')||$('taskTitle')).focus()}
function validateRequired(radioName,errId){const sel=document.querySelector(`input[name=${radioName}]:checked`),reason=$('reason').value.trim();
  $(errId).hidden=!!sel;$('reasonError').hidden=!!reason;$('reason').setAttribute('aria-invalid',!reason);
  if(!sel){document.querySelector(`input[name=${radioName}]`).focus();return null}if(!reason){$('reason').focus();return null}return {value:sel.value,reason}}
function afterChange(msg){renderDetail();$('taskTitle').setAttribute('tabindex','-1');$('taskTitle').focus();if(msg)toast(msg)}
function confirmResolve(e){e.preventDefault();const c=active,v=validateRequired('plate','plateError');if(!v)return;
  c.resolving=false;
  if(v.value==='__none'){log(c,'Analista','Patente no confirmada por analista',`Se solicitará el padrón. Motivo: ${v.reason}`);c.requesting=true;renderDetail();focusTask();return}
  c.plate=v.value;c.block=null;c.resolution=v;c.docs.forEach(d=>{if(d.state==='review')d.state='validated'});
  log(c,'Analista','Datos confirmados por analista',`Patente ${v.value}. Motivo: ${v.reason}`);c.stage='calculo';afterChange('Decisión registrada. El caso avanza a cálculo.')}
function sendRequest(e){e.preventDefault();const c=active;const docs=[...document.querySelectorAll('input[name=rdoc]:checked')].map(x=>x.value);
  $('docsError').hidden=docs.length>0;if(!docs.length){document.querySelector('input[name=rdoc]').focus();return}
  c.request={docs,sentAt:`${fmtD(TODAY)} ${clock()}`,prev:c.block};c.requesting=false;c.block='waiting';
  log(c,'Analista','Solicitud simulada',`Envío simulado al asegurado: ${docs.join(' · ')}`);afterChange('Envío de solicitud simulado');
  const num=c.number;clearTimeout(c.replyTimer);c.replyTimer=setTimeout(()=>simulateReply(num),12000)}
function simulateReply(num){const c=CLAIMS.find(x=>x.number===num);if(c.block!=='waiting')return;clearTimeout(c.replyTimer);
  const d={...c.reply,state:'review'};c.docs.push(d);log(c,'Sistema','Documento recibido en demo',`${d.name} (respuesta simulada del asegurado).`);log(c,'Sistema','Documento procesado',d.name);
  applyReply(c,d.name);pushNotif({claim:c.number,actor:'Sistema',title:'Antecedentes recibidos (demo)',detail:`${d.type}: datos extraídos pendientes de tu revisión.`});refresh()}
function applyReply(c,docName){
  const doc=docName||c.reply.name,fields=c.reply.fields.map(f=>`${f[0]}: ${f[1]}`).join(' · ');
  if(c.request?.prev==='conflict'||c.altPlate&&!c.resolution){c.padron=true;c.block='conflict';log(c,'Sistema','Datos extraídos',`${fields} (${doc}). La patente queda pendiente de confirmación del analista.`);return}
  c.pendingExtract={doc,fields:c.reply.fields,apply:c.reply.apply};c.block='extracted';
  log(c,'Sistema','Datos extraídos',`${fields} (${doc}). Pendientes de confirmación del analista.`)}
function confirmExtracted(){const c=active,p=c.pendingExtract;if(!p)return;
  Object.assign(c,p.apply);c.eventFromReply=true;c.block=null;c.stage='calculo';c.pendingExtract=null;
  c.docs.forEach(d=>{if(d.name===p.doc)d.state='validated'});
  c.summary=c.summary.replace('La fecha del evento y el número de póliza no aparecen en los documentos disponibles.','La fecha del evento y la póliza se completaron con antecedentes del asegurado, confirmados por el analista.');
  log(c,'Analista','Datos confirmados por analista',`${p.fields.map(f=>`${f[0]}: ${f[1]}`).join(' · ')}. Expediente actualizado.`);afterChange('Datos confirmados. Expediente actualizado.')}
function rejectExtracted(){const c=active,p=c.pendingExtract;if(!p)return;c.pendingExtract=null;c.block='missing';
  c.docs.forEach(d=>{if(d.name===p.doc)d.state='validated'});
  log(c,'Analista','Datos extraídos no confirmados',`${p.doc}: el analista indicó que los datos no son correctos. El expediente no se modificó.`);openForm('requesting')}
function confirmEvidence(){const c=active;const ok=c.docs.filter(d=>d.state!=='blocked').length;c.block=null;c.stage='calculo';
  log(c,'Analista','Evidencia revisada por analista',`${ok} documentos confirmados como evidencia. El documento excluido por seguridad no se utiliza.`);afterChange('Evidencia confirmada. El caso avanza a cálculo.')}
function openBlockedDoc(){const c=active,i=c.docs.findIndex(d=>d.state==='blocked');if(i>=0)c.docs[i].open=true;renderDocs();selectTab('docs',true)}
function openExtractedDoc(){const c=active,i=c.docs.findIndex(d=>d.name===c.pendingExtract?.doc);if(i>=0)c.docs[i].open=true;renderDocs();selectTab('docs',true)}
function runCalc(fromChat){const c=active;computeCalc(c);const r=c.calcResult;
  log(c,'Sistema','Cálculo determinístico ejecutado',`Deducible ${clp(r.deductible)} · Reserva ${clp(r.reserve)}. Regla configurada para demostración. Pendiente de validación del analista.`);
  if(!fromChat)botPush(c,{title:'Cálculo realizado mediante regla determinística',body:`<p>Deducible: <strong>${clp(r.deductible)}</strong><br>Reserva preliminar: <strong>${clp(r.reserve)}</strong></p><p>Valídalo en “Siguiente paso”.</p>`,sources:['Regla configurada para demostración','Presupuesto de reparación']});
  renderDetail();if(!fromChat){$('taskTitle').setAttribute('tabindex','-1');$('taskTitle').focus()}}
function confirmCalc(){const c=active;c.calcConfirmed=true;log(c,'Analista','Reserva validada por analista',clp(c.calcResult.reserve));
  c.stage='propuesta';makeProposal(c);log(c,'Asistente','Propuesta asistida generada',`Resultado sugerido: ${RESULT[c.proposal.result].label}${c.proposal.result==='investigation'?'':` · cita ${CLAUSE.code}`}. Pendiente de revisión del analista.`);
  afterChange('Reserva validada. El asistente preparó una propuesta asistida para tu revisión.');
  const num=c.number;setTimeout(()=>{if(active?.number!==num||$('detailView').hidden)pushNotif({claim:num,actor:'Asistente',title:'Propuesta asistida lista',detail:'Revisa el resultado sugerido y su fundamento.'})},400)}
function acceptProposal(){const c=active;c.decision={action:'accept',result:c.proposal.result,reason:''};
  log(c,'Analista','Propuesta aceptada por analista',`Sin cambios. Resultado decidido: ${RESULT[c.proposal.result].label}`);finishDecision(c)}
function submitDecision(e){e.preventDefault();const c=active,v=validateRequired('result','resultError');if(!v)return;
  c.decision={action:c.deciding,result:v.value,reason:v.reason};
  log(c,'Analista',c.deciding==='reject'?'Propuesta rechazada por analista':'Propuesta modificada por analista',`Resultado decidido: ${RESULT[v.value].label}. Motivo: ${v.reason}`);c.deciding=false;finishDecision(c)}
function finishDecision(c){
  if(c.decision.result==='investigation'){c.stage='investigacion';c.closedAt=`${fmtD(TODAY)} ${clock()}`;afterChange('Caso derivado a investigación');return}
  c.stage='comunicacion';c.draft=null;afterChange('Decisión registrada. Prepara la comunicación.')}
async function sendCommunication(){const c=active,err=$('sendError');c.draft=$('draft').value;
  if(!c.recipient){err.textContent='Falta el destinatario. Consulta el correo en el sistema de clientes antes de simular el envío.';err.hidden=false;($('recipientBtn')||$('draft')).focus();return}
  if(!c.draft.trim()){err.textContent='El borrador está vacío. Escribe o restaura el texto antes de simular el envío.';err.hidden=false;$('draft').focus();return}
  if(!await mdConfirm({title:'¿Simular envío de la resolución?',text:'Esta acción representa el envío para efectos de la demostración. No se conectará con un canal real.',ok:'Simular envío',icon:'send'}))return;c.draft=$('draft')?.value??c.draft;
  const edited=c.draft!==draftFor(c);c.stage='cerrado';c.closedAt=`${fmtD(TODAY)} ${clock()}`;c.appealUntil=addBizDays(TODAY,10);
  log(c,'Analista','Envío simulado de resolución',`Destinatario: ${c.recipient.from==='sys'?'correo obtenido del sistema de clientes':'correo declarado en el expediente'}. ${edited?'Borrador editado por el analista. ':''}Plazo de impugnación configurado para la demo: hasta ${fmtD(c.appealUntil)}.`);afterChange('Envío simulado. Flujo completado en la demostración.')}

/* ---------- Cliente, documentos, historial ---------- */
function custCall(c){const rec=CUST_DB[c.rut];
  if(rec&&rec.failOnce&&!rec.failed){rec.failed=true;return {status:'unavailable'}}
  return rec?{status:'found',id:rec.id}:{status:'notfound'}}
function logCust(c,actor,r,field){
  if(r.status==='unavailable')return log(c,actor,'Sistema de clientes no disponible','La consulta no pudo realizarse. Resultado desconocido: no se interpreta como cliente no encontrado.');
  if(r.status==='notfound')return log(c,actor,'Verificación de cliente','Búsqueda realizada: el RUT del declarante no figura en el sistema de clientes.');
  log(c,actor,field?'Consulta de dato de contacto':'Verificación de cliente',field?`Campo consultado: ${FIELD[field].toLowerCase()} (${r.id}). Solo lectura; el valor no se guarda en el expediente.`:`Cliente encontrado (${r.id}). No se consultaron datos personales.`)}
function verifyCustomer(c,actor){const r=custCall(c);c.custCheck=r;logCust(c,actor,r);return r}
function fetchField(c,field,actor){const r=custCall(c);c.custCheck=r;logCust(c,actor,r,r.status==='found'?field:null);
  return r.status==='found'?{...r,field,value:CUST_DB[c.rut][field]}:r}
function custStatus(v){return !v?['Sin verificar','neutral']:v.status==='found'?['Cliente','ok']:v.status==='notfound'?['No figura como cliente','warn']:['Resultado desconocido','error']}
function renderCustomer(){const c=active,v=c.custCheck,f=c.custField,[sl,sc]=custStatus(v);
  const declSrc=(c.docs.find(d=>/Denuncia|Declaraci/.test(d.type))||c.docs[0]).name;
  let note='';
  if(v?.status==='unavailable')note=`<p class="cust-note error" role="status">No fue posible consultar el sistema de clientes en este momento. Esto no significa que el declarante no sea cliente.</p>`;
  else if(v?.status==='notfound')note=`<p class="cust-note warn" role="status">La búsqueda se realizó correctamente y el RUT no figura como cliente. No hay datos corporativos que consultar.</p>`;
  else if(f&&f.field==='email'&&c.declared&&c.declared.email!==f.value)note=`<p class="cust-note">El correo declarado en ${esc(c.declared.src)} (${esc(c.declared.email)}) difiere del registrado. Se usa el sistema de clientes como fuente de referencia.</p>`;
  $('customerCard').innerHTML=`<div class="card-head"><h2>Cliente</h2><span class="tag sys">Sistema de clientes · solo lectura · simulado</span></div>
    <div class="customer-info">
      <div><span>RUT del declarante</span><b>${esc(c.rut)}</b><small>Fuente: expediente (${esc(declSrc)})</small></div>
      <div><span>Verificación</span><b><span class="badge ${sc}">${sl}</span></b><small>${v?.status==='found'?'Código '+esc(v.id):v?'Consulta registrada en historial':'Aún no consultado'}</small></div>
      ${f&&v?.status==='found'?`<div><span>${FIELD[f.field]}</span><b>${esc(f.value)}</b><small>Fuente: sistema de clientes</small></div>`:''}
    </div>${note}
    <div class="cust-actions">
      <button class="btn${v?'':' primary'}" type="button" onclick="uiVerify()"><span class="mi" aria-hidden="true">person_search</span>${!v?'Verificar si es cliente':v.status==='unavailable'?'Reintentar':'Verificar nuevamente'}</button>
      ${v?.status==='found'?`<label for="custField" class="sr-only">Dato de contacto a consultar</label><select id="custField">${Object.entries(FIELD).map(([k,l])=>`<option value="${k}" ${f?.field===k?'selected':''}>${l}</option>`).join('')}</select><button class="btn" type="button" onclick="uiFetch()">Consultar dato</button>`:''}
    </div>
    <p class="help" style="margin-top:10px">Verificar solo confirma si es cliente, sin datos personales. Cada dato de contacto se consulta por separado, uno a la vez, y no se guarda en el expediente.</p>`}
function uiVerify(){const c=active,r=verifyCustomer(c,'Analista');c.custField=null;renderCustomer();renderTimeline();
  announce(r.status==='found'?'Cliente verificado':r.status==='notfound'?'No figura como cliente':'Sistema de clientes no disponible');document.querySelector('#customerCard .btn')?.focus()}
function uiFetch(){const c=active,field=$('custField').value,r=fetchField(c,field,'Analista');c.custField=r.status==='found'?{field,value:r.value}:null;renderCustomer();renderTimeline();
  announce(r.status==='found'?FIELD[field]+' consultado':'No fue posible consultar el dato');$('custField')?.focus()}
function recipientHtml(c){
  if(c.recipient)return `<p>Destinatario: <strong>${esc(c.recipient.email)}</strong><span class="tag ${c.recipient.from==='sys'?'sys':''} kind">${c.recipient.from==='sys'?'Sistema de clientes · simulado':'Correo declarado · expediente'}</span></p>`;
  const v=c.recipientTry;
  const msg=v==='unavailable'?'<p class="cust-note error" role="status">No fue posible consultar el sistema de clientes. Reintenta; no se asume que el declarante no sea cliente.</p>'
    :v==='notfound'?`<p class="cust-note warn" role="status">El declarante no figura como cliente.${c.declared?' Puedes usar el correo declarado en el expediente, indicando su origen.':''}</p>`:'';
  return `<p>Destinatario: <strong>pendiente</strong>. El correo se consulta en el sistema de clientes (solo ese dato).</p>${msg}
    <div class="cust-actions" style="margin-top:8px"><button class="btn" id="recipientBtn" type="button" onclick="uiRecipient()"><span class="mi" aria-hidden="true">person_search</span>${v==='unavailable'?'Reintentar consulta':'Consultar correo del destinatario'}</button>
    ${v==='notfound'&&c.declared?`<button class="btn ghost" type="button" onclick="useDeclared()">Usar correo declarado</button>`:''}</div>`}
function uiRecipient(){const c=active,r=fetchField(c,'email','Analista');c.recipientTry=r.status;if(r.status==='found')c.recipient={email:r.value,from:'sys'};renderTask();renderCustomer();renderTimeline();
  announce(r.status==='found'?'Destinatario obtenido':'No fue posible obtener el destinatario');($('recipientBtn')||$('draft'))?.focus()}
function useDeclared(){const c=active;c.recipient={email:c.declared.email,from:'decl'};log(c,'Analista','Destinatario desde el expediente',`Correo declarado en ${c.declared.src}; el declarante no figura como cliente.`);renderTask();renderTimeline();$('draft').focus()}
const DOC_STATES={ok:['Procesado','ok'],review:['Requiere revisión','warn'],processing:['Procesando…','neutral'],validated:['Revisado por analista','info'],blocked:['Bloqueado por seguridad','error']};
function renderDocs(){const c=active;$('docCount').textContent=c.docs.length;
  $('docList').innerHTML=c.docs.map((d,i)=>{const[l,cls]=DOC_STATES[d.state],img=/\.(png|jpe?g)$/i.test(d.name);
    return `<div class="doc"><div class="doc-row"><span class="doc-icon" aria-hidden="true">${img?ICON.img:ICON.doc}</span><div style="min-width:0"><div class="doc-name">${esc(d.name)}</div><div class="doc-type">${esc(d.type)}</div></div><span class="badge ${cls}">${l}</span>
    ${d.state==='processing'?'':`<button class="btn sm" type="button" aria-expanded="${!!d.open}" aria-controls="ex-${i}" onclick="toggleDoc(${i})">${d.open?(d.state==='blocked'?'Ocultar detalle':'Ocultar datos'):(d.state==='blocked'?'Ver detalle':'Ver datos extraídos')}</button>`}</div>
    ${d.open?(d.state==='blocked'?`<div class="doc-extract" id="ex-${i}"><h3>Excluido de la evidencia</h3><p>Se detectó contenido que intenta modificar el comportamiento del asistente. Este documento no se utilizó como evidencia.</p></div>`:`<div class="doc-extract" id="ex-${i}"><h3>Datos extraídos de este documento</h3><dl>${(d.fields||[]).map(f=>`<dt>${esc(f[0])}</dt><dd>${esc(f[1])}</dd>`).join('')}</dl></div>`):''}</div>`}).join('')}
function toggleDoc(i){active.docs[i].open=!active.docs[i].open;renderDocs();document.querySelectorAll('#docList .doc-row .btn')[i]?.focus()}
function renderTimeline(){$('timeline').innerHTML=active.history.map(h=>`<li><span class="actor ${h.actor}">${h.actor}</span><div><strong>${esc(h.title)}</strong><p>${esc(h.detail)}</p></div><time>${esc(h.time)}</time></li>`).join('')}
function pickFile(){$('file').click()}
function onFile(e){const f=e.target.files?.[0];e.target.value='';if(!f)return;
  if(!['application/pdf','image/jpeg','image/png'].includes(f.type)){toast('Formato no admitido. Usa PDF, JPG o PNG.');return}
  if(f.size>10*1024*1024){toast('El archivo supera los 10 MB permitidos.');return}
  const c=active,doc={name:f.name,type:'Documento adjuntado por analista',state:'processing',fields:[]};c.docs.push(doc);
  log(c,'Analista','Documento adjuntado',f.name);selectTab('docs');renderDetail();toast('Documento recibido. Procesando…');
  setTimeout(()=>{doc.state='ok';
    log(c,'Sistema','Documento procesado',f.name);
    if(c.stage==='expediente'&&(c.block==='missing'||c.block==='waiting')&&c.reply){doc.fields=c.reply.fields;doc.type=c.reply.type;doc.state='review';c.request=c.request||{prev:c.block};applyReply(c,f.name)}else doc.fields=[['Tipo de documento','Por clasificar']];
    if(active!==c||$('detailView').hidden)pushNotif({claim:c.number,actor:'Sistema',title:'Documento procesado',detail:`${f.name} ya está disponible en el expediente.`,target:'docs'});
    refresh();announce(`${f.name} procesado`)},1800)}

/* Tabs accesibles */
function selectTab(name,focus){document.querySelectorAll('[role=tab]').forEach(t=>{const on=t.dataset.tab===name;t.setAttribute('aria-selected',on);t.tabIndex=on?0:-1;$(t.getAttribute('aria-controls')).hidden=!on;if(on&&focus)t.focus()})}
document.querySelector('.tabs').addEventListener('click',e=>{const t=e.target.closest('[role=tab]');if(t)selectTab(t.dataset.tab)});
document.querySelector('.tabs').addEventListener('keydown',e=>{const tabs=[...document.querySelectorAll('[role=tab]')];let i=tabs.indexOf(document.activeElement);if(i<0)return;
  if(e.key==='ArrowRight')i=(i+1)%tabs.length;else if(e.key==='ArrowLeft')i=(i-1+tabs.length)%tabs.length;else if(e.key==='Home')i=0;else if(e.key==='End')i=tabs.length-1;else return;e.preventDefault();selectTab(tabs[i].dataset.tab,true)});

/* ============ ASISTENTE ============ */
function sess(){return active.sessions.find(s=>s.id===active.sessionId)}
function renderSessions(){const c=active;$('sessionSelect').innerHTML=c.sessions.map(s=>`<option value="${s.id}" ${s.id===c.sessionId?'selected':''}>${esc(s.title)}</option>`).join('');$('delSession').hidden=c.sessions.length<2}
function switchSession(id){active.sessionId=Number(id);renderChat();announce('Conversación cambiada: '+sess().title)}
function newSession(){const c=active;c.sessionSeq++;c.sessions.push({id:c.sessionSeq,title:`Conversación ${c.sessionSeq}`,chat:[]});c.sessionId=c.sessionSeq;renderChat();$('askInput').focus();announce('Nueva conversación iniciada')}
async function deleteSession(){const c=active;if(c.sessions.length<2)return;if(!await mdConfirm({title:'¿Eliminar conversación?',text:`“${sess().title}” y sus mensajes se perderán.`,ok:'Eliminar',icon:'delete'}))return;c.sessions=c.sessions.filter(s=>s.id!==c.sessionId);c.sessionId=c.sessions[c.sessions.length-1].id;renderChat();toast('Conversación eliminada')}
function suggestionsFor(c){
  if(c.stage==='expediente')return c.block==='conflict'?['¿Hay inconsistencias?','¿Qué falta para continuar?','¿El declarante es cliente?']:c.block==='evidence'?['¿Qué documentos hay?','¿Qué falta para continuar?','¿El declarante es cliente?']:['¿Qué falta para continuar?','¿Qué documentos hay?','¿El declarante es cliente?'];
  if(c.stage==='calculo')return ['Calcula deducible y reserva','¿El declarante es cliente?','Resume el caso'];
  if(c.stage==='propuesta')return ['¿Por qué propones este resultado?','¿Qué dice la cláusula?','Aprueba este siniestro'];
  if(c.stage==='comunicacion')return ['¿El declarante es cliente?','¿Cuál es su correo?','Envía la comunicación'];
  return ['Resume el caso','¿El declarante es cliente?','¿Qué documentos hay?'];
}
function renderChat(){const c=active,chat=sess().chat;renderSessions();
  $('log').innerHTML=chat.length?chat.map(msgHtml).join(''):`<div class="welcome"><strong>¿En qué te ayudo con ${c.number}?</strong>Puedo resumir el expediente, explicar de dónde sale cada dato, consultar póliza y condicionado, verificar si el declarante es cliente (solo lectura), ejecutar cálculos con reglas y preparar propuestas y borradores. Las decisiones son tuyas.</div>`;
  $('log').scrollTop=$('log').scrollHeight;
  $('suggest').innerHTML=suggestionsFor(c).map(s=>`<button type="button" class="chip" onclick="ask(this.textContent)">${esc(s)}</button>`).join('')}
function msgHtml(m){if(m.role==='user')return `<div class="msg user"><span class="sr-only">Tú: </span><p>${esc(m.text)}</p></div>`;
  const label=m.kind==='guard'?`${ICON.lock} Acción reservada al analista`:m.kind==='empty'?'Sin información suficiente':'Asistente';
  return `<div class="msg bot ${m.kind}"><div class="msg-label">${label}</div>${m.title?`<p class="lead">${m.title}</p>`:''}${m.body||''}
  ${m.sources?.length?`<div class="sources"><span class="sr-only">Fuentes:</span>${m.sources.map(s=>`<span class="tag ${/sistema de clientes/i.test(s)?'sys':/póliza|condicionado|policy|regla/i.test(s)?'corp':''}">${esc(s)}</span>`).join('')}</div>`:''}${m.action?`<div class="act">${m.action}</div>`:''}</div>`}
function botPush(c,m){c.sessions.find(s=>s.id===c.sessionId).chat.push({role:'bot',kind:'answer',...m});if(c===active)renderChat()}
function bot(m){botPush(active,m)}
async function ask(text){
  $('askInput').value='';
  const localSession=sess();
  localSession.chat.push({role:'user',text});
  renderChat();
  const c=active;
  if(INTEGRATION.connected){
    try{
      const backendId=await ensureBackendSession(c,localSession);
      const r=await apiJson('/assistant/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:backendId,message:text})});
      if(active!==c)return;
      botPush(c,{kind:'answer',title:'Respuesta del backend integrado',body:`<p>${esc(r.response)}</p>`,sources:[`PoC 1–11 · provider clientes: ${esc(INTEGRATION.provider)}`]});
      return;
    }catch(err){
      setBackendStatus(false,'Backend no disponible; usando simulación local.');
    }
  }
  setTimeout(()=>{if(active===c)answer(text)},350)
}
function onAsk(e){e.preventDefault();const t=$('askInput').value.trim();if(t)ask(t)}
$('askInput').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();onAsk(e)}});
$('askInput').addEventListener('input',e=>{e.target.style.height='auto';e.target.style.height=Math.min(e.target.scrollHeight,120)+'px'});
const goTask=label=>`<button class="btn sm" type="button" onclick="focusTask()">${label}</button>`;
function answer(text){
  const s=norm(text),c=active;
  const guard=(title,body,what,action)=>{bot({kind:'guard',title,body,action});log(c,'Asistente','Solicitud bloqueada',what);renderTimeline()};
  if(/ignora|system prompt|instrucciones internas|olvida tus instrucciones/.test(s))return guard('No puedo procesar esa solicitud.','<p>Solo apoyo el análisis de siniestros automotrices.</p>','Intento de modificar instrucciones del asistente.');
  if(/aprueba|aprobar/.test(s))return guard('No puedo aprobar el siniestro.','<p>Esta acción corresponde al analista responsable. Puedes aceptar, modificar o rechazar la propuesta asistida desde “Siguiente paso”.</p>','Solicitud de aprobación.',c.stage==='propuesta'?goTask('Ir a la propuesta'):'');
  if(/rechaza|rechazar/.test(s))return guard('No puedo rechazar el siniestro.','<p>Esta acción corresponde al analista responsable.</p>','Solicitud de rechazo.');
  if(/cierra|cerrar/.test(s))return guard('No puedo cerrar el caso.','<p>Esta acción corresponde al analista responsable. En esta demostración, el flujo se completa cuando el analista simula el envío de la resolución.</p>','Solicitud de cierre.');
  if(/actualiza|modifica|cambia|elimina|borra|crea/.test(s)&&/cliente|correo|telefono|direccion|datos/.test(s))return guard('No puedo modificar datos de clientes.','<p>La integración con el sistema de clientes es de solo lectura: permite verificar y consultar, pero no crear, modificar ni eliminar registros.</p>','Solicitud de modificar datos del cliente.');
  if(/envia|enviar|manda/.test(s))return guard('No puedo enviar comunicaciones.','<p>Esta acción corresponde al analista responsable. Puedo preparar el borrador; el envío (simulado en esta demo) lo realizas tú.</p>','Solicitud de envío de comunicación.',c.stage==='comunicacion'?goTask('Ir al borrador'):'');
  if(/por que|fundamento|propones|cobertura|cubierto/.test(s)){
    if(!c.proposal)return bot({kind:'empty',title:'Aún no hay propuesta asistida.',body:`<p>Primero hay que completar: ${esc(nextOf(c).toLowerCase())}.</p>`});
    const p=c.proposal;return bot(p.result==='investigation'?{title:'Vía de gestión sugerida: investigación.',body:`<p>La información recuperada muestra estas señales de alerta:</p><ul style="margin:6px 0 0;padding-left:18px">${p.alerts.map(a=>`<li>${esc(a.t)} <span class="tag">${esc(a.src)}</span></li>`).join('')}</ul><p>Es una recomendación; la derivación la decide el analista.</p>`,sources:c.docs.filter(d=>d.state!=='blocked').map(d=>d.name)}
      :{title:`Resultado sugerido: ${RESULT[p.result].label}.`,body:`<p>Según la evidencia disponible, el daño informado es compatible con la cobertura ${CLAUSE.name} (cláusula ${CLAUSE.code}), y la validación de vigencia indica que la póliza estaba vigente a la fecha del evento. ${esc(p.viaReason)}</p><p>Es una propuesta asistida: la decisión corresponde al analista.</p>`,sources:[`Condicionado ${CLAUSE.doc} · pág. ${CLAUSE.page} · Fuente simulada`,'Policy Core · Fuente simulada']});
  }
  if(/clausula|condicionado/.test(s))return bot({title:`La información recuperada indica la cláusula ${CLAUSE.code}: ${CLAUSE.name}.`,body:`<p>Documento ${CLAUSE.doc}, página ${CLAUSE.page}.</p>`,sources:['Condicionado de póliza · Fuente simulada']});
  if(/falta|pendiente|continuar/.test(s)){
    if(c.block==='missing')return bot({title:'Ningún documento disponible permite confirmar la fecha del evento ni el número de póliza.',body:'<p>Puedo preparar la solicitud de antecedentes al asegurado.</p>',sources:['declaracion_colision.pdf'],action:goTask('Solicitar antecedentes')});
    if(c.block==='extracted')return bot({title:'Hay datos extraídos pendientes de tu confirmación.',body:`<p>Se extrajeron de ${esc(c.pendingExtract.doc)}. El expediente se actualizará cuando los confirmes.</p>`,sources:[c.pendingExtract.doc],action:goTask('Revisar datos extraídos')});
    if(c.block==='evidence')return bot({title:'Falta tu revisión de la evidencia disponible.',body:'<p>Un documento fue excluido por seguridad y no se utiliza. Confirma la evidencia válida para continuar.</p>',sources:c.docs.filter(d=>d.state!=='blocked').map(d=>d.name),action:goTask('Revisar evidencia')});
    if(c.block==='conflict')return bot({title:'Se detectó una discrepancia en la patente.',body:`<p><strong>${esc(c.plate)}</strong> y <strong>${esc(c.altPlate)}</strong>. La confirmación corresponde al analista.</p>`,action:goTask('Resolver discrepancia')});
    return bot({title:`Siguiente paso: ${esc(nextOf(c).toLowerCase())}.`});
  }
  if(/inconsisten|discrepancia|diferencia/.test(s))return c.block==='conflict'?bot({title:'Se detectó una diferencia en la patente.',body:`<p><strong>${esc(c.plate)}</strong> en la denuncia y <strong>${esc(c.altPlate)}</strong> en el antecedente escaneado. No selecciono un valor automáticamente: la confirmación corresponde al analista.</p>`,sources:['denuncia_sintetica_poc6.pdf','scan_poc6_valido.png'],action:goTask('Resolver discrepancia')}):bot({title:'No se detectaron inconsistencias en los campos comparados.',sources:['Expediente']});
  if(/resume|resumen|antecedentes/.test(s))return bot({title:'Resumen del caso',body:`<p>Según la evidencia disponible: ${esc(c.summary)}</p>`,sources:['Expediente']});
  if(/documentos/.test(s)){const ok=c.docs.filter(d=>d.state!=='blocked'),bl=c.docs.length-ok.length;return bot({title:`Hay ${ok.length} documento(s) utilizables como evidencia.`,body:`<ul style="margin:6px 0 0;padding-left:18px">${ok.map(d=>`<li>${esc(d.type)}</li>`).join('')}</ul>${bl?`<p>${bl} documento fue excluido de la evidencia por seguridad.</p>`:''}`,action:`<button class="btn sm" type="button" onclick="selectTab('docs',true)">Ver documentos</button>`})}
  if(/perfil completo|todos (los|sus) datos|ficha completa/.test(s))return bot({kind:'empty',title:'Solo consulto el dato necesario.',body:'<p>Por minimización de datos, consulto un campo a la vez: correo, teléfono o dirección. ¿Cuál necesitas?</p>',action:`<button class="btn sm" type="button" onclick="ask('¿Cuál es el correo del declarante?')">Correo</button><button class="btn sm" type="button" onclick="ask('¿Cuál es el teléfono del declarante?')">Teléfono</button>`});
  const fld=/correo|email|mail/.test(s)?'email':/telefono|celular|fono/.test(s)?'phone_number':/direccion|domicilio/.test(s)?'address':/contacto/.test(s)?'email':null;
  if(fld){const S=sess();
    if(/\bsus?\b/.test(s)&&!S.custRef)return bot({kind:'empty',title:'En esta conversación aún no hay una persona de referencia.',body:'<p>Cada conversación tiene su propio contexto. ¿Te refieres al declarante del caso?</p>',action:`<button class="btn sm" type="button" onclick="ask('¿Cuál es el ${FIELD[fld].toLowerCase()} del declarante?')">${FIELD[fld]} del declarante</button>`});
    S.custRef=true;const r=fetchField(c,fld,'Asistente');renderTimeline();if(c===active)renderCustomer();
    if(r.status==='unavailable')return bot({kind:'empty',title:'No fue posible consultar el sistema de clientes en este momento.',body:'<p>Esto no significa que el declarante no sea cliente. Puedes reintentar en unos minutos.</p>',sources:[SRC_CUST]});
    if(r.status==='notfound')return bot({kind:'empty',title:'El declarante no figura como cliente.',body:`<p>No hay datos corporativos de contacto.${c.declared?` El expediente tiene un correo declarado en ${esc(c.declared.src)}, que no está confirmado por el sistema de clientes.`:''}</p>`,sources:[SRC_CUST]});
    const diff=fld==='email'&&c.declared&&c.declared.email!==r.value;
    return bot({title:`${FIELD[fld]} registrado: ${esc(r.value)}`,body:`<p>Consulté nuevamente el sistema de clientes y solicité solo este dato; no uso valores recordados en la conversación.</p>${diff?`<p>Difiere del correo declarado en ${esc(c.declared.src)}. Prevalece el sistema de clientes como fuente de referencia.</p>`:''}`,sources:[SRC_CUST]})}
  if(/cliente/.test(s)){sess().custRef=true;const r=verifyCustomer(c,'Asistente');renderTimeline();if(c===active)renderCustomer();
    if(r.status==='unavailable')return bot({kind:'empty',title:'No fue posible consultar el sistema de clientes en este momento.',body:'<p>El resultado es desconocido: no puedo afirmar que sea ni que no sea cliente.</p>',sources:[SRC_CUST]});
    if(r.status==='notfound')return bot({title:'El declarante no figura como cliente.',body:`<p>Busqué el RUT ${esc(c.rut)}, tomado del expediente. La búsqueda se realizó correctamente.</p>`,sources:[SRC_CUST]});
    return bot({title:`Sí, el declarante está registrado como cliente (código ${esc(r.id)}).`,body:`<p>Verifiqué con el RUT ${esc(c.rut)} del expediente. No consulté datos personales; si necesitas uno, pídelo y lo consulto por separado.</p>`,sources:[SRC_CUST]})}
  if(/poliza|vigente|vigencia/.test(s))return c.policy?bot({title:`La validación de vigencia indica que ${c.policy} estaba vigente a la fecha del evento.`,sources:['Policy Core · Fuente simulada']}):bot({kind:'empty',title:'No hay número de póliza en los antecedentes.',action:goTask('Solicitar antecedentes')});
  if(/deducible|reserva|calcul/.test(s)){if(c.stage==='expediente')return bot({kind:'empty',title:'Aún no puedo calcular.',body:'<p>Primero debe completarse el expediente.</p>'});
    if(!c.calcResult)runCalc(true);const r=c.calcResult;return bot({title:'Cálculo realizado mediante regla determinística',body:`<p>Deducible: <strong>${clp(r.deductible)}</strong><br>Reserva preliminar: <strong>${clp(r.reserve)}</strong></p>${c.calcConfirmed?'<p class="calc-note">Validado por el analista.</p>':'<p class="calc-note">No es un resultado generado por IA. Valídalo en “Siguiente paso”.</p>'}`,sources:['Regla configurada para demostración','Presupuesto de reparación']})}
  bot({kind:'empty',title:'No encontré evidencia suficiente en el expediente para responder eso.',body:'<p>Prueba con una de las preguntas sugeridas.</p>'});
}


/* ============ INTEGRACIÓN REAL OPCIONAL ============ */
const INTEGRATION={connected:false,provider:'desconocido'};
async function apiJson(url,options={}){
  const r=await fetch(url,options);
  if(!r.ok){let d='';try{d=(await r.json()).detail||''}catch(e){};throw new Error(d||`HTTP ${r.status}`)}
  if(r.status===204)return null;
  return r.json();
}
function setBackendStatus(ok,text){
  INTEGRATION.connected=ok;
  const el=$('backendStatus');
  if(!el)return;
  el.textContent=text;
  el.classList.toggle('connected',ok);
  el.classList.toggle('error',!ok);
}
async function ensureBackendSession(c,localSession){
  if(localSession.backendId)return localSession.backendId;
  const r=await apiJson('/sessions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({claim_number:c.number})});
  localSession.backendId=r.session_id;
  return r.session_id;
}
async function detectBackend(){
  try{
    const info=await apiJson('/integration/info');
    INTEGRATION.provider=info.customer_provider||'desconocido';
    setBackendStatus(true,`Backend PoC 1–11 conectado · clientes vía ${INTEGRATION.provider.toUpperCase()}`);
  }catch(e){
    setBackendStatus(false,'Modo demo local · backend no conectado');
  }
}

renderNotif();renderList();detectBackend();
