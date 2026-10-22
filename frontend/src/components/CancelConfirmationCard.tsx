import { useState } from 'react'
import { confirmCancel } from '../api'
import { formatRupees } from '../format'
import type { ButtonResult, CancelConfirmationCard as CancelConfirmationData } from '../types'

interface Props {
  card: CancelConfirmationData
  customerId: string
  onResult: (result: ButtonResult) => void
  onError: (message: string) => void
}

export function CancelConfirmationCard({ card, customerId, onResult, onError }: Props) {
  const [tapped, setTapped] = useState(false)

  async function cancel() {
    if (tapped) return
    setTapped(true)
    try {
      onResult(await confirmCancel(customerId, card.order_id))
    } catch {
      setTapped(false)
      onError('Could not cancel the order. Please try again.')
    }
  }

  return (
    <div className="card">
      <div className="card-title">Cancel order #{card.order_id}?</div>
      <ul className="line-list">
        {card.items.map((item) => (
          <li key={item.name} className="line">
            <div className="line-main">
              <span>{item.name}</span>
              <span>× {item.quantity}</span>
            </div>
          </li>
        ))}
      </ul>
      <div className="total-row">
        <span>Total</span>
        <span className="price">{formatRupees(card.total)}</span>
      </div>
      <div className="buttons">
        <button type="button" className="danger" disabled={tapped} onClick={cancel}>
          {tapped ? 'Cancelling…' : 'Yes, cancel order'}
        </button>
      </div>
    </div>
  )
}
