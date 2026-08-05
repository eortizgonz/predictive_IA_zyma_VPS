let highestRiskMachineId = null;
let currentDiagnosticMachineId = null;

async function loadMachines() {
    try {
        const response = await fetch('/api/machines');
        if (!response.ok) throw new Error('No fue posible consultar las máquinas');
        const machines = await response.json();
        let healthy = 0, warning = 0, critical = 0, totalRisk = 0;
        let highest = null;
        const rows = machines.map(machine => {
            if (machine.status === 'Healthy') healthy++;
            if (machine.status === 'Warning') warning++;
            if (machine.status === 'Critical') critical++;
            totalRisk += Number(machine.failure_probability || 0);
            if (!highest || machine.failure_probability > highest.failure_probability) highest = machine;
            const color = machine.status === 'Healthy' ? 'healthy' : machine.status === 'Warning' ? 'warning' : 'critical';
            const aiButton = machine.status === 'Warning' || machine.status === 'Critical'
                ? `<button class="btn-ai" onclick="getAiReport('${escapeHtml(machine.machine_id)}', ${Number(machine.failure_probability).toFixed(1)})">Diagnóstico IA</button>`
                : '<span style="color:#60738e;font-size:11px">Sin alerta</span>';
            return `<tr id="row-${escapeHtml(machine.machine_id)}" class="${machine.status === 'Critical' ? 'priority-row' : ''}">
                <td><strong>${escapeHtml(machine.machine_id)}</strong></td>
                <td>${Number(machine.temperature).toFixed(1)} °C</td>
                <td>${Number(machine.vibration).toFixed(2)}</td>
                <td><div class="risk-meter"><div class="risk-track"><i style="width:${Math.min(100, Number(machine.failure_probability))}%"></i></div><strong>${Number(machine.failure_probability).toFixed(1)}%</strong></div></td>
                <td><span class="status-badge ${color}">${escapeHtml(machine.status)}</span></td>
                <td>${escapeHtml(machine.prediction)}</td>
                <td>${aiButton}</td>
            </tr>`;
        }).join('');

        document.getElementById('healthy').textContent = healthy;
        document.getElementById('warning').textContent = warning;
        document.getElementById('critical').textContent = critical;
        document.getElementById('machine-count').textContent = `${machines.length} activos monitoreados`;
        document.getElementById('machine-body').innerHTML = rows;
        const averageRisk = machines.length ? totalRisk / machines.length : 0;
        document.getElementById('average-risk').textContent = `${averageRisk.toFixed(1)}%`;

        if (highest) {
            highestRiskMachineId = highest.machine_id;
            document.getElementById('highest-risk-label').textContent = `Mayor exposición: ${highest.machine_id}`;
            document.getElementById('executive-recommendation').textContent = `${highest.machine_id} concentra el mayor riesgo predictivo (${Number(highest.failure_probability).toFixed(1)}%).`;
            document.getElementById('executive-detail').textContent = highest.status === 'Critical'
                ? 'Se recomienda revisar el diagnóstico basado en manual y modelo antes de mantener la operación.'
                : 'Mantener seguimiento y validar la mejor ventana de intervención.';
        }
    } catch (error) {
        console.error('Error cargando máquinas:', error);
    }
}

