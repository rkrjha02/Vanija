import { useState } from 'react'
import { confirmCancel } from '../api'
import { formatRupees } from '../format'
import type { ButtonResult, CancelConfirmationCard as CancelConfirmationData } from '../types'
import { AlertIcon, CheckIcon } from './Icons'

interface Props {
  card: CancelConfirmationData
  fromHistory?: boolean
  onResult: (result: ButtonResult) => void
  onError: (message: string) => void
}

const ERROR_TEXT = 'Could not cancel the order. Please try again.'

export function CancelConfirmationCard({ card, fromHistory, onResult, onError }: Props) {
  const [tapped, setTapped] = useState(false)
  const [answered, setAnswered] = useState(fromHistory ?? false)
  const [failed, setFailed] = useState(false)
  const [kept, setKept] = useState(false)

  async function cancel() {
    if (tapped) return
    setTapped(true)
    setFailed(false)
    try {
      const result = await confirmCancel(card.order_id)
      setAnswered(true)
      onResult(result)
    } catch {
      setTapped(false)
      setFailed(true)
      onError(ERROR_TEXT)
    }
  }

  // "Keep order" changes nothing on the server; it only closes this card.
  if (kept) {
    return (
      <div className="card txn-card collapsed">
        <span>Order #{card.order_id} was not cancelled.</span>
        <button type="button" className="link-button" onClick={() => setKept(false)}>
          Undo
        </button>
      </div>
    )
  }

  return (
    <div className="card txn-card danger">
      <div className="card-head">
        <div className="card-head-icon bad">
          <AlertIcon size={18} />
        </div>
        <div>
          <div className="card-title lg">Cancel Order</div>
          <div className="card-meta">Order #{card.order_id}</div>
        </div>
      </div>

      <div className="section-label">Items in this order</div>
      <ul className="line-list">
        {card.items.map((item) => (
          <li key={item.name} className="line">
            <div className="line-info">
              <div className="line-name">{item.name}</div>
            </div>
            <div className="line-qty">Qty {item.quantity}</div>
          </li>
        ))}
      </ul>
      <div className="total-row">
        <span>Order amount</span>
        <span className="total-amount">{formatRupees(card.total)}</span>
      </div>

      {answered ? (
        <div className="outcome-note" role="status">
          <CheckIcon size={16} />
          <span>{fromHistory ? 'This cancellation was already acted on.' : 'Request sent. See the result below.'}</span>
        </div>
      ) : (
        <>
          <p className="confirm-prompt">
            Are you sure you want to cancel this order?
            <span>A cancelled order cannot be restored.</span>
          </p>
          {failed && (
            <div className="notice bad" role="alert">
              <AlertIcon size={16} />
              <span>{ERROR_TEXT}</span>
            </div>
          )}
          <div className="card-actions">
            <button type="button" className="btn btn-danger btn-block btn-lg" disabled={tapped} onClick={cancel}>
              {tapped && <span className="spinner" />}
              {tapped ? 'Cancelling…' : 'Confirm Cancellation'}
            </button>
            <button type="button" className="btn btn-outline btn-block" disabled={tapped} onClick={() => setKept(true)}>
              No, keep my order
            </button>
          </div>
        </>
      )}
    </div>
  )
}
