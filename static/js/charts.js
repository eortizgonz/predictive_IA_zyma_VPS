const CHART_CONFIG = {
    displayModeBar: false,
    responsive: true,
    scrollZoom: false,
    staticPlot: false
};

async function loadCharts() {
    try {
        const response = await fetch('/api/history');
        if (!response.ok) throw new Error('No fue posible consultar el historial');
        const data = await response.json();
        drawCharts(data);
    } catch (error) {
        console.error('Error cargando tendencias:', error);
    }
}

function chartHeight(chartId) {
    const mobile = window.matchMedia('(max-width: 780px)').matches;
    if (chartId === 'risk-chart') return mobile ? 260 : 300;
    return mobile ? 235 : 260;
}

function chartLayout(chartId, yTitle) {
    return {
        autosize: true,
        height: chartHeight(chartId),
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#91a3bc', size: 10 },
        margin: { l: 48, r: 18, t: 12, b: 38 },
        xaxis: {
            title: 'Tiempo / min',
            gridcolor: 'rgba(145,163,188,.10)',
            zeroline: false,
            automargin: true
        },
        yaxis: {
            title: yTitle,
            gridcolor: 'rgba(145,163,188,.10)',
            zeroline: false,
            automargin: true
        },
        showlegend: false,
        hovermode: 'x unified'
    };
}

function trace(x, y, name) {
    return {
        x,
        y,
        type: 'scatter',
        mode: 'lines',
        name,
        line: { width: 3 },
        fill: 'tozeroy',
        fillcolor: 'rgba(59,130,246,.07)'
    };
}

function renderChart(chartId, x, y, name, yTitle) {
    const element = document.getElementById(chartId);
    if (!element || typeof Plotly === 'undefined') return;
    element.style.height = `${chartHeight(chartId)}px`;
    Plotly.react(
        element,
        [trace(x || [], y || [], name)],
        chartLayout(chartId, yTitle),
        CHART_CONFIG
    );
}

function drawCharts(data) {
    renderChart('temperature-chart', data.time, data.temperature, 'Temperatura', '°C');
    renderChart('vibration-chart', data.time, data.vibration, 'Vibración', 'mm/s');
    renderChart('risk-chart', data.time, data.risk, 'Riesgo', '%');
}

let resizeTimer;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(loadCharts, 180);
});

window.setInterval(loadCharts, 5000);
loadCharts();
