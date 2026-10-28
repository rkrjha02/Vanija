import { useEffect, useState } from 'react'
import { categoryLabel, formatRupees, specRows } from '../format'
import type { ProductItem, ProductsCard as ProductsCardData } from '../types'
import { CartIcon, CategoryIcon } from './Icons'

interface Props {
  card: ProductsCardData
  busy: boolean
  onSendMessage: (text: string) => void
}

interface ItemProps {
  item: ProductItem
  busy: boolean
  adding: boolean
  onAdd: () => void
  onDetails: () => void
}

function StockBadge({ item }: { item: ProductItem }) {
  if (!item.in_stock) return <span className="badge bad">Out of stock</span>
  if (item.units_left !== undefined && item.units_left <= 5) {
    return <span className="badge warn">Only {item.units_left} left</span>
  }
  return <span className="badge ok">In stock</span>
}

function ProductMeta({ item }: { item: ProductItem }) {
  const parts = [item.brand, categoryLabel(item.category)].filter(Boolean)
  if (parts.length === 0) return null
  return (
    <div className="product-meta">
      <CategoryIcon category={item.category} size={13} />
      <span>{parts.join(' · ')}</span>
    </div>
  )
}

function SpecList({ item, limit }: { item: ProductItem; limit?: number }) {
  const rows = specRows(item.key_specs ?? item.specs).slice(0, limit)
  if (rows.length === 0) return null
  return (
    <dl className="spec-list">
      {rows.map((row) => (
        <div key={row.label} className="spec-row">
          <dt>{row.label}</dt>
          <dd>{row.value}</dd>
        </div>
      ))}
    </dl>
  )
}

function AddButton({ item, busy, adding, onAdd, block = false }: Omit<ItemProps, 'onDetails'> & { block?: boolean }) {
  return (
    <button
      type="button"
      className={['btn', item.in_stock ? 'btn-accent' : 'btn-unavailable', block ? 'btn-block' : ''].join(' ').trim()}
      disabled={busy || !item.in_stock}
      onClick={onAdd}
    >
      {adding ? <span className="spinner" /> : item.in_stock && <CartIcon size={16} />}
      {adding ? 'Adding…' : item.in_stock ? 'Add to Cart' : 'Unavailable'}
    </button>
  )
}

function ProductTile({ item, busy, adding, onAdd, onDetails }: ItemProps) {
  return (
    <li className={item.in_stock ? 'product-card' : 'product-card unavailable'}>
      <div className="product-top">
        {item.position !== undefined ? (
          <span className="position-tag" title={`Item ${item.position} in this list`}>
            #{item.position}
          </span>
        ) : (
          <span />
        )}
        <StockBadge item={item} />
      </div>
      <h3 className="product-name" title={item.name}>
        {item.name}
      </h3>
      <ProductMeta item={item} />
      <div className="product-price">{formatRupees(item.price ?? 0)}</div>
      {item.description && <p className="product-desc">{item.description}</p>}
      <SpecList item={item} limit={4} />
      <div className="product-actions">
        <AddButton item={item} busy={busy} adding={adding} onAdd={onAdd} block />
        <button type="button" className="btn btn-outline" disabled={busy} onClick={onDetails}>
          Details
        </button>
      </div>
    </li>
  )
}

function ProductDetail({ item, busy, adding, onAdd }: Omit<ItemProps, 'onDetails'>) {
  return (
    <article className="card product-detail">
      <div className="detail-head">
        <div className="detail-title">
          <ProductMeta item={item} />
          <h3 className="detail-name">{item.name}</h3>
        </div>
        <StockBadge item={item} />
      </div>
      <div className="product-price lg">{formatRupees(item.price ?? 0)}</div>
      {item.description && <p className="detail-description">{item.description}</p>}
      <SpecList item={item} />
      <AddButton item={item} busy={busy} adding={adding} onAdd={onAdd} block />
    </article>
  )
}

export function ProductsCard({ card, busy, onSendMessage }: Props) {
  // Which product's Add button was tapped, so only that button shows "Adding…" while the chat reply is on its way.
  const [addingId, setAddingId] = useState<string | null>(null)
  useEffect(() => {
    if (!busy) setAddingId(null)
  }, [busy])

  const found = card.items.filter((item) => item.status !== 'not_found')
  const missing = card.items.filter((item) => item.status === 'not_found')
  const isDetail = found.length > 0 && found.every((item) => item.specs !== undefined)

  function add(item: ProductItem) {
    setAddingId(item.id)
    onSendMessage(`Add ${item.name} (${item.id}) to my cart`)
  }

  return (
    <div className="products-card">
      {isDetail ? (
        found.map((item) => (
          <ProductDetail key={item.id} item={item} busy={busy} adding={busy && addingId === item.id} onAdd={() => add(item)} />
        ))
      ) : (
        <>
          {found.length > 1 && <div className="rail-caption">{found.length} products found</div>}
          <ul className="product-grid">
            {found.map((item) => (
              <ProductTile
                key={item.id}
                item={item}
                busy={busy}
                adding={busy && addingId === item.id}
                onAdd={() => add(item)}
                onDetails={() => onSendMessage(`Tell me more about ${item.name} (${item.id})`)}
              />
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
