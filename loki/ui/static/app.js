const API_BASE = '';
let currentFile = null;

document.addEventListener('DOMContentLoaded', () => {
    refreshData();
    setupChat();
});

async function refreshData() {
    await loadFiles();
    await loadAllErrors();
}

async function loadFiles() {
    try {
        const response = await fetch(`${API_BASE}/api/files`);
        const data = await response.json();

        const tree = document.getElementById('file-tree');
        const files = data.files || [];

        document.getElementById('stat-files').textContent = files.length;

        tree.innerHTML = files.map(f => {
            const name = f.path.split('/').pop() || f.path.split('\\').pop() || f.path;
            const ext = name.split('.').pop() || '';
            const icon = getFileIcon(ext);

            return `
                <div class="file-item ${f.errors > 0 ? 'has-errors' : ''} ${currentFile === f.path ? 'active' : ''}"
                     onclick="loadContent('${f.path}', '${ext}')">
                    <span class="file-icon">${icon}</span>
                    <span class="file-name">${name}</span>
                    ${f.errors > 0 ? `<span class="file-errors">${f.errors}</span>` : ''}
                </div>
            `;
        }).join('');
    } catch (err) {
        console.error('Failed to load files:', err);
    }
}

function getFileIcon(ext) {
    const icons = {
        'py': '&#128013;',
        'js': '&#9997;',
        'ts': '&#128309;',
        'go': '&#128036;',
        'rs': '&#9881;',
    };
    return icons[ext] || '&#128196;';
}

function getLanguageClass(ext) {
    const langs = {
        'py': 'python',
        'js': 'javascript',
        'ts': 'typescript',
        'go': 'go',
        'rs': 'rust',
    };
    return langs[ext] || 'python';
}

async function loadContent(filePath, ext) {
    currentFile = filePath;
    document.getElementById('current-file').textContent = filePath;

    try {
        const response = await fetch(`${API_BASE}/api/content?file=${encodeURIComponent(filePath)}`);
        const data = await response.json();

        const codeElement = document.getElementById('code-content');
        const langClass = getLanguageClass(ext || filePath.split('.').pop());

        if (data.content) {
            codeElement.className = `language-${langClass}`;
            codeElement.textContent = data.content;

            Prism.highlightElement(codeElement);

            const lineCount = data.content.split('\n').length;
            document.getElementById('line-count').textContent = `${lineCount} lines`;
        } else {
            codeElement.textContent = data.error || 'File not found';
        }

        await loadFileErrors(filePath);
        await loadFiles();
    } catch (err) {
        console.error('Failed to load content:', err);
    }
}

async function loadAllErrors() {
    try {
        const response = await fetch(`${API_BASE}/api/errors`);
        const data = await response.json();
        const errors = data.errors || [];

        let errorCount = 0;
        let warningCount = 0;

        errors.forEach(e => {
            const sev = getSeverity(e);
            if (sev === 'error') errorCount++;
            else if (sev === 'warning') warningCount++;
        });

        document.getElementById('stat-errors').textContent = errorCount;
        document.getElementById('stat-warnings').textContent = warningCount;

        if (!currentFile) {
            displayErrors(errors);
        }
    } catch (err) {
        console.error('Failed to load errors:', err);
    }
}

async function loadFileErrors(filePath) {
    try {
        const response = await fetch(`${API_BASE}/api/errors?file=${encodeURIComponent(filePath)}`);
        const data = await response.json();
        displayErrors(data.errors || []);
    } catch (err) {
        console.error('Failed to load errors:', err);
    }
}

function getSeverity(error) {
    if (typeof error.severity === 'string') return error.severity;
    if (error.severity && error.severity.value) return error.severity.value;
    return 'unknown';
}

function getAttr(error, attr) {
    if (error[attr] !== undefined) return error[attr];
    return '';
}

function displayErrors(errors) {
    const list = document.getElementById('error-list');
    const countBadge = document.getElementById('error-count');

    countBadge.textContent = errors.length;

    if (errors.length === 0) {
        list.innerHTML = '<p class="empty-state">No errors detected</p>';
        return;
    }

    list.innerHTML = errors.map(e => {
        const severity = getSeverity(e);
        const file = getAttr(e, 'file');
        const line = getAttr(e, 'line');
        const message = getAttr(e, 'message');
        const source = getAttr(e, 'source');

        return `
            <div class="error-item ${severity}">
                <div class="error-header">
                    <span class="error-severity ${severity}">${severity}</span>
                    <span class="error-location">${file}:${line}</span>
                </div>
                <div class="error-message">${escapeHtml(String(message))}</div>
                ${source ? `<div class="error-source">Source: ${source}</div>` : ''}
            </div>
        `;
    }).join('');
}

function setupChat() {
    const input = document.getElementById('chat-input');

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChat();
        }
    });
}

async function sendChat() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message) return;

    appendMessage('user', message);
    input.value = '';

    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message }),
        });

        const data = await response.json();
        appendMessage('assistant', data.response || 'No response');
    } catch (err) {
        appendMessage('assistant', 'Error: Failed to get response');
    }
}

function appendMessage(role, content) {
    const messages = document.getElementById('chat-messages');

    const welcome = messages.querySelector('.chat-welcome');
    if (welcome) welcome.remove();

    const div = document.createElement('div');
    div.className = `chat-message ${role}`;
    div.innerHTML = `
        <div class="role">${role === 'user' ? 'You' : 'Loki'}</div>
        <div class="content">${escapeHtml(content)}</div>
    `;

    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}