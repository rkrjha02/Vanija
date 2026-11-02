import { formatRupees } from '../format'
import type { OrderListCard as OrderListData } from '../types'

export function OrderListCard({ card }: { card: OrderListData }) {
  return (
    <div className="card txn-card">
      <div className="card-head">
        <div className="card-head-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M16 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V8Z" />
            <path d="M15 3v4a1 1 0 0 0 1 1h4" />
          </svg>
        </div>
        <div>
          <div className="card-eyebrow">Order history</div>
          <div className="card-title">{card.orders.length} {card.orders.length === 1 ? 'order' : 'orders'}</div>
        </div>
      </div>

      <div className="order-list">
        {card.orders.map((order) => (
          <div key={order.order_id} className="order-block">
            <div className="order-block-head">
              <span className="order-position">Order #{order.position}</span>
              <span className={order.status === 'placed' ? 'badge ok' : 'badge bad'}>
                {order.status === 'placed' ? 'Placed' : 'Cancelled'}
              </span>
            </div>
            <div className="order-date">{order.date}</div>
            <ul className="line-list">
              {order.items.map((item, idx) => (
                <li key={idx} className="line">
                  <div className="line-info">
                    <div className="line-name">{item.name}</div>
                    <div className="line-sub">
                      Qty {item.quantity} × {formatRupees(item.price)}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
            <div className="total-row">
              <span>Total</span>
              <span className="total-amount">{formatRupees(order.total)}</span>
            </div>
            <div className="order-address">{order.address}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
