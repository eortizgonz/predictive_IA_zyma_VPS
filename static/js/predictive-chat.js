(() => {
    const questionsByProfile = {
        operations: [
            "¿Cuál es el estado actual de las máquinas?",
            "¿Cuál es la máquina con mayor riego de falla?",
            "¿Cuál es la máquina con menor riego de falla?"
                       
        ],
        finance: [
            
        ],
        technology: [
            
        ]
    };

    let machineCache = [];
    let conversationId = localStorage.getItem("predictiveConversationId") || null;
    const byId = id => document.getElementById(id);
    const escapeHtml = value => String(value ?? "")
        .replaceAll("&", "&amp;").replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");

    async function refreshMachines() {
        const response = await fetch("/api/machines");
        if (!response.ok) throw new Error("No fue posible consultar las máquinas");
        machineCache = await response.json();
        const select = byId("copilot-machine");
        if (!select) return;
        const current = select.value;
        select.innerHTML = '<option value="">Todas las máquinas</option>' + machineCache
            .map(m => `<option value="${escapeHtml(m.machine_id)}">${escapeHtml(m.machine_id)} · ${escapeHtml(m.status)}</option>`).join("");
        if ([...select.options].some(option => option.value === current)) select.value = current;
    }

    function renderQuickActions() {
        const profile = byId("user-profile")?.value || "operations";
        const container = byId("quick-actions");
        if (!container) return;
        container.innerHTML = questionsByProfile[profile]
            .map(question => `<button type="button" class="quick-action-btn" data-question="${escapeHtml(question)}">${escapeHtml(question)}</button>`).join("");
        container.querySelectorAll("button").forEach(button => button.addEventListener("click", () => submitQuestion(button.dataset.question)));
    }

    function appendMessage(role, html) {
        const messages = byId("chat-messages");
        if (!messages) return;
        const article = document.createElement("article");
        article.className = `chat-message ${role === "user" ? "user-message" : "assistant-message"}`;
        article.innerHTML = `<div class="message-avatar">${role === "user" ? "TÚ" : "AI"}</div><div class="message-content">${html}</div>`;
        messages.appendChild(article);
        messages.scrollTop = messages.scrollHeight;
    }

    function setAnalyzing(active) {
        if (byId("copilot-status")) byId("copilot-status").hidden = !active;
        if (byId("chat-submit")) byId("chat-submit").disabled = active;
        if (byId("chat-input")) byId("chat-input").disabled = active;
    }

    const money = (value, currency) => new Intl.NumberFormat("es-CL", { style: "currency", currency, maximumFractionDigits: 0 }).format(value);

    // AJUSTE: Soporte híbrido para Ollama (Texto) y Servicio Estructurado
    function renderResponse(data) {
        const textContent = data.answer || data.reply;
        if (textContent) {
            return `<p>${escapeHtml(textContent).replace(/\n/g, '<br>')}</p>`;
        }

        const machine = data.machine || {};
        const op = data.operational_impact || {};
        const fin = data.financial_impact || {};
        const factors = (data.explanation_factors || []).slice(0, 5)
            .map(item => `<div class="factor-row"><span>${escapeHtml(item.name)}</span><div class="factor-track"><i style="width:${item.contribution}%"></i></div><strong>${item.contribution}%</strong></div>`).join("");
        const sources = (data.sources || []).map(source => `<li><strong>${escapeHtml(source.name)}</strong>: ${escapeHtml(source.excerpt)}</li>`).join("");
        const actions = (data.actions || []).map(action => `<button type="button" class="copilot-action" data-action="${escapeHtml(action.id)}" data-machine="${escapeHtml(machine.machine_id)}">${escapeHtml(action.label)}</button>`).join("");
        return `
            <strong>${escapeHtml(data.summary)}</strong>
            <p>${escapeHtml(data.recommendation)}</p>
            <div class="copilot-metrics">
                <div class="copilot-metric"><span>Activo</span><strong>${escapeHtml(machine.machine_id)}</strong></div>
                <div class="copilot-metric"><span>Riesgo</span><strong>${Number(machine.failure_probability || 0).toFixed(1)}%</strong></div>
                <div class="copilot-metric"><span>Producción en riesgo</span><strong>${op.production_units_at_risk || 0} unidades</strong></div>
                <div class="copilot-metric"><span>Pérdida potencial</span><strong>${money(fin.potential_loss, fin.currency)}</strong></div>
                <div class="copilot-metric"><span>Pérdida evitable</span><strong>${money(fin.avoidable_loss, fin.currency)}</strong></div>
                <div class="copilot-metric"><span>ROI estimado</span><strong>${fin.roi_multiple || 0}x</strong></div>
            </div>
            <details class="copilot-details"><summary>Factores de la predicción</summary>${factors}</details>
            <details class="copilot-details"><summary>Fuentes consultadas</summary><ul>${sources}</ul></details>
            <div class="copilot-response-actions">${actions}</div>
            <p class="copilot-disclaimer">${escapeHtml(data.disclaimer)}</p>`;
    }

    async function submitQuestion(rawQuestion) {
        const question = String(rawQuestion || "").trim();
        if (!question) return;
        appendMessage("user", `<p>${escapeHtml(question)}</p>`);
        if (byId("chat-input")) byId("chat-input").value = "";
        setAnalyzing(true);
        try {
            // AJUSTE: Enviar 'prompt' para compatibilidad completa con el backend
            const response = await fetch("/api/copilot/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    prompt: question,
                    question: question,
                    profile: byId("user-profile")?.value || "operations",
                    machine_id: byId("copilot-machine")?.value || null,
                    conversation_id: conversationId
                })
            });
            if (!response.ok) throw new Error((await response.json()).detail || "Error del copiloto");
            const data = await response.json();
            conversationId = data.conversation_id || conversationId;
            if (conversationId) localStorage.setItem("predictiveConversationId", conversationId);
            appendMessage("assistant", renderResponse(data));
            bindActionButtons();
        } catch (error) {
            appendMessage("assistant", `<strong>No fue posible completar el análisis.</strong><p>${escapeHtml(error.message)}</p>`);
        } finally {
            setAnalyzing(false);
            byId("chat-input")?.focus();
        }
    }

    function bindActionButtons() {
        document.querySelectorAll(".copilot-action:not([data-bound])").forEach(button => {
            button.dataset.bound = "true";
            button.addEventListener("click", async () => {
                if (button.dataset.action === "preview_work_order") {
                    const response = await fetch("/api/work-orders/preview", {
                        method: "POST", headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ machine_id: button.dataset.machine })
                    });
                    const draft = await response.json();
                    appendMessage("assistant", `<strong>Orden preparada: ${escapeHtml(draft.id)}</strong><p>${escapeHtml(draft.title)}</p><p>Estado: borrador · Prioridad: ${escapeHtml(draft.priority)} · Costo estimado: ${money(draft.estimated_cost, "USD")}</p>`);
                } else if (button.dataset.action === "compare_scenarios") {
                    submitQuestion("Compara intervenir hoy versus esperar tres días");
                } else {
                    submitQuestion("Explica por qué se generó esta predicción");
                }
            });
        });
    }

    function initialize() {
        byId("chat-form")?.addEventListener("submit", event => { event.preventDefault(); submitQuestion(byId("chat-input")?.value); });
        byId("user-profile")?.addEventListener("change", renderQuickActions);
        renderQuickActions();
        refreshMachines().catch(console.error);
        appendMessage("assistant", "<strong>Predictive Copilot listo para ayudarte.</strong>");
        window.setInterval(() => refreshMachines().catch(console.error), 15000);
    }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize); else initialize();
})();