const PORT = 8765;
let ws;

function connect() {
    ws = new WebSocket(`ws://localhost:${PORT}/ws`);

    ws.onopen = () => {
        document.getElementById('status-text').textContent = 'Connected';
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'status') {
            updateStatus(data.monitoring, data.processing);
        } else if (data.type === 'processing') {
            showSpinner();
        } else if (data.type === 'result') {
            showResult(data);
        }
    };

    ws.onclose = () => {
        document.getElementById('status-text').textContent = 'Reconnecting...';
        document.getElementById('status-indicator').className = 'indicator off';
        setTimeout(connect, 3000);
    };

    ws.onerror = () => ws.close();
}

function updateStatus(monitoring, processing) {
    const indicator = document.getElementById('status-indicator');
    indicator.className = 'indicator ' + (monitoring ? 'on' : 'off');
    document.getElementById('status-text').textContent = monitoring ? 'Monitoring ON' : 'Monitoring OFF';
    if (!processing) hideSpinner();
}

function showSpinner() {
    document.getElementById('spinner').style.display = 'block';
    document.getElementById('result').style.display = 'none';
}

function hideSpinner() {
    document.getElementById('spinner').style.display = 'none';
}

function showResult(data) {
    hideSpinner();
    document.getElementById('question-text').textContent = data.question || '';
    document.getElementById('answer-text').textContent = data.answer || '';

    const explanationEl = document.getElementById('explanation-text');
    explanationEl.innerHTML = formatExplanation(data.explanation || '');
    Prism.highlightAllUnder(explanationEl);

    const ts = data.timestamp ? new Date(data.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
    document.getElementById('timestamp').textContent = 'Last updated: ' + ts;
    document.getElementById('result').style.display = 'block';
}

function formatExplanation(text) {
    return text
        .replace(/```sas\n?([\s\S]*?)```/g, '<pre><code class="language-sas">$1</code></pre>')
        .replace(/```\n?([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
}

connect();
