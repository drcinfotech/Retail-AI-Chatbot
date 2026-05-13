// Renders each of the rich-message block types the backend can return:
//   type=text     →  TextBlock
//   type=products →  ProductsBlock
//   type=cart     →  CartBlock
//   type=order    →  OrderBlock
//   type=promo    →  PromoBlock

import {
  Star, ShoppingCart, Plus, Trash2, CircleDot, Tag, Truck, CheckCircle2,
} from 'lucide-react';

const ACCENT = '#FF6B9D';

// ────────────────────────────────────────────────────
function Card({ children, className = '' }) {
  return (
    <div
      className={`rounded-2xl p-4 border ${className}`}
      style={{
        background: 'linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.015))',
        borderColor: 'rgba(255,255,255,0.08)',
      }}
    >
      {children}
    </div>
  );
}

function TinyChip({ children }) {
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-10 font-medium"
      style={{ background: ACCENT + '22', color: ACCENT }}
    >
      {children}
    </span>
  );
}

// ── TextBlock — markdown-lite (just **bold**) ────────
export function TextBlock({ content }) {
  // Split on **bold** markers
  const parts = content.split(/(\*\*[^*]+\*\*)/g);
  return (
    <div
      className="px-4 py-2.5 rounded-2xl text-sm leading-relaxed"
      style={{
        background: 'rgba(255,255,255,0.03)',
        color: 'rgba(255,255,255,0.85)',
        borderTopLeftRadius: '0.375rem',
      }}
    >
      {parts.map((part, i) =>
        part.startsWith('**') && part.endsWith('**') ? (
          <strong key={i} className="text-white font-medium">{part.slice(2, -2)}</strong>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </div>
  );
}

// ── ProductsBlock ────────────────────────────────────
export function ProductsBlock({ items, onAdd }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-2">
      {items.map((p) => (
        <div
          key={p.id}
          className="rounded-xl p-3 border hover-scale-102 flex flex-col"
          style={{ background: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.08)' }}
        >
          <div
            className="h-24 rounded-lg flex items-center justify-center text-5xl mb-2"
            style={{ background: ACCENT + '14' }}
          >
            {p.image}
          </div>
          <div className="flex items-center gap-1 mb-0.5">
            <Star size={9} fill={ACCENT} stroke="none" />
            <span className="text-10 text-white/60">{p.rating} · {p.reviews.toLocaleString()}</span>
          </div>
          <div className="text-xs text-white/90 font-medium truncate" title={p.name}>{p.name}</div>
          <div className="text-11 text-white/40 mb-1">{p.brand}</div>
          <div className="flex items-center justify-between mt-auto pt-2">
            <span className="text-sm font-semibold text-white">
              ₹{p.price.toLocaleString('en-IN')}
            </span>
            <button
              onClick={() => onAdd?.(p)}
              className="w-7 h-7 rounded-full flex items-center justify-center transition-all hover:scale-110"
              style={{ background: ACCENT, color: '#0A0A0A' }}
              aria-label={`Add ${p.name} to cart`}
            >
              <Plus size={14} />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── CartBlock ────────────────────────────────────────
export function CartBlock({ items, subtotal, shipping, total, onRemove }) {
  if (!items.length) {
    return (
      <Card>
        <div className="text-center py-4">
          <ShoppingCart size={20} className="mx-auto mb-2 text-white/30" />
          <div className="text-xs text-white/50">Your cart is empty.</div>
        </div>
      </Card>
    );
  }
  return (
    <Card>
      <div className="text-10 uppercase tracking-tighter2 text-white/40 mb-3">
        Your Cart · {items.length} item{items.length !== 1 ? 's' : ''}
      </div>
      <div className="space-y-2 mb-3">
        {items.map((it) => (
          <div key={it.product_id + (it.size || '')} className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center text-xl flex-shrink-0"
              style={{ background: ACCENT + '14' }}
            >
              {it.image}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs text-white/90 font-medium truncate">{it.name}</div>
              <div className="text-10 text-white/40">
                {it.brand} · qty {it.quantity}{it.size ? ` · ${it.size}` : ''}
              </div>
            </div>
            <div className="text-xs text-white/90 font-medium">
              ₹{(it.price * it.quantity).toLocaleString('en-IN')}
            </div>
            <button
              onClick={() => onRemove?.(it.product_id)}
              className="text-white/30 hover:text-white/70 transition-all"
              aria-label={`Remove ${it.name}`}
            >
              <Trash2 size={12} />
            </button>
          </div>
        ))}
      </div>
      <div className="pt-3 border-t space-y-1 text-11" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
        <div className="flex justify-between text-white/60">
          <span>Subtotal</span>
          <span>₹{subtotal.toLocaleString('en-IN')}</span>
        </div>
        <div className="flex justify-between text-white/60">
          <span>Shipping</span>
          <span>{shipping === 0 ? 'Free' : `₹${shipping}`}</span>
        </div>
        <div
          className="flex justify-between pt-1.5 mt-1.5 border-t text-sm text-white font-semibold"
          style={{ borderColor: 'rgba(255,255,255,0.06)' }}
        >
          <span>Total</span>
          <span>₹{total.toLocaleString('en-IN')}</span>
        </div>
      </div>
    </Card>
  );
}

// ── OrderBlock — tracking timeline ────────────────────
export function OrderBlock({ order }) {
  return (
    <Card>
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-10 text-white/40 uppercase tracking-wider">
            Tracking · {order.order_id}
          </div>
          <div className="text-sm text-white font-medium mt-0.5">
            Arriving {order.eta}
          </div>
        </div>
        <TinyChip>
          <CircleDot size={9} /> {order.status}
        </TinyChip>
      </div>
      <div className="relative pl-5 space-y-3 mt-3">
        <div
          className="absolute left-1.5 top-1 bottom-1 w-px"
          style={{ background: 'rgba(255,255,255,0.08)' }}
        />
        {order.events.map((e, i) => (
          <div key={i} className="relative">
            <div
              className="absolute neg-left-18 top-1 w-3 h-3 rounded-full border-2 flex items-center justify-center"
              style={{
                background: e.done ? ACCENT : '#0A0A0A',
                borderColor: e.done ? ACCENT : 'rgba(255,255,255,0.2)',
              }}
            >
              {e.current && <div className="w-1 h-1 rounded-full bg-black" />}
            </div>
            <div className="text-xs text-white/90 font-medium">{e.label}</div>
            <div className="text-10 text-white/40 font-mono">{e.date}</div>
          </div>
        ))}
      </div>
      <div
        className="mt-3 pt-3 border-t flex items-center gap-2 text-10 text-white/50"
        style={{ borderColor: 'rgba(255,255,255,0.06)' }}
      >
        <Truck size={11} style={{ color: ACCENT }} />
        {order.items_count} item{order.items_count !== 1 ? 's' : ''} · Total ₹{order.total.toLocaleString('en-IN')}
      </div>
    </Card>
  );
}

// ── PromoBlock ───────────────────────────────────────
export function PromoBlock({ code, description, discount_pct }) {
  return (
    <div
      className="rounded-xl p-3 border flex items-center gap-3 hover-scale-101 cursor-pointer"
      style={{
        background: 'linear-gradient(135deg, ' + ACCENT + '22, ' + ACCENT + '08)',
        borderColor: ACCENT + '44',
      }}
    >
      <div
        className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
        style={{ background: ACCENT + '33' }}
      >
        <Tag size={16} style={{ color: ACCENT }} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-xs text-white font-medium font-mono">{code}</div>
        <div className="text-10 text-white/60">{description}</div>
      </div>
      {discount_pct > 0 && (
        <div
          className="text-xs font-semibold px-2 py-1 rounded-md"
          style={{ background: ACCENT, color: '#0A0A0A' }}
        >
          {discount_pct}% OFF
        </div>
      )}
    </div>
  );
}

// ── Generic block renderer ───────────────────────────
export function Block({ block, onAddProduct, onRemoveCartItem }) {
  switch (block.type) {
    case 'text':     return <TextBlock content={block.content} />;
    case 'products': return <ProductsBlock items={block.items} onAdd={onAddProduct} />;
    case 'cart':     return <CartBlock {...block} onRemove={onRemoveCartItem} />;
    case 'order':    return <OrderBlock order={block.order} />;
    case 'promo':    return <PromoBlock {...block} />;
    default:         return null;
  }
}

// ── "Typing" indicator dots ──────────────────────────
export function TypingDots() {
  return (
    <div className="flex items-center gap-1 px-4 py-3">
      {[0, 0.15, 0.3].map((delay, i) => (
        <div
          key={i}
          className="w-1.5 h-1.5 rounded-full bounce-dot"
          style={{ background: ACCENT, animationDelay: delay + 's' }}
        />
      ))}
    </div>
  );
}
