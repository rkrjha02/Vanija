import { formatRupees } from '../format'
import type { OrderResultCard as OrderResultData } from '../types'
import { DeliveryDetails } from './DeliveryDetails'

export function OrderResultCard({ card }: { card: OrderResultData }) {
  const placed = card.status === 'placed'
  return (
    <div className={placed ? 'card result ok' : 'card result cancelled'}>
      <div className="card-title">
        Order #{card.order_id} {placed ? 'placed' : 'cancelled'}
      </div>
      <ul className="line-list">
        {card.items.map((item) => (
          <li key={item.product_id} className="line">
            <div className="line-main">
              <span>{item.name}</span>
              <span className="price">{formatRupees(item.line_total)}</span>
            </div>
            <div className="line-sub">
              {item.quantity} × {formatRupees(item.unit_price)}
            </div>
          </li>
        ))}
      </ul>
      <div className="total-row">
        <span>{placed ? 'Pay on delivery' : 'Total'}</span>
        <span className="price">{formatRupees(card.total)}</span>
      </div>
      {placed && <DeliveryDetails delivery={card.delivery} />}
    </div>
  )
}
