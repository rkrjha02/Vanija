import { formatRupees, formatSpecs } from '../format'
import type { ProductItem, ProductsCard as ProductsCardData } from '../types'
import { CartIcon, CategoryIcon } from './Icons'

interface Props {
  card: ProductsCardData
  busy: boolean
  onSendMessage: (text: string) => void
}

function StockBadge({ item }: { item: ProductItem }) {
  if (!item.in_stock) return <span className="badge bad">Out of stock</span>
  if (item.units_left !== undefined && item.units_left <= 5) {
    return <span className="badge warn">Only {item.units_left} left</span>
  }
  return <span className="badge ok">In stock</span>
}

function ProductTile({ item, busy, onSendMessage }: { item: ProductItem; busy: boolean; onSendMessage: Props['onSendMessage'] }) {
  const specs = formatSpecs(item.key_specs ?? item.specs).slice(0, 3)
  return (
    <li className={item.in_stock ? 'product-tile' : 'product-tile unavailable'}>
      <div className={`product-media cat-${item.category ?? 'other'}`}>
        {item.position !== undefined && <span className="position-tag">{item.position}</span>}
        <CategoryIcon category={item.category} size={44} strokeWidth={1.3} />
        <div className="media-badge">
          <StockBadge item={item} />
        </div>
      </div>
      <div className="product-body">
        {item.brand && <div className="product-brand">{item.brand}</div>}
        <div className="product-name" title={item.name}>
          {item.name}
        </div>
        {specs.length > 0 && (
          <ul className="spec-chips">
            {specs.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        )}
        <div className="product-price">{formatRupees(item.price ?? 0)}</div>
        <div className="product-actions">
          <button
            type="button"
            className="btn btn-ink btn-sm"
            disabled={busy || !item.in_stock}
            onClick={() => onSendMessage(`Add ${item.name} (${item.id}) to my cart`)}
          >
            <CartIcon size={15} />
            Add
          </button>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            disabled={busy}
            onClick={() => onSendMessage(`Tell me more about ${item.name} (${item.id})`)}
          >
            Details
          </button>
        </div>
      </div>
    </li>
  )
}

function ProductDetail({ item, busy, onSendMessage }: { item: ProductItem; busy: boolean; onSendMessage: Props['onSendMessage'] }) {
  const specs = formatSpecs(item.specs)
  return (
    <article className="card product-detail">
      <div className={`product-media detail cat-${item.category ?? 'other'}`}>
        <CategoryIcon category={item.category} size={64} strokeWidth={1.2} />
      </div>
      <div className="detail-body">
        {item.brand && <div className="product-brand">{item.brand}</div>}
        <h3 className="detail-name">{item.name}</h3>
        <div className="detail-price-row">
          <span className="product-price lg">{formatRupees(item.price ?? 0)}</span>
          <StockBadge item={item} />
        </div>
        {item.description && <p className="detail-description">{item.description}</p>}
        {specs.length > 0 && (
          <ul className="spec-chips">
            {specs.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        )}
        <button
          type="button"
          className="btn btn-ink"
          disabled={busy || !item.in_stock}
          onClick={() => onSendMessage(`Add ${item.name} (${item.id}) to my cart`)}
        >
          <CartIcon size={16} />
          {item.in_stock ? 'Add to cart' : 'Out of stock'}
        </button>
      </div>
    </article>
  )
}

export function ProductsCard({ card, busy, onSendMessage }: Props) {
  const found = card.items.filter((item) => item.status !== 'not_found')
  const missing = card.items.filter((item) => item.status === 'not_found')
  const isDetail = found.length > 0 && found.every((item) => item.specs !== undefined)

  return (
    <div className="products-card">
      {isDetail ? (
        found.map((item) => <ProductDetail key={item.id} item={item} busy={busy} onSendMessage={onSendMessage} />)
      ) : (
        <>
          {found.length > 1 && (
            <div className="rail-caption">{found.length} products</div>
          )}
          <ul className={found.length === 1 ? 'product-rail single' : 'product-rail'}>
            {found.map((item) => (
              <ProductTile key={item.id} item={item} busy={busy} onSendMessage={onSendMessage} />
            ))}
          </ul>
        </>
      )}
      {missing.map((item) => (
        <div key={item.id} className="missing-note">
          {item.id}: not available
        </div>
      ))}
    </div>
  )
}
