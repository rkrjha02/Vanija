import { formatRupees, formatSpecs } from '../format'
import type { ProductsCard as ProductsCardData } from '../types'

export function ProductsCard({ card }: { card: ProductsCardData }) {
  return (
    <div className="card">
      <ul className="product-list">
        {card.items.map((item) =>
          item.status === 'not_found' ? (
            <li key={item.id} className="product muted">
              {item.id}: not available
            </li>
          ) : (
            <li key={item.id} className="product">
              <div className="product-head">
                <span className="product-name">
                  {item.position !== undefined && <span className="position">{item.position}.</span>}
                  {item.name}
                </span>
                <span className="price">{formatRupees(item.price ?? 0)}</span>
              </div>
              <div className="product-meta">
                {item.brand && <span>{item.brand}</span>}
                {item.in_stock ? (
                  item.units_left !== undefined && item.units_left <= 5 ? (
                    <span className="badge warn">Only {item.units_left} left</span>
                  ) : (
                    <span className="badge ok">In stock</span>
                  )
                ) : (
                  <span className="badge bad">Out of stock</span>
                )}
              </div>
              {formatSpecs(item.key_specs ?? item.specs).length > 0 && (
                <div className="specs">{formatSpecs(item.key_specs ?? item.specs).join(' · ')}</div>
              )}
              {item.description && <p className="description">{item.description}</p>}
            </li>
          ),
        )}
      </ul>
    </div>
  )
}
