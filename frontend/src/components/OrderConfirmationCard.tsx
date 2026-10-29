import { useState } from 'react'
import { confirmOrder } from '../api'
import { formatRupees, formatTime } from '../format'
import type { ButtonResult, OrderConfirmationCard as OrderConfirmationData } from '../types'
import { DeliveryDetails } from './DeliveryDetails'
import { AlertIcon, CashIcon, CheckIcon, ClockIcon, ReceiptIcon } from './Icons'

interface Props {
  card: OrderConfirmationData
  fromHistory?: boolean
  onResult: (result: ButtonResult) => void
  onError: (message: string) => void
}

const ERROR_TEXT = 'Could not confirm the order. Please try again.'

// What to show on this card once the backend has answered (the answer itself appears as a new message below).
function outcomeText(status: string): string {
  if (status === 'placed' || status === 'already_placed') return 'Order placed. See the confirmation below.'
  if (status === 'needs_reconfirm') return 'Something changed. Please review the updated summary below.'
  if (status === 'history') return 'This summary was already acted on.'
  return 'This summary can no longer be used. See the message below.'
}

export function OrderConfirmationCard({ card, fromHistory, onResult, onError }: Props) {
  const [tapped, setTapped] = useState<'plain' | 'save' | null>(null)
  const [outcome, setOutcome] = useState<string | null>(fromHistory ? 'history' : null)
  const [failed, setFailed] = useState(false)
  const [dismissed, setDismissed] = useState(false)
  const { summary } = card

  async function confirm(saveAddress: boolean) {
    if (tapped) return
    setTapped(saveAddress ? 'save' : 'plain')
    setFailed(false)
    try {
      const result = await confirmOrder(card.pending_id, saveAddress)
      setOutcome(result.status)
      onResult(result)
    } catch {
      setTapped(null)
      setFailed(true)
      onError(ERROR_TEXT)
    }
  }

  if (dismissed) {
    return (
      <div className="card txn-card collapsed">
        <span>Order not placed. Ask Vanija whenever you're ready.</span>
        <button type="button" className="link-button" onClick={() => setDismissed(false)}>
          Show summary
        </button>
      </div>
    )
  }

  const payment = summary.payment === 'Cash on Delivery' ? 'Cash on Delivery (COD)' : summary.payment

  return (
    <div className="card txn-card emphasis">
      <div className="card-head">
        <div className="card-head-icon">
          <ReceiptIcon size={18} />
        </div>
        <div>
          <div className="card-eyebrow">Review before placing</div>
          <div className="card-title lg">Confirm Your Order</div>
        </div>
      </div>

      <div className="section-label">Order items</div>
      <ul className="line-list">
        {summary.items.map((item) => (
          <li key={item.name} className="line">
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

      <div className="info-block">
        <DeliveryDetails delivery={summary.delivery} />
        <div className="info-row">
          <div className="info-icon">
            <CashIcon size={17} />
          </div>
          <div className="info-content">
            <div className="info-label">Payment Method</div>
            <div className="info-strong">{payment}</div>
            <div className="info-text">Pay in cash when your order arrives.</div>
          </div>
        </div>
      </div>

      <div className="total-row">
        <span>Total amount</span>
        <span className="total-amount">{formatRupees(summary.cart_total)}</span>
      </div>

      {outcome ? (
        <div className="outcome-note" role="status">
          <CheckIcon size={16} />
          <span>{outcomeText(outcome)}</span>
        </div>
      ) : (
        <>
          {failed && (
            <div className="notice bad" role="alert">
              <AlertIcon size={16} />
              <span>{ERROR_TEXT}</span>
            </div>
          )}
          <div className="card-actions">
            <button
              type="button"
              className="btn btn-accent btn-block btn-lg"
              disabled={tapped !== null}
              onClick={() => confirm(false)}
            >
              {tapped === 'plain' && <span className="spinner" />}
              {tapped === 'plain' ? 'Confirming…' : 'Confirm Order'}
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
            <button
              type="button"
              className="btn btn-ghost btn-block"
              disabled={tapped !== null}
              onClick={() => setDismissed(true)}
            >
              Not now
            </button>
          </div>
          <div className="expiry">
            <ClockIcon size={14} />
            Valid until {formatTime(card.expires_at)}
          </div>
        </>
      )}
    </div>
  )
}
