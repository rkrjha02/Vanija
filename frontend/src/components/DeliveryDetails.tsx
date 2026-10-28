import type { Delivery } from '../types'
import { PinIcon } from './Icons'

export function DeliveryDetails({ delivery, label = 'Delivery Address' }: { delivery: Delivery; label?: string }) {
  return (
    <div className="info-row">
      <div className="info-icon">
        <PinIcon size={17} />
      </div>
      <div className="info-content">
        <div className="info-label">{label}</div>
        <div className="info-strong">
          {delivery.name} · {delivery.phone}
        </div>
        <div className="info-text">{delivery.address_line}</div>
        <div className="info-text">
          {delivery.city}, {delivery.state} {delivery.pincode}
        </div>
      </div>
    </div>
  )
}
