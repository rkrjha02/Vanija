import { formatRupees, problemText } from '../format'
import type { CartCard as CartCardData } from '../types'
import { AlertIcon, CartIcon, ChevronIcon } from './Icons'

interface Props {
  card: CartCardData
  busy: boolean
  onSendMessage: (text: string) => void
}

export function CartCard({ card, busy, onSendMessage }: Props) {
  if (card.items.length === 0) {
    return (
      <div className="card txn-card cart-empty">
        <div className="empty-icon">
          <CartIcon size={22} />
        </div>
        <div className="card-title">Your cart is empty.</div>
        <p className="card-meta">Ask Vanija to find a phone, laptop or headphones, then tap Add to Cart.</p>
      </div>
    )
  }

  const units = card.items.reduce((sum, item) => sum + item.quantity, 0)
  return (
    <div className="card txn-card">
      <div className="card-head">
        <div className="card-head-icon">
          <CartIcon size={18} />
        </div>
        <div>
          <div className="card-title">Your Cart</div>
          <div className="card-meta">
            {units} {units === 1 ? 'item' : 'items'}
          </div>
        </div>
      </div>
      <ul className="line-list">
        {card.items.map((item) => (
          <li key={item.product_id} className={item.problem ? 'line has-problem' : 'line'}>
            <div className="line-info">
              <div className="line-name">{item.name}</div>
              <div className="line-sub">
                Qty {item.quantity} × {formatRupees(item.unit_price)}
              </div>
              {item.problem && <span className="badge bad">{problemText(item.problem, item.units_left)}</span>}
            </div>
            <div className="line-total">{formatRupees(item.line_total)}</div>
          </li>
        ))}
      </ul>
      <div className="summary-row">
        <span>Total items</span>
        <span>{units}</span>
      </div>
      <div className="total-row">
        <span>Cart total</span>
        <span className="total-amount">{formatRupees(card.cart_total)}</span>
      </div>
      {card.has_problems ? (
        <div className="notice bad" role="status">
          <AlertIcon size={16} />
          <span>Some items need attention before you can order. Ask Vanija to update your cart.</span>
        </div>
      ) : (
        <button
          type="button"
          className="btn btn-accent btn-block btn-lg card-cta"
          disabled={busy}
          onClick={() => onSendMessage('Place my order')}
        >
          Proceed to Order
          <ChevronIcon size={16} />
        </button>
      )}
    </div>
  )
}
