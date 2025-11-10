/**
 * Cryptographic Performance Simulator - Professional Frontend
 * Clean WebSocket handling with proper error management
 */

const elements = {
    runButton: document.getElementById('run-benchmark'),
    modeClassical: document.getElementById('mode-classical'),
    modePQC: document.getElementById('mode-pqc'),
    modeHybrid: document.getElementById('mode-hybrid'),
    latencySlider: document.getElementById('latency-slider'),
    latencyValue: document.getElementById('latency-value'),
    packetLossSlider: document.getElementById('packet-loss-slider'),
    packetLossValue: document.getElementById('packet-loss-value'),
    progressSection: document.getElementById('progress-section'),
    progressBar: document.getElementById('progress-bar'),
    progressText: document.getElementById('progress-text'),
    progressPercent: document.getElementById('progress-percent'),
    statusLog: document.getElementById('status-log'),
    resultsSection: document.getElementById('results-section'),
    statClassical: document.getElementById('stat-classical'),
    statPQC: document.getElementById('stat-pqc'),
    statHybrid: document.getElementById('stat-hybrid'),
    statKeysize: document.getElementById('stat-keysize'),
    chartLatency: document.getElementById('chart-latency'),
    chartKeys: document.getElementById('chart-keys'),
    chartOverhead: document.getElementById('chart-overhead'),
};

let socket = null;
let charts = { latency: null, keys: null, overhead: null };
let currentBenchmark = { totalIterations: 0, completedIterations: 0, modes: [] };

function init() {
    updateSliderDisplay(elements.latencySlider, elements.latencyValue, ' ms');
    updateSliderDisplay(elements.packetLossSlider, elements.packetLossValue, '%');
    
    elements.latencySlider.addEventListener('input', (e) => {
        updateSliderDisplay(e.target, elements.latencyValue, ' ms');
    });
    
    elements.packetLossSlider.addEventListener('input', (e) => {
        updateSliderDisplay(e.target, elements.packetLossValue, '%');
    });
    
    elements.runButton.addEventListener('click', startBenchmark);
    
    console.log('✅ Simulator initialized');
}

function updateSliderDisplay(slider, display, suffix = '') {
    display.textContent = `${slider.value}${suffix}`;
}

