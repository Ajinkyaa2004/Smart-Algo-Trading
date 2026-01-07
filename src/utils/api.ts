/**
 * API Client Utilities
 * Handles authenticated API requests with session token
 */

const API_BASE_URL = 'http://localhost:8000';

/**
 * Get session token from localStorage
 */
export const getSessionToken = (): string | null => {
    return localStorage.getItem('authToken');
};

/**
 * Create headers with session token
 */
export const getAuthHeaders = (): HeadersInit => {
    const token = getSessionToken();
    const headers: HeadersInit = {
        'Content-Type': 'application/json',
    };

    if (token) {
        headers['X-Session-Token'] = token;
    }

    return headers;
};

/**
 * Authenticated fetch wrapper
 */
export const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;

    const headers = {
        ...getAuthHeaders(),
        ...(options.headers || {}),
    };

    const response = await fetch(url, {
        ...options,
        headers,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
};

/**
 * API methods
 */
export const api = {
    // Auth
    getAuthStatus: () => {
        const token = getSessionToken();
        const url = token
            ? `${API_BASE_URL}/api/auth/status?token=${token}`
            : `${API_BASE_URL}/api/auth/status`;
        return fetch(url).then(r => r.json());
    },

    // Portfolio
    getPortfolio: () => apiFetch('/api/portfolio/holdings'),
    getPositions: () => apiFetch('/api/portfolio/positions'),
    getOrders: () => apiFetch('/api/portfolio/orders'),
    getMargins: () => apiFetch('/api/portfolio/margins'),

    // Paper Trading
    getPaperPortfolio: () => apiFetch('/api/paper-trading/portfolio'),
    getPaperTrades: () => apiFetch('/api/paper-trading/trades'),
    getPaperFunds: () => apiFetch('/api/paper-trading/funds'),
    getPaperStats: () => apiFetch('/api/paper-trading/stats'),
    resetPaperPortfolio: () => apiFetch('/api/paper-trading/reset', { method: 'POST' }),

    // Trading Bot
    getBotStatus: () => apiFetch('/api/bot/status'),
    startBot: (data: any) => apiFetch('/api/bot/start', {
        method: 'POST',
        body: JSON.stringify(data),
    }),
    stopBot: (data: any) => apiFetch('/api/bot/stop', {
        method: 'POST',
        body: JSON.stringify(data),
    }),

    // Market Data
    getLTP: (symbols: string[]) => apiFetch('/api/market/ltp', {
        method: 'POST',
        body: JSON.stringify({ symbols }),
    }),

    getHistoricalData: (params: any) => apiFetch('/api/market/historical', {
        method: 'POST',
        body: JSON.stringify(params),
    }),
};

export default api;