async function getAiReport(machineId, visibleRisk) {
    currentDiagnosticMachineId = machineId;
    const modal = document.getElementById('aiModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalContent = document.getElementById('modalContent');
    if (!modal) return;
    modalTitle.textContent = `Diagnóstico IA · ${machineId}`;
    modalContent.innerHTML = '<div class="ai-validation-note">Consultando el manual técnico asociado y el modelo predictivo...</div>';
    modal.style.display = 'flex';
    try {
        const response = await fetch(`/api/machines/${encodeURIComponent(machineId)}/ai-report?risk=${visibleRisk}`);
        const data = await response.json();
        if (!response.ok || data.error || data.detail) {
            modalContent.innerHTML = `<p class="critical">${escapeHtml(data.error || data.detail || 'No fue posible generar el diagnóstico.')}</p>`;
            return;
        }
        const manual = data.manual || {};
        const model = data.modelo_predictivo || {};
        const telemetry = data.telemetria_actual || {};
        const actions = Array.isArray(data.acciones_mantenimiento) ? data.acciones_mantenimiento : [];
        const importances = Array.isArray(model.global_feature_importance) ? model.global_feature_importance.slice(0, 5) : [];
        const actionsHtml = actions.length ? `<ul>${actions.map(a => `<li>${escapeHtml(a)}</li>`).join('')}</ul>` : '<p>No hay acciones registradas.</p>';
        const factorsHtml = importances.length ? `<div class="model-factors">${importances.map(item => `<div class="model-factor-row"><span>${formatFeature(item.feature)}: ${formatValue(item.value)}</span><div class="model-factor-bar"><span style="width:${Math.max(2, item.importance)}%"></span></div><strong>${item.importance}%</strong></div>`).join('')}</div>` : '<p>No se dispone de importancia de variables.</p>';
        modalContent.innerHTML = `
            <div class="ai-diagnostic-summary"><h3>${escapeHtml(manual.equipment_name || machineId)}</h3><span class="risk-pill ${String(model.classification || '').toLowerCase()}">Riesgo ${Number(model.failure_probability || visibleRisk).toFixed(1)}% · ${escapeHtml(model.classification || data.prioridad_atencion)}</span><p>${escapeHtml(data.diagnostico_resumido || 'Sin diagnóstico disponible')}</p></div>
            <div class="diagnostic-grid">
                <section class="diagnostic-source-card manual-card"><h4>Manual técnico de la máquina</h4><p><strong>Equipo:</strong> ${escapeHtml(manual.equipment_name || 'No identificado')}</p><p><strong>Rango aplicable:</strong> ${escapeHtml(manual.risk_range || 'No disponible')}</p><p><strong>Diagnóstico técnico:</strong> ${escapeHtml(data.causa_probable || 'No disponible')}</p><h5>Acciones recomendadas</h5>${actionsHtml}<p class="diagnostic-source"><strong>Fuente consultada:</strong> ${escapeHtml(manual.source || 'Manual no disponible')}</p></section>
                <section class="diagnostic-source-card model-card"><h4>Modelo predictivo</h4><p><strong>Modelo:</strong> ${escapeHtml(model.model_name || 'No disponible')}</p><p><strong>Conclusión:</strong> ${escapeHtml(model.model_conclusion || 'No disponible')}</p><p><strong>Clasificación:</strong> ${escapeHtml(model.classification || 'No disponible')}</p><p><strong>Probabilidad:</strong> ${Number(model.failure_probability || 0).toFixed(1)}%</p><h5>Telemetría utilizada</h5><div class="telemetry-chips"><span>Temp. ${formatValue(telemetry.temperature)} °C</span><span>Vibración ${formatValue(telemetry.vibration)}</span><span>Corriente ${formatValue(telemetry.current)} A</span><span>Presión ${formatValue(telemetry.pressure)} bar</span><span>RPM ${formatValue(telemetry.rpm)}</span><span>Carga ${formatValue(telemetry.load)}%</span></div><h5>Importancia global de variables</h5>${factorsHtml}</section>
            </div><div class="ai-validation-note">${escapeHtml(model.disclaimer || 'Resultado sujeto a validación técnica.')}</div>`;
    } catch (error) {
        console.error('Error obteniendo diagnóstico:', error);
        modalContent.innerHTML = '<p class="critical">Ocurrió un error al consultar el manual y el modelo predictivo.</p>';
    }
}

function focusHighestRiskMachine() {
    if (!highestRiskMachineId) return;
    document.getElementById('assets').scrollIntoView({behavior:'smooth'});
    setTimeout(() => {
        const row = document.getElementById(`row-${highestRiskMachineId}`);
        if (row) { row.scrollIntoView({behavior:'smooth', block:'center'}); row.animate([{outline:'2px solid #ff6673'},{outline:'2px solid transparent'}],{duration:1800}); }
    }, 500);
}
function openDiagnosticInCopilot(){
    closeModal();
    document.getElementById('copilot').scrollIntoView({behavior:'smooth'});
    const machineSelect=document.getElementById('copilot-machine');
    if(machineSelect && currentDiagnosticMachineId){machineSelect.value=currentDiagnosticMachineId;}
    const input=document.getElementById('chat-input');
    if(input){input.value='Explica el diagnóstico de esta máquina usando el manual y el modelo predictivo';input.focus();}
}
function closeModal(){document.getElementById('aiModal').style.display='none';}
function escapeHtml(value){return String(value ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;');}
function formatFeature(feature){return({temperature:'Temperatura',vibration:'Vibración',current:'Corriente',pressure:'Presión',rpm:'RPM',load:'Carga',operating_hours:'Horas de operación'})[feature]||feature;}
function formatValue(value){const n=Number(value);return Number.isFinite(n)?n.toFixed(2):'N/D';}

document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal();});
document.querySelectorAll('.nav-item').forEach(item=>item.addEventListener('click',()=>{document.querySelectorAll('.nav-item').forEach(i=>i.classList.remove('active'));item.classList.add('active');}));
setInterval(loadMachines,15000);loadMachines();
