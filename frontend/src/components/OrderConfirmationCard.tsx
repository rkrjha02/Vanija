import { useState } from 'react'
import { confirmOrder } from '../api'
import { formatRupees, formatTime } from '../format'
import type { ButtonResult, OrderConfirmationCard as OrderConfirmationData } from '../types'
import { DeliveryDetails } from './DeliveryDetails'
import { CashIcon, ClockIcon } from './Icons'

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
    <div className="card emphasis">
      <div className="card-head">
        <div>
          <div className="card-eyebrow">Almost done</div>
          <div className="card-title lg">Review your order</div>
        </div>
      </div>
      <ul className="line-list">
        {summary.items.map((item) => (
          <li key={item.name} className="line">
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
        <span>Total</span>
        <span className="total-amount">{formatRupees(summary.cart_total)}</span>
      </div>
      <div className="info-block">
        <DeliveryDetails delivery={summary.delivery} />
        <div className="info-row">
          <div className="info-icon">
            <CashIcon size={17} />
          </div>
          <div>
            <div className="info-label">Payment</div>
            <div className="info-strong">{summary.payment}</div>
          </div>
        </div>
      </div>
      <div className="card-actions">
        <button
          type="button"
          className="btn btn-accent btn-block"
          disabled={tapped !== null}
          onClick={() => confirm(false)}
        >
          {tapped === 'plain' && <span className="spinner" />}
          {tapped === 'plain' ? 'Confirming…' : 'Confirm order'}
        </button>
        {card.show_save_address && (
          <button
            type="button"
            className="btn btn-outline btn-block"
            disabled={tapped !== null}
            onClick={() => confirm(true)}
          >
            {tapped === 'save' && <span className="spinner" />}
            {tapped === 'save' ? 'Confirming…' : 'Confirm and save address'}
          </button>
        )}
      </div>
      <div className="expiry">
        <ClockIcon size={14} />
        Valid until {formatTime(card.expires_at)}
      </div>
    </div>
  )
}
