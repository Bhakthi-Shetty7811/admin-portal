// ============================================================
//  sky/api.js  — All backend API calls live here.
//  This file is loaded before admin.js so the functions
//  defined here are available throughout admin.js.
// ============================================================

const API_BASE = 'http://localhost:5000/api';

// ── Token helpers ────────────────────────────────────────────

function getToken() {
    return localStorage.getItem('sky_token') || sessionStorage.getItem('sky_token');
}

function saveToken(token, rememberMe) {
    if (rememberMe) {
        localStorage.setItem('sky_token', token);
    } else {
        sessionStorage.setItem('sky_token', token);
    }
}

function clearToken() {
    localStorage.removeItem('sky_token');
    sessionStorage.removeItem('sky_token');
}

function authHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`,
    };
}

// ── Generic fetch wrapper ────────────────────────────────────

async function apiFetch(path, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${path}`, options);
        const json = await response.json();
        return { ok: response.ok, status: response.status, data: json };
    } catch (err) {
        console.error('API error:', err);
        return { ok: false, status: 0, data: { error: 'Could not reach the server. Is Flask running?' } };
    }
}

// ── Auth API ─────────────────────────────────────────────────

async function apiSignup(fullName, email, password, confirmPassword) {
    return apiFetch('/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            full_name: fullName,
            email,
            password,
            confirm_password: confirmPassword,
        }),
    });
}

async function apiLogin(email, password, rememberMe) {
    return apiFetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, remember_me: rememberMe }),
    });
}

async function apiForgotPassword(email) {
    return apiFetch('/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
    });
}

// ── Opportunities API ────────────────────────────────────────

async function apiGetOpportunities() {
    return apiFetch('/opportunities', {
        method: 'GET',
        headers: authHeaders(),
    });
}

async function apiCreateOpportunity(payload) {
    return apiFetch('/opportunities', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(payload),
    });
}

async function apiUpdateOpportunity(id, payload) {
    return apiFetch(`/opportunities/${id}`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(payload),
    });
}

async function apiDeleteOpportunity(id) {
    return apiFetch(`/opportunities/${id}`, {
        method: 'DELETE',
        headers: authHeaders(),
    });
}