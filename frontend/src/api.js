// Tiny API client for the FastAPI backend.
// In dev, Vite proxies /api → http://127.0.0.1:8000 (see vite.config.js).
// In production, set VITE_API_BASE in your environment.

const BASE = import.meta.env.VITE_API_BASE || '/api';

async function jsonRequest(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

export function chat(message, sessionId) {
  return jsonRequest('/chat', {
    method: 'POST',
    body: JSON.stringify({ message, session_id: sessionId }),
  });
}

export function cartAdd(sessionId, productId, quantity = 1, size = null) {
  return jsonRequest('/cart/add', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, product_id: productId, quantity, size }),
  });
}

export function cartRemove(sessionId, productId) {
  return jsonRequest('/cart/remove', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, product_id: productId }),
  });
}

export function viewCart(sessionId) {
  return jsonRequest(`/cart?session_id=${encodeURIComponent(sessionId)}`);
}

export function listProducts(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return jsonRequest(`/products${qs ? '?' + qs : ''}`);
}

export function health() {
  return jsonRequest('/health');
}
