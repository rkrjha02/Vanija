import { formatRupees, problemText } from '../format'
import type { CartCard as CartCardData } from '../types'

export function CartCard({ card }: { card: CartCardData }) {
  return (
    <div className="card">
      <div className="card-title">Your cart</div>
      <ul className="line-list">
        {card.items.map((item) => (
          <li key={item.product_id} className={item.problem ? 'line has-problem' : 'line'}>
            <div className="line-main">
              <span>{item.name}</span>
              <span className="price">{formatRupees(item.line_total)}</span>
            </div>
            <div className="line-sub">
              {item.quantity} × {formatRupees(item.unit_price)}
              {item.problem && <span className="badge bad">{problemText(item.problem, item.units_left)}</span>}
            </div>
          </li>
        ))}
      </ul>
      <div className="total-row">
        <span>Total</span>
        <span className="price">{formatRupees(card.cart_total)}</span>
      </div>
      {card.has_problems && (
        <p className="notice bad">Some items need attention before you can order.</p>
      )}
    </div>
  )
}
