import type { Delivery } from '../types'

export function DeliveryDetails({ delivery }: { delivery: Delivery }) {
  return (
    <div className="delivery">
      <div className="card-subtitle">Deliver to</div>
      <div>
        {delivery.name}, {delivery.phone}
      </div>
      <div>{delivery.address_line}</div>
      <div>
        {delivery.city}, {delivery.state} {delivery.pincode}
      </div>
    </div>
  )
}
