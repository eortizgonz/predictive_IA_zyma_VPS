(() => {
  let drawerConversationId = localStorage.getItem('drawerConversationId') || null;
  let drawerMachines = [];
  const byId = id => document.getElementById(id);
  const esc = value => String(value ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;');
  const money = (value, currency='USD') => new Intl.NumberFormat('es-CL',{style:'currency',currency,maximumFractionDigits:0}).format(Number(value||0));

  const actionQuestions = {
    consultas: '¿Qué máquina debo intervenir primero y por qué?',
    diagnostico: 'Explica el diagnóstico del activo prioritario usando el manual y el modelo predictivo',
    finanzas: '¿Cuánto dinero está en riesgo y cuál es la pérdida potencial evitable?',
    tecnologia: '¿Qué datos, modelo y fuentes respaldan esta predicción?'
  };

  window.toggleExperienceDrawer = () => byId('experience-drawer')?.classList.contains('open') ? closeDrawer() : openDrawer();
  window.closeExperienceDrawer = closeDrawer;
  window.openExperience = mode => {
    openDrawer();
    window.setTimeout(() => runExperienceAction(mode), 220);
  };

  function openDrawer(){
    byId('experience-drawer')?.classList.add('open');
    byId('experience-backdrop')?.classList.add('open');
    byId('experience-drawer')?.setAttribute('aria-hidden','false');
    byId('drawer-input')?.focus();
  }
  function closeDrawer(){
    byId('experience-drawer')?.classList.remove('open');
    byId('experience-backdrop')?.classList.remove('open');
    byId('experience-drawer')?.setAttribute('aria-hidden','true');
  }

  async function loadDrawerMachines(){
    const response = await fetch('/api/machines');
    if(!response.ok) return;
    drawerMachines = await response.json();
    const select = byId('drawer-machine');
    const current = select?.value || '';
    if(select){
      select.innerHTML = '<option value="">Todas las máquinas</option>' + drawerMachines.map(m => `<option value="${esc(m.machine_id)}">${esc(m.machine_id)} · ${esc(m.status)}</option>`).join('');
      if([...select.options].some(o=>o.value===current)) select.value=current;
    }
  }

  function addMessage(role, html){
    const area = byId('drawer-messages'); if(!area) return;
    const row = document.createElement('div'); row.className=`drawer-message ${role}`;
    row.innerHTML=`<div class="avatar">${role==='user'?'TÚ':'AI'}</div><div class="bubble">${html}</div>`;
    area.appendChild(row); area.scrollTop=area.scrollHeight;
  }
  function setBusy(value){
    if(byId('drawer-status')) byId('drawer-status').hidden=!value;
    if(byId('drawer-submit')) byId('drawer-submit').disabled=value;
    if(byId('drawer-input')) byId('drawer-input').disabled=value;
  }

  // AJUSTE: Renderizar respuesta de texto de Ollama o JSON completo
  function responseHtml(data){
    const textContent = data.answer || data.reply;
    if (textContent) {
      return `<p>${esc(textContent).replace(/\n/g, '<br>')}</p>`;
    }

    const m=data.machine||{}, op=data.operational_impact||{}, fin=data.financial_impact||{};
    const actions=(data.actions||[]).map(a=>`<button type="button" data-drawer-action="${esc(a.id)}" data-machine="${esc(m.machine_id)}">${esc(a.label)}</button>`).join('');
    return `<strong>${esc(data.summary)}</strong><p>${esc(data.recommendation)}</p>
      <div class="drawer-kpis">
        <div class="drawer-kpi"><span>Activo</span><strong>${esc(m.machine_id)}</strong></div>
        <div class="drawer-kpi"><span>Riesgo</span><strong>${Number(m.failure_probability||0).toFixed(1)}%</strong></div>
        <div class="drawer-kpi"><span>Producción en riesgo</span><strong>${Number(op.production_units_at_risk||0)} unidades</strong></div>
        <div class="drawer-kpi"><span>Pérdida potencial</span><strong>${money(fin.potential_loss,fin.currency)}</strong></div>
      </div><div class="drawer-message-actions">${actions}</div>`;
  }

  async function ask(question){
    const q=String(question||'').trim(); if(!q) return;
    addMessage('user',`<p>${esc(q)}</p>`); if(byId('drawer-input')) byId('drawer-input').value=''; setBusy(true);
    try{
      // AJUSTE: Se incluye la clave 'prompt' para asegurar compatibilidad con Python
      const response=await fetch('/api/copilot/chat',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({
          prompt: q,
          question: q,
          profile: byId('drawer-profile')?.value || 'operations',
          machine_id: byId('drawer-machine')?.value || null,
          conversation_id: drawerConversationId
        })
      });
      const data=await response.json(); if(!response.ok) throw new Error(data.detail||'No fue posible completar la consulta');
      drawerConversationId=data.conversation_id || drawerConversationId; 
      if(drawerConversationId) localStorage.setItem('drawerConversationId',drawerConversationId);
      addMessage('assistant',responseHtml(data)); bindDrawerActions();
    }catch(error){addMessage('assistant',`<strong>No fue posible completar el análisis.</strong><p>${esc(error.message)}</p>`);}finally{setBusy(false);byId('drawer-input')?.focus();}
  }

  function runExperienceAction(mode){
    if(mode==='diagnostico'){
      const selected=byId('drawer-machine')?.value;
      const highestRiskMachineId = drawerMachines.length ? drawerMachines.reduce((max, m) => m.failure_probability > max.failure_probability ? m : max, drawerMachines[0]).machine_id : null;
      const target=selected || highestRiskMachineId;
      if(target && typeof getAiReport==='function'){
        const machine=drawerMachines.find(m=>m.machine_id===target);
        closeDrawer(); getAiReport(target, Number(machine?.failure_probability||0)); return;
      }
    }
    ask(actionQuestions[mode]||actionQuestions.consultas);
  }

  function bindDrawerActions(){
    document.querySelectorAll('[data-drawer-action]:not([data-bound])').forEach(btn=>{
      btn.dataset.bound='true'; btn.addEventListener('click',async()=>{
        const action=btn.dataset.drawerAction;
        if(action==='preview_work_order'){
          const response=await fetch('/api/work-orders/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({machine_id:btn.dataset.machine})});
          const draft=await response.json();
          addMessage('assistant',`<strong>Orden de trabajo preparada</strong><p>${esc(draft.title)}</p><div class="drawer-kpis"><div class="drawer-kpi"><span>Prioridad</span><strong>${esc(draft.priority)}</strong></div><div class="drawer-kpi"><span>Costo estimado</span><strong>${money(draft.estimated_cost)}</strong></div></div>`);
        }else if(action==='compare_scenarios') ask('Compara intervenir hoy versus esperar tres días');
        else ask('Explica por qué se generó esta predicción');
      });
    });
  }

  function init(){
    byId('drawer-form')?.addEventListener('submit',e=>{e.preventDefault();ask(byId('drawer-input')?.value);});
    document.querySelectorAll('[data-experience-action]').forEach(btn=>btn.addEventListener('click',()=>runExperienceAction(btn.dataset.experienceAction)));
    loadDrawerMachines().catch(console.error);
    setInterval(()=>loadDrawerMachines().catch(console.error),15000);
    addMessage('assistant','<strong>Bienvenido a Predictive Copilot.</strong><p>Cuéntame en que te puedo ayudar.</p>');
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init); else init();
})();