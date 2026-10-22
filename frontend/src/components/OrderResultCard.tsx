import { formatRupees } from '../format'
import type { OrderResultCard as OrderResultData } from '../types'
import { DeliveryDetails } from './DeliveryDetails'
import { CheckIcon, XIcon } from './Icons'

export function OrderResultCard({ card }: { card: OrderResultData }) {
  const placed = card.status === 'placed'
  return (
    <div className={placed ? 'card result ok' : 'card result cancelled'}>
      <div className="result-hero">
        <div className="result-icon">{placed ? <CheckIcon size={26} strokeWidth={2.4} /> : <XIcon size={24} strokeWidth={2.4} />}</div>
        <div className="result-title">
          Order #{card.order_id} {placed ? 'placed' : 'cancelled'}
        </div>
        <div className="result-text">
          {placed
            ? `Please keep ${formatRupees(card.total)} ready in cash when it arrives.`
            : 'Your order has been cancelled.'}
        </div>
      </div>
      <ul className="line-list">
        {card.items.map((item) => (
          <li key={item.product_id} className="line">
            <div className="line-info">
              <div className="line-name">{item.name}</div>
              <div className="line-sub">
                {item.quantity} × {formatRupees(item.unit_price)}
              </div>
            </div>
            <div className="line-total">{formatRupees(item.line_total)}</div>
          </li>
        ))}
      </ul>
      <div className="total-row">
        <span>{placed ? 'Pay on delivery' : 'Total'}</span>
        <span className="total-amount">{formatRupees(card.total)}</span>
      </div>
      {placed && (
        <div className="info-block">
          <DeliveryDetails delivery={card.delivery} />
        </div>
      )}
    </div>
  )
}
