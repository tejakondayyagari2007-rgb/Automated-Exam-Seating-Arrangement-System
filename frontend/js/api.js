async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
    };

    const finalOptions = { ...defaultOptions, ...options };
    if (!finalOptions.headers) finalOptions.headers = {};
    if (finalOptions.body && typeof finalOptions.body !== 'string') {
        finalOptions.body = JSON.stringify(finalOptions.body);
    }

    const response = await fetch(url, finalOptions);
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(payload.message || 'Request failed.');
    }
    return payload;
}

function formatDate(dateValue) {
    if (!dateValue) return '—';
    const date = new Date(dateValue);
    return isNaN(date.getTime()) ? dateValue : date.toLocaleDateString();
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 2500);
}
