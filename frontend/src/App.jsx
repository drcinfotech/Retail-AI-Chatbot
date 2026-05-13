import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Send, Sparkles, CircleDot, Phone, MoreHorizontal, Zap, ShoppingBag,
  Check, AlertCircle, RefreshCw,
} from 'lucide-react';

import { chat, cartAdd, cartRemove, health } from './api';
import { Block, TypingDots } from './components/Blocks';

const ACCENT = '#FF6B9D';
const ACCENT_SOFT = '#FF6B9D14';

const INITIAL_MESSAGES = [
  {
    role: 'bot',
    blocks: [{
      type: 'text',
      content:
        "Hi, I'm Lume — your shopping assistant. I can help you find products, " +
        "track orders, manage your cart, or just talk through what you need. " +
        "What brings you in today?",
    }],
    suggestions: ['Find a gift for my sister', 'Track my order', 'Show trending items', 'Return an item'],
  },
];

export default function App() {
  const [sessionId,  setSessionId]  = useState(null);
  const [messages,   setMessages]   = useState(INITIAL_MESSAGES);
  const [draft,      setDraft]      = useState('');
  const [sending,    setSending]    = useState(false);
  const [cartCount,  setCartCount]  = useState(0);
  const [backendOK,  setBackendOK]  = useState(null);   // null = checking
  const [error,      setError]      = useState(null);

  const chatEndRef = useRef(null);

  // ── Health check on mount ──────────────────────────
  useEffect(() => {
    health()
      .then(() => setBackendOK(true))
      .catch(() => setBackendOK(false));
  }, []);

  // ── Auto-scroll to latest message ──────────────────
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, sending]);

  // ── Send a message to the backend ──────────────────
  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || sending) return;
    setError(null);
    setMessages((prev) => [...prev, {
      role: 'user',
      blocks: [{ type: 'text', content: text }],
    }]);
    setDraft('');
    setSending(true);

    try {
      const res = await chat(text, sessionId);
      if (!sessionId) setSessionId(res.session_id);
      setMessages((prev) => [...prev, {
        role: 'bot',
        blocks: res.blocks,
        suggestions: res.suggestions,
        intent: res.intent,
      }]);

      // Refresh cart count if any of the blocks is a cart
      const cartBlock = res.blocks.find((b) => b.type === 'cart');
      if (cartBlock) {
        setCartCount(cartBlock.items.reduce((sum, i) => sum + i.quantity, 0));
      }
    } catch (e) {
      console.error(e);
      setError(e.message || 'Something went wrong.');
      setMessages((prev) => [...prev, {
        role: 'bot',
        blocks: [{
          type: 'text',
          content: "Sorry — I couldn't reach the server. Make sure the Python backend is running on port 8000.",
        }],
      }]);
    } finally {
      setSending(false);
    }
  }, [sessionId, sending]);

  // ── Add product to cart (from product card +) ──────
  const handleAddProduct = useCallback(async (product) => {
    if (!sessionId) {
      // No session yet — start one via chat
      await sendMessage(`Add ${product.name} to my cart`);
      return;
    }
    try {
      const res = await cartAdd(sessionId, product.id);
      setCartCount(res.cart_size);
      // Inform user inline
      setMessages((prev) => [...prev, {
        role: 'bot',
        blocks: [{
          type: 'text',
          content: `Added **${product.name}** to your cart. Subtotal is ₹${res.subtotal.toLocaleString('en-IN')}.`,
        }],
        suggestions: ['View my cart', 'Checkout', 'Keep shopping', 'Apply a coupon'],
      }]);
    } catch (e) {
      setError(e.message);
    }
  }, [sessionId, sendMessage]);

  // ── Remove from cart (from trash icon) ─────────────
  const handleRemoveCartItem = useCallback(async (productId) => {
    if (!sessionId) return;
    try {
      const res = await cartRemove(sessionId, productId);
      setCartCount(res.cart_size);
      await sendMessage('show my cart');
    } catch (e) {
      setError(e.message);
    }
  }, [sessionId, sendMessage]);

  // ── Render ─────────────────────────────────────────
  return (
    <div
      className="min-h-screen w-full"
      style={{
        background: 'radial-gradient(ellipse at top left, #15161B 0%, #0A0A0C 50%, #050506 100%)',
        color: 'rgba(255,255,255,0.9)',
      }}
    >
      <div className="fixed inset-0 pointer-events-none grain opacity-50" />

      <div className="relative max-w-1400 mx-auto px-6 py-8">
        {/* ── HEADER ───────────────────────────────── */}
        <header className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center border"
              style={{
                background: 'linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.01))',
                borderColor: 'rgba(255,255,255,0.08)',
              }}
            >
              <Sparkles size={16} style={{ color: ACCENT }} />
            </div>
            <div>
              <div className="text-xs uppercase tracking-tighter3 text-white/40">
                Retail AI Chatbot
              </div>
              <div className="text-lg text-white font-serif">
                Lume<span style={{ color: ACCENT }}>.</span>
                <span className="text-white/40"> Your shopping companion.</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 text-11">
              {backendOK === null && <span className="text-white/40">Checking…</span>}
              {backendOK === true && (
                <>
                  <CircleDot size={8} style={{ color: '#4ADE80' }} className="animate-pulse" />
                  <span className="text-white/40">Backend online</span>
                </>
              )}
              {backendOK === false && (
                <>
                  <AlertCircle size={11} style={{ color: '#FB7185' }} />
                  <span className="text-white/60">Backend offline · start uvicorn</span>
                </>
              )}
            </div>
            <div className="relative">
              <ShoppingBag size={18} className="text-white/70" />
              {cartCount > 0 && (
                <div
                  className="absolute -top-1.5 -right-2 w-4 h-4 rounded-full text-9 font-semibold flex items-center justify-center"
                  style={{ background: ACCENT, color: '#0A0A0A' }}
                >
                  {cartCount}
                </div>
              )}
            </div>
          </div>
        </header>

        {/* ── MAIN GRID ────────────────────────────── */}
        <div className="grid-main">
          {/* CHAT WINDOW */}
          <div
            className="rounded-3xl border overflow-hidden flex flex-col chat-height"
            style={{
              background: 'linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.005))',
              borderColor: 'rgba(255,255,255,0.08)',
            }}
          >
            {/* Chat header */}
            <div
              className="px-5 py-4 border-b flex items-center justify-between"
              style={{ borderColor: 'rgba(255,255,255,0.06)' }}
            >
              <div className="flex items-center gap-3">
                <div className="relative">
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium border-2 font-serif"
                    style={{
                      background: 'linear-gradient(135deg, ' + ACCENT + '33, ' + ACCENT + '0A)',
                      borderColor: ACCENT + '44',
                      color: ACCENT,
                    }}
                  >
                    L
                  </div>
                  <div
                    className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 pulse-ring"
                    style={{ background: ACCENT, borderColor: '#0A0A0A' }}
                  />
                </div>
                <div>
                  <div className="text-sm text-white font-medium">Lume</div>
                  <div className="text-11 text-white/40">
                    {sending ? 'typing…' : 'AI shopping assistant'}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => window.location.reload()}
                  className="w-8 h-8 rounded-full flex items-center justify-center text-white/40 hover:text-white/80 hover:bg-white/5 transition-all"
                  title="Reset conversation"
                >
                  <RefreshCw size={13} />
                </button>
                <button className="w-8 h-8 rounded-full flex items-center justify-center text-white/40 hover:text-white/80 hover:bg-white/5 transition-all">
                  <Phone size={13} />
                </button>
                <button className="w-8 h-8 rounded-full flex items-center justify-center text-white/40 hover:text-white/80 hover:bg-white/5 transition-all">
                  <MoreHorizontal size={13} />
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-5 py-5 space-y-3 scrollbar">
              {messages.map((m, i) => {
                if (m.role === 'user') {
                  const text = m.blocks[0]?.content || '';
                  return (
                    <div key={i} className="flex justify-end msg-anim">
                      <div
                        className="max-w-80pct px-4 py-2.5 rounded-2xl text-sm"
                        style={{
                          background: 'rgba(255,255,255,0.06)',
                          color: 'rgba(255,255,255,0.95)',
                          borderBottomRightRadius: '0.375rem',
                        }}
                      >
                        {text}
                      </div>
                    </div>
                  );
                }
                return (
                  <div key={i} className="flex gap-2.5 msg-anim">
                    <div
                      className="w-7 h-7 rounded-full flex items-center justify-center text-11 font-medium flex-shrink-0 mt-0.5 border font-serif"
                      style={{
                        background: ACCENT + '14',
                        borderColor: ACCENT + '33',
                        color: ACCENT,
                      }}
                    >
                      L
                    </div>
                    <div className="max-w-85pct flex-1 space-y-2">
                      {m.blocks.map((block, j) => (
                        <Block
                          key={j}
                          block={block}
                          onAddProduct={handleAddProduct}
                          onRemoveCartItem={handleRemoveCartItem}
                        />
                      ))}
                    </div>
                  </div>
                );
              })}

              {sending && (
                <div className="flex gap-2.5 msg-anim">
                  <div
                    className="w-7 h-7 rounded-full flex items-center justify-center text-11 font-medium flex-shrink-0 mt-0.5 border font-serif"
                    style={{
                      background: ACCENT + '14',
                      borderColor: ACCENT + '33',
                      color: ACCENT,
                    }}
                  >
                    L
                  </div>
                  <div
                    className="rounded-2xl"
                    style={{
                      background: 'rgba(255,255,255,0.03)',
                      borderTopLeftRadius: '0.375rem',
                    }}
                  >
                    <TypingDots />
                  </div>
                </div>
              )}

              <div ref={chatEndRef} />
            </div>

            {/* Quick replies + input */}
            <div
              className="px-5 pt-3 pb-3 border-t"
              style={{ borderColor: 'rgba(255,255,255,0.06)' }}
            >
              <div className="flex gap-1.5 overflow-x-auto nav-scrollbar mb-3 -mx-1 px-1">
                {(messages[messages.length - 1]?.suggestions || []).map((q, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(q)}
                    disabled={sending}
                    className="text-11 px-3 py-1.5 rounded-full border whitespace-nowrap hover-scale-103 disabled:opacity-40"
                    style={{
                      background: 'rgba(255,255,255,0.02)',
                      borderColor: 'rgba(255,255,255,0.08)',
                      color: 'rgba(255,255,255,0.65)',
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage(draft)}
                  placeholder="Message Lume…"
                  disabled={sending}
                  className="flex-1 bg-transparent text-sm text-white placeholder-white/30 px-4 py-2.5 rounded-xl border focus:outline-none transition-all disabled:opacity-60"
                  style={{ borderColor: 'rgba(255,255,255,0.08)' }}
                />
                <button
                  onClick={() => sendMessage(draft)}
                  disabled={!draft.trim() || sending}
                  className="w-10 h-10 rounded-xl flex items-center justify-center transition-all hover:scale-105 disabled:opacity-30"
                  style={{ background: ACCENT, color: '#0A0A0A' }}
                  aria-label="Send"
                >
                  <Send size={14} />
                </button>
              </div>
              {error && (
                <div className="mt-2 text-10 flex items-center gap-1.5" style={{ color: '#FB7185' }}>
                  <AlertCircle size={11} />
                  {error}
                </div>
              )}
            </div>
          </div>

          {/* RIGHT SIDEBAR */}
          <aside className="space-y-4">
            {/* About card */}
            <div
              className="rounded-2xl border p-5 overflow-hidden relative"
              style={{
                background: 'linear-gradient(180deg, ' + ACCENT_SOFT + ', rgba(255,255,255,0.005))',
                borderColor: ACCENT + '22',
              }}
            >
              <div
                className="absolute -top-12 -right-12 w-32 h-32 rounded-full blur-3xl opacity-40"
                style={{ background: ACCENT }}
              />
              <div className="relative">
                <div className="flex items-center gap-2 mb-3">
                  <ShoppingBag size={14} style={{ color: ACCENT }} />
                  <div className="text-10 uppercase tracking-tighter2 text-white/40">
                    Retail · E-Commerce
                  </div>
                </div>
                <h2 className="text-4xl text-white leading-none font-serif">
                  Lume<span style={{ color: ACCENT }}>.</span>
                </h2>
                <p className="text-sm text-white/60 mt-2 italic font-serif">
                  A patient, curious shopping concierge.
                </p>
              </div>
            </div>

            {/* Capabilities */}
            <div
              className="rounded-2xl border p-5"
              style={{
                background: 'rgba(255,255,255,0.015)',
                borderColor: 'rgba(255,255,255,0.06)',
              }}
            >
              <div className="text-10 uppercase tracking-tighter2 text-white/40 mb-3">
                What I can do
              </div>
              <div className="space-y-2.5">
                {[
                  'Personalized product discovery from a 30-item catalog',
                  'Smart filtering by category, color, price, and tags',
                  'Cart management with real subtotal & shipping logic',
                  'Order tracking with timeline visualization',
                  'Discount codes, returns, sizing, and shipping Q&A',
                ].map((c, i) => (
                  <div key={i} className="flex items-start gap-2.5">
                    <div
                      className="w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                      style={{ background: ACCENT + '22' }}
                    >
                      <Check size={9} style={{ color: ACCENT }} />
                    </div>
                    <div className="text-xs text-white/75 leading-relaxed">{c}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Tech stack */}
            <div
              className="rounded-2xl border p-5"
              style={{
                background: 'rgba(255,255,255,0.015)',
                borderColor: 'rgba(255,255,255,0.06)',
              }}
            >
              <div className="text-10 uppercase tracking-tighter2 text-white/40 mb-3">
                Tech stack
              </div>
              <div className="flex flex-wrap gap-1.5">
                {['Python', 'FastAPI', 'Pydantic', 'React', 'Vite', 'Tailwind', 'lucide-react'].map((c, i) => (
                  <span
                    key={i}
                    className="text-10 px-2 py-1 rounded-md border font-mono"
                    style={{
                      background: 'rgba(255,255,255,0.02)',
                      borderColor: 'rgba(255,255,255,0.06)',
                      color: 'rgba(255,255,255,0.6)',
                    }}
                  >
                    {c}
                  </span>
                ))}
              </div>
              <div
                className="mt-4 pt-4 border-t flex items-center gap-2 text-10 text-white/50"
                style={{ borderColor: 'rgba(255,255,255,0.06)' }}
              >
                <Zap size={11} style={{ color: ACCENT }} />
                Rule-based NLU · zero-API-key
              </div>
            </div>

            {/* Try saying… */}
            <div
              className="rounded-2xl border p-5"
              style={{
                background: 'rgba(255,255,255,0.015)',
                borderColor: 'rgba(255,255,255,0.06)',
              }}
            >
              <div className="text-10 uppercase tracking-tighter2 text-white/40 mb-3">
                Try asking
              </div>
              <div className="space-y-1.5">
                {[
                  'Find me a gift under ₹5,000',
                  'Show wireless headphones',
                  'Add the first one to my cart',
                  'Track order TRK-8829145',
                  'Any coupons available?',
                ].map((s, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(s)}
                    disabled={sending}
                    className="block w-full text-left text-11 text-white/60 hover:text-white px-2 py-1.5 rounded-md hover:bg-white/5 transition-all disabled:opacity-50"
                  >
                    “{s}”
                  </button>
                ))}
              </div>
            </div>
          </aside>
        </div>

        <footer
          className="mt-10 pt-6 border-t flex items-center justify-between text-11 text-white/30"
          style={{ borderColor: 'rgba(255,255,255,0.05)' }}
        >
          <div>
            Frontend: React + Vite · Backend: Python + FastAPI
            {sessionId && (
              <span className="ml-3 font-mono text-white/20">session: {sessionId.slice(0, 8)}…</span>
            )}
          </div>
          <div className="italic font-serif">A full-stack AI demo.</div>
        </footer>
      </div>
    </div>
  );
}