async function startBenchmark() {
    const modes = [];
    if (elements.modeClassical.checked) modes.push('classical');
    if (elements.modePQC.checked) modes.push('pqc');
    if (elements.modeHybrid.checked) modes.push('hybrid');
    
    if (modes.length === 0) {
        alert('⚠️ Please select at least one benchmark mode');
        return;
    }
    
    const latency = parseFloat(elements.latencySlider.value);
    const packetLoss = parseFloat(elements.packetLossSlider.value);
    
    currentBenchmark = {
        totalIterations: modes.length * 50,
        completedIterations: 0,
        modes: modes,
    };
    
    disableControls();
    showProgressSection();
    hideResultsSection();
    resetProgress();
    log('🔧 Initializing benchmark...');
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/benchmark`;
    
    try {
        socket = new WebSocket(wsUrl);
        
        socket.onopen = () => {
            log('✅ Connected to server');
            log(`📊 Modes: ${modes.map(m => m.toUpperCase()).join(', ')}`);
            log(`⏱️ Latency: ${latency}ms | 📉 Loss: ${packetLoss}%`);
            
            socket.send(JSON.stringify({
                modes: modes,
                latency: latency,
                packetLoss: packetLoss,
            }));
            log('🚀 Benchmark started');
        };
        
        socket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            handleWebSocketMessage(message);
        };
        
        socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            handleError('Connection error. Please refresh and try again.');
        };
        
        socket.onclose = (event) => {
            if (event.code === 1000) {
                log('✅ Benchmark completed');
            }
            enableControls();
        };
        
    } catch (error) {
        console.error('Failed to connect:', error);
        handleError('Failed to connect to server');
        enableControls();
    }
}

function handleWebSocketMessage(message) {
    switch (message.type) {
        case 'progress':
            handleProgress(message);
            break;
        case 'result':
            handleResults(message.data);
            break;
        case 'error':
            handleError(message.message);
            break;
        default:
            console.warn('Unknown message type:', message.type);
    }
}

function handleProgress(message) {
    const { mode, iteration, total } = message;
    
    currentBenchmark.completedIterations++;
    const progress = (currentBenchmark.completedIterations / currentBenchmark.totalIterations) * 100;
    
    updateProgress(progress);
    elements.progressText.textContent = `${mode}: ${iteration}/${total}`;
    log(`▶️ ${mode} - ${iteration}/${total}`);
}

function updateProgress(percent) {
    percent = Math.min(Math.max(percent, 0), 100);
    elements.progressBar.style.width = `${percent}%`;
    elements.progressPercent.textContent = `${Math.round(percent)}%`;
}

function resetProgress() {
    updateProgress(0);
    elements.progressText.textContent = 'Initializing...';
    clearLog();
}

function handleResults(data) {
    console.log('📊 Results received:', data);
    
    log('✅ Benchmark completed successfully');
    
    setTimeout(() => {
        hideProgressSection();
        showResultsSection();
        updateStatCards(data);
        renderCharts(data);
        
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.close(1000, 'Benchmark completed');
        }
    }, 300);
}

function updateStatCards(data) {
    const times = data.handshake_time_ms;
    
    elements.statClassical.textContent = times.classical ? `${times.classical.toFixed(2)} ms` : '--';
    elements.statPQC.textContent = times.pqc ? `${times.pqc.toFixed(2)} ms` : '--';
    elements.statHybrid.textContent = times.hybrid ? `${times.hybrid.toFixed(2)} ms` : '--';
    elements.statKeysize.textContent = `${data.public_key_bytes.pqc.toLocaleString()}`;
}

function renderCharts(data) {
    Object.values(charts).forEach(chart => {
        if (chart) chart.destroy();
    });
    
    const colors = {
        classical: { bg: 'rgba(6, 182, 212, 0.8)', border: 'rgba(6, 182, 212, 1)' },
        pqc: { bg: 'rgba(20, 184, 166, 0.8)', border: 'rgba(20, 184, 166, 1)' },
        hybrid: { bg: 'rgba(16, 185, 129, 0.8)', border: 'rgba(16, 185, 129, 1)' },
    };
    
    const modes = data.settings.modes;
    const times = data.handshake_time_ms;
    const keyBytes = data.public_key_bytes;
    const sigBytes = data.signature_bytes;
    
    const latencyLabels = [];
    const latencyData = [];
    const latencyColors = [];
    const latencyBorderColors = [];
    
    if (modes.includes('classical') && times.classical !== undefined) {
        latencyLabels.push('Classical');
        latencyData.push(times.classical);
        latencyColors.push(colors.classical.bg);
        latencyBorderColors.push(colors.classical.border);
    }
    if (modes.includes('pqc') && times.pqc !== undefined) {
        latencyLabels.push('Post-Quantum');
        latencyData.push(times.pqc);
        latencyColors.push(colors.pqc.bg);
        latencyBorderColors.push(colors.pqc.border);
    }
    if (modes.includes('hybrid') && times.hybrid !== undefined) {
        latencyLabels.push('Hybrid');
        latencyData.push(times.hybrid);
        latencyColors.push(colors.hybrid.bg);
        latencyBorderColors.push(colors.hybrid.border);
    }
    
    charts.latency = new Chart(elements.chartLatency, {
        type: 'bar',
        data: {
            labels: latencyLabels,
            datasets: [{
                label: 'Time (ms)',
                data: latencyData,
                backgroundColor: latencyColors,
                borderColor: latencyBorderColors,
                borderWidth: 2,
                borderRadius: 8,
            }]
        },
        options: getChartOptions('ms')
    });
    
    charts.keys = new Chart(elements.chartKeys, {
        type: 'bar',
        data: {
            labels: ['Classical', 'PQC', 'Hybrid'],
            datasets: [{
                label: 'Size (bytes)',
                data: [keyBytes.classical, keyBytes.pqc, keyBytes.hybrid],
                backgroundColor: [colors.classical.bg, colors.pqc.bg, colors.hybrid.bg],
                borderColor: [colors.classical.border, colors.pqc.border, colors.hybrid.border],
                borderWidth: 2,
                borderRadius: 8,
            }]
        },
        options: getChartOptions('bytes')
    });
    
    charts.overhead = new Chart(elements.chartOverhead, {
        type: 'bar',
        data: {
            labels: ['Kyber768\nPublic Key', 'ML-DSA-65\nSignature'],
            datasets: [{
                label: 'Size (bytes)',
                data: [keyBytes.pqc, sigBytes.pqc],
                backgroundColor: [colors.pqc.bg, colors.hybrid.bg],
                borderColor: [colors.pqc.border, colors.hybrid.border],
                borderWidth: 2,
                borderRadius: 8,
            }]
        },
        options: getChartOptions('bytes')
    });
}

function getChartOptions(unit) {
    return {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: 'rgba(15, 23, 42, 0.95)',
                titleColor: '#06b6d4',
                bodyColor: '#e2e8f0',
                borderColor: '#06b6d4',
                borderWidth: 1,
                padding: 10,
                displayColors: false,
                callbacks: {
                    label: (context) => {
                        const value = context.parsed.y;
                        return unit === 'ms' 
                            ? `${value.toFixed(2)} ${unit}`
                            : `${value.toLocaleString()} ${unit}`;
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: { 
                    color: '#94a3b8',
                    font: { size: 11 }
                },
                grid: { 
                    color: 'rgba(148, 163, 184, 0.1)'
                }
            },
            x: {
                ticks: { 
                    color: '#94a3b8',
                    font: { size: 10 }
                },
                grid: { display: false }
            }
        }
    };
}

function handleError(message) {
    console.error('Error:', message);
    log(`❌ Error: ${message}`, 'error');
    
    setTimeout(() => {
        hideProgressSection();
        enableControls();
    }, 2000);
}

function disableControls() {
    elements.runButton.disabled = true;
    elements.modeClassical.disabled = true;
    elements.modePQC.disabled = true;
    elements.modeHybrid.disabled = true;
    elements.latencySlider.disabled = true;
    elements.packetLossSlider.disabled = true;
}

function enableControls() {
    elements.runButton.disabled = false;
    elements.modeClassical.disabled = false;
    elements.modePQC.disabled = false;
    elements.modeHybrid.disabled = false;
    elements.latencySlider.disabled = false;
    elements.packetLossSlider.disabled = false;
}

function showProgressSection() {
    elements.progressSection.classList.remove('hidden');
}

function hideProgressSection() {
    elements.progressSection.classList.add('hidden');
}

function showResultsSection() {
    elements.resultsSection.classList.remove('hidden');
    elements.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function hideResultsSection() {
    elements.resultsSection.classList.add('hidden');
}

function log(message, type = 'info') {
    const logEntry = document.createElement('div');
    logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logEntry.className = type === 'error' ? 'text-red-400' : 'text-cyan-400/80';
    elements.statusLog.appendChild(logEntry);
    elements.statusLog.scrollTop = elements.statusLog.scrollHeight;
}

function clearLog() {
    elements.statusLog.innerHTML = '<div class="text-slate-600">Ready to start...</div>';
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
