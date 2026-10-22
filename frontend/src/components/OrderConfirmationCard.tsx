import { useState } from 'react'
import { confirmOrder } from '../api'
import { formatRupees, formatTime } from '../format'
import type { ButtonResult, OrderConfirmationCard as OrderConfirmationData } from '../types'
import { DeliveryDetails } from './DeliveryDetails'

interface Props {
  card: OrderConfirmationData
  customerId: string
  onResult: (result: ButtonResult) => void
  onError: (message: string) => void
}

export function OrderConfirmationCard({ card, customerId, onResult, onError }: Props) {
  const [tapped, setTapped] = useState<'plain' | 'save' | null>(null)
  const { summary } = card

  async function confirm(saveAddress: boolean) {
    if (tapped) return
    setTapped(saveAddress ? 'save' : 'plain')
    try {
      onResult(await confirmOrder(customerId, card.pending_id, saveAddress))
    } catch {
      setTapped(null)
      onError('Could not confirm the order. Please try again.')
    }
  }

  return (
    <div className="card">
      <div className="card-title">Order summary</div>
      <ul className="line-list">
        {summary.items.map((item) => (
          <li key={item.name} className="line">
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
        <span>Total</span>
        <span className="price">{formatRupees(summary.cart_total)}</span>
      </div>
      <DeliveryDetails delivery={summary.delivery} />
      <div className="payment">Payment: {summary.payment}</div>
      <div className="buttons">
        <button type="button" className="primary" disabled={tapped !== null} onClick={() => confirm(false)}>
          {tapped === 'plain' ? 'Confirming…' : 'Confirm order'}
        </button>
        {card.show_save_address && (
          <button type="button" disabled={tapped !== null} onClick={() => confirm(true)}>
            {tapped === 'save' ? 'Confirming…' : 'Confirm and save address'}
          </button>
        )}
      </div>
      <div className="expiry">Valid until {formatTime(card.expires_at)}</div>
    </div>
  )
}
