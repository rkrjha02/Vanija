import { formatRupees, problemText } from '../format'
import type { CartCard as CartCardData } from '../types'
import { AlertIcon, BoxIcon, CartIcon } from './Icons'

interface Props {
  card: CartCardData
  busy: boolean
  onSendMessage: (text: string) => void
}

export function CartCard({ card, busy, onSendMessage }: Props) {
  const units = card.items.reduce((sum, item) => sum + item.quantity, 0)
  return (
    <div className="card">
      <div className="card-head">
        <div className="card-head-icon">
          <CartIcon size={18} />
        </div>
        <div>
          <div className="card-title">Your cart</div>
          <div className="card-meta">
            {units} {units === 1 ? 'item' : 'items'}
          </div>
        </div>
      </div>
      <ul className="line-list">
        {card.items.map((item) => (
          <li key={item.product_id} className={item.problem ? 'line has-problem' : 'line'}>
            <div className="line-thumb">
              <BoxIcon size={18} />
            </div>
            <div className="line-info">
              <div className="line-name">{item.name}</div>
              <div className="line-sub">
                {item.quantity} × {formatRupees(item.unit_price)}
              </div>
              {item.problem && <span className="badge bad">{problemText(item.problem, item.units_left)}</span>}
            </div>
            <div className="line-total">{formatRupees(item.line_total)}</div>
          </li>
        ))}
      </ul>
      <div className="total-row">
        <span>Total</span>
        <span className="total-amount">{formatRupees(card.cart_total)}</span>
      </div>
      {card.has_problems ? (
        <div className="notice bad">
          <AlertIcon size={16} />
          <span>Some items need attention before you can order.</span>
        </div>
      ) : (
        <button
          type="button"
          className="btn btn-accent btn-block card-cta"
          disabled={busy}
          onClick={() => onSendMessage('Place my order')}
        >
          Place order · Cash on Delivery
        </button>
      )}
    </div>
  )
}
