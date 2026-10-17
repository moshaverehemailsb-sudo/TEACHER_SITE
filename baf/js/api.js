/* API client: one base URL, timeout, Persian error messages, bearer token storage. */
const API_BASE = ['5500', '5501'].includes(location.port) ? 'http://127.0.0.1:8000/api/v1' : '/api/v1';
const API_TIMEOUT = 12000;
const TOKEN_KEY = 'baf_token';

let authToken = null;
try { authToken = localStorage.getItem(TOKEN_KEY) } catch (e) { }
function setToken(t) { authToken = t || null; try { if (t) localStorage.setItem(TOKEN_KEY, t); else localStorage.removeItem(TOKEN_KEY) } catch (e) { } }
const loggedIn = () => !!authToken;

class ApiError extends Error { constructor(status, code, message) { super(message); this.status = status; this.code = code } }
class ApiAbort extends Error { }

async function api(path, opt = {}) {
    const { method = 'GET', params, body, auth = false, signal } = opt;
    const url = new URL(API_BASE + path, location.href);
    if (params) for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v);
    const ctrl = new AbortController(); let timedOut = false;
    const timer = setTimeout(() => { timedOut = true; ctrl.abort() }, API_TIMEOUT);
    if (signal) { if (signal.aborted) ctrl.abort(); else signal.addEventListener('abort', () => ctrl.abort(), { once: true }) }
    const headers = {};
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (auth && authToken) headers.Authorization = 'Bearer ' + authToken;
    let res;
    try { res = await fetch(url, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined, signal: ctrl.signal }) }
    catch (e) {
        clearTimeout(timer);
        if (timedOut) throw new ApiError(0, 'TIMEOUT', 'پاسخ سرور دیر شد؛ دوباره تلاش کن.');
        if (signal && signal.aborted) throw new ApiAbort();
        throw new ApiError(0, 'NETWORK', 'اتصال به سرور برقرار نشد؛ اینترنتت را بررسی کن.');
    }
    clearTimeout(timer);
    let data = null;
    try { data = await res.json() } catch (e) { }
    if (!res.ok) {
        const err = data && data.error;
        if (res.status === 401 && auth) { setToken(null); onAuthChange() }
        throw new ApiError(res.status, (err && err.code) || 'HTTP_ERROR', (err && err.message) || 'خطایی رخ داد؛ دوباره تلاش کن.');
    }
    return data;
}

const API = {
    subjects: () => api('/subjects'),
    teachers: (params, signal) => api('/teachers', { params, signal }),
    teacher: id => api('/teachers/' + id),
    reviews: (id, page) => api('/teachers/' + id + '/reviews', { params: { page, pageSize: 10 } }),
    rivals: id => api('/teachers/' + id + '/rivals', { params: { limit: 10 } }),
    compare: (a, b) => api('/compare', { params: { a, b } }),
    popular: () => api('/popular-comparisons'),
    requestCode: phone => api('/auth/request-code', { method: 'POST', body: { phone } }),
    verifyCode: (phone, code) => api('/auth/verify-code', { method: 'POST', body: { phone, code } }),
    me: () => api('/auth/me', { auth: true }),
    postReview: (id, body) => api('/teachers/' + id + '/reviews', { method: 'POST', body, auth: true })
};