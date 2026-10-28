import { useState } from 'react'
import { confirmCancel } from '../api'
import { formatRupees } from '../format'
import type { ButtonResult, CancelConfirmationCard as CancelConfirmationData } from '../types'
import { AlertIcon } from './Icons'

interface Props {
  card: CancelConfirmationData
  onResult: (result: ButtonResult) => void
  onError: (message: string) => void
}

export function CancelConfirmationCard({ card, onResult, onError }: Props) {
  const [tapped, setTapped] = useState(false)

  async function cancel() {
    if (tapped) return
    setTapped(true)
    try {
      onResult(await confirmCancel(card.order_id))
    } catch {
      setTapped(false)
      onError('Could not cancel the order. Please try again.')
    }
  }

  return (
    <div className="card">
      <div className="card-head">
        <div className="card-head-icon bad">
          <AlertIcon size={18} />
        </div>
        <div>
          <div className="card-title">Cancel order #{card.order_id}?</div>
          <div className="card-meta">A cancelled order cannot be restored.</div>
        </div>
      </div>
      <ul className="line-list">
        {card.items.map((item) => (
          <li key={item.name} className="line">
            <div className="line-info">
              <div className="line-name">{item.name}</div>
            </div>
            <div className="line-qty">× {item.quantity}</div>
          </li>
        ))}
      </ul>
      <div className="total-row">
        <span>Total</span>
        <span className="total-amount">{formatRupees(card.total)}</span>
      </div>
      <div className="card-actions">
        <button type="button" className="btn btn-danger btn-block" disabled={tapped} onClick={cancel}>
          {tapped && <span className="spinner" />}
          {tapped ? 'Cancelling…' : 'Yes, cancel order'}
        </button>
      </div>
    </div>
  )
}
