import { formatRupees } from '../format'
import type { OrderResultCard as OrderResultData } from '../types'
import { DeliveryDetails } from './DeliveryDetails'
import { CheckIcon, ChevronIcon, XIcon } from './Icons'

// Shown only after the backend confirms the order was placed or cancelled (this card comes from its response).
export function OrderResultCard({ card }: { card: OrderResultData }) {
  const placed = card.status === 'placed'
  const units = card.items.reduce((sum, item) => sum + item.quantity, 0)

  return (
    <div className={placed ? 'card txn-card result ok' : 'card txn-card result cancelled'}>
      <div className="result-hero">
        <div className="result-icon">
          {placed ? <CheckIcon size={28} strokeWidth={2.4} /> : <XIcon size={26} strokeWidth={2.4} />}
        </div>
        <div className="result-title">{placed ? 'Order Placed Successfully!' : 'Order Cancelled'}</div>
        <div className="result-text">
          {placed ? 'Your order has been placed successfully.' : 'Your order has been cancelled successfully.'}
        </div>
      </div>

      <dl className="result-facts">
        <div>
          <dt>Order ID</dt>
          <dd>#{card.order_id}</dd>
        </div>
        <div>
          <dt>{placed ? 'Pay on delivery' : 'Order amount'}</dt>
          <dd className="result-amount">{formatRupees(card.total)}</dd>
        </div>
        <div>
          <dt>{placed ? 'Payment' : 'Status'}</dt>
          <dd>{placed ? 'Cash on Delivery' : 'Cancelled'}</dd>
        </div>
      </dl>

      {placed && <p className="result-note">Please keep {formatRupees(card.total)} ready in cash when your order arrives.</p>}

      <details className="result-details">
        <summary>
          View order details
          <span className="result-details-meta">
            {units} {units === 1 ? 'item' : 'items'}
          </span>
          <ChevronIcon size={15} className="details-chevron" />
        </summary>
        <ul className="line-list">
          {card.items.map((item) => (
            <li key={item.product_id} className="line">
              <div className="line-info">
                <div className="line-name">{item.name}</div>
                <div className="line-sub">
                  Qty {item.quantity} × {formatRupees(item.unit_price)}
                </div>
              </div>
              <div className="line-total">{formatRupees(item.line_total)}</div>
            </li>
          ))}
        </ul>
        {placed && (
          <div className="info-block">
            <DeliveryDetails delivery={card.delivery} label="Delivering to" />
          </div>
        )}
      </details>
    </div>
  )
}
