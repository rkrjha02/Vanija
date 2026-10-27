import { useEffect, useState, useCallback } from 'react'
import {
  fetchProducts,
  fetchCategories,
  deleteProduct,
  reactivateProduct,
  type AdminProduct,
  type ProductListResponse,
} from '../adminApi'
import { formatRupees } from '../format'
import { CsvUpload } from './CsvUpload'

interface Props {
  onAdd: () => void
  onEdit: (id: string) => void
}

export function ProductList({ onAdd, onEdit }: Props) {
  const [data, setData] = useState<ProductListResponse | null>(null)
  const [categories, setCategories] = useState<string[]>([])
  const [brands, setBrands] = useState<string[]>([])
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [brand, setBrand] = useState('')
  const [activeFilter, setActiveFilter] = useState('')
  const [sortBy, setSortBy] = useState('name')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState<AdminProduct | null>(null)
  const [showUpload, setShowUpload] = useState(false)

  const pageSize = 20

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, string> = {
        page: String(page),
        page_size: String(pageSize),
        sort_by: sortBy,
        sort_order: sortOrder,
      }
      if (search) params.search = search
      if (category) params.category = category
      if (brand) params.brand = brand
      if (activeFilter) params.is_active = activeFilter
      const result = await fetchProducts(params)
      setData(result)
      const uniqueBrands = [...new Set(result.products.map((p) => p.brand).filter(Boolean) as string[])].sort()
      if (uniqueBrands.length > 0) setBrands(uniqueBrands)
    } catch {
      /* let the table show empty */
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, sortBy, sortOrder, search, category, brand, activeFilter])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    fetchCategories().then(setCategories).catch(() => {})
  }, [])

  function handleSort(col: string) {
    if (sortBy === col) {
      setSortOrder((o) => (o === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortBy(col)
      setSortOrder('asc')
    }
    setPage(1)
  }

  function sortArrow(col: string) {
    if (sortBy !== col) return ''
    return sortOrder === 'asc' ? ' ▲' : ' ▼'
  }

  async function handleDelete(product: AdminProduct) {
    try {
      await deleteProduct(product.id)
      setConfirmDelete(null)
      void load()
    } catch { /* keep dialog open */ }
  }

  async function handleReactivate(id: string) {
    try {
      await reactivateProduct(id)
      void load()
    } catch { /* ignore */ }
  }

  // Debounce search
  const [searchInput, setSearchInput] = useState('')
  useEffect(() => {
    const t = setTimeout(() => {
      setSearch(searchInput)
      setPage(1)
    }, 300)
    return () => clearTimeout(t)
  }, [searchInput])

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0
  const products = data?.products ?? []

  return (
    <>
      <div className="admin-toolbar">
        <input
          className="admin-search"
          type="text"
          placeholder="Search by name..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
        />
        <select
          className="admin-select"
          value={category}
          onChange={(e) => { setCategory(e.target.value); setPage(1) }}
        >
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <select
          className="admin-select"
          value={brand}
          onChange={(e) => { setBrand(e.target.value); setPage(1) }}
        >
          <option value="">All brands</option>
          {brands.map((b) => (
            <option key={b} value={b}>{b}</option>
          ))}
        </select>
        <select
          className="admin-select"
          value={activeFilter}
          onChange={(e) => { setActiveFilter(e.target.value); setPage(1) }}
        >
          <option value="">All statuses</option>
          <option value="true">Active</option>
          <option value="false">Inactive</option>
        </select>
        <div style={{ flex: 1 }} />
        <button type="button" className="btn btn-outline btn-sm" onClick={() => setShowUpload(true)}>
          Upload CSV
        </button>
        <button type="button" className="btn btn-accent btn-sm" onClick={onAdd}>
          Add Product
        </button>
      </div>

      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('name')}>Name<span className="sort-arrow">{sortArrow('name')}</span></th>
              <th onClick={() => handleSort('brand')}>Brand<span className="sort-arrow">{sortArrow('brand')}</span></th>
              <th onClick={() => handleSort('category')}>Category<span className="sort-arrow">{sortArrow('category')}</span></th>
              <th onClick={() => handleSort('price')}>Price<span className="sort-arrow">{sortArrow('price')}</span></th>
              <th onClick={() => handleSort('stock')}>Stock<span className="sort-arrow">{sortArrow('stock')}</span></th>
              <th>Status</th>
              <th>Embed</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && products.length === 0 && (
              <tr><td colSpan={8} style={{ textAlign: 'center', padding: 32 }}>Loading...</td></tr>
            )}
            {!loading && products.length === 0 && (
              <tr><td colSpan={8} style={{ textAlign: 'center', padding: 32, color: 'var(--text-muted)' }}>No products found</td></tr>
            )}
            {products.map((p) => (
              <tr key={p.id} className={p.is_active ? '' : 'inactive'}>
                <td><strong>{p.name}</strong><br /><span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{p.id}</span></td>
                <td>{p.brand ?? '-'}</td>
                <td>{p.category}</td>
                <td>{formatRupees(p.price)}</td>
                <td>{p.stock}</td>
                <td>
                  {p.is_active
                    ? <span className="badge badge-ok">Active</span>
                    : <span className="badge badge-bad">Inactive</span>
                  }
                </td>
                <td>{p.has_embedding ? <span className="badge badge-ok">Yes</span> : <span className="badge badge-neutral">No</span>}</td>
                <td>
                  <div className="actions">
                    <button type="button" className="btn btn-outline btn-sm" onClick={() => onEdit(p.id)}>Edit</button>
                    {p.is_active ? (
                      <button type="button" className="btn btn-danger btn-sm" onClick={() => setConfirmDelete(p)}>Delete</button>
                    ) : (
                      <button type="button" className="btn btn-outline btn-sm" onClick={() => handleReactivate(p.id)}>Reactivate</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {totalPages > 0 && (
          <div className="admin-pagination">
            <span>
              {data!.total} product{data!.total !== 1 ? 's' : ''} &middot; Page {page} of {totalPages}
            </span>
            <div className="admin-pagination-buttons">
              <button
                type="button"
                className="btn btn-outline btn-sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Prev
              </button>
              <button
                type="button"
                className="btn btn-outline btn-sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {confirmDelete && (
        <div className="modal-overlay" onClick={() => setConfirmDelete(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Delete product?</h2>
            <p>This will deactivate <strong>{confirmDelete.name}</strong>. It can be reactivated later.</p>
            <div className="modal-actions">
              <button type="button" className="btn btn-outline btn-sm" onClick={() => setConfirmDelete(null)}>Cancel</button>
              <button type="button" className="btn btn-danger btn-sm" onClick={() => handleDelete(confirmDelete)}>Delete</button>
            </div>
          </div>
        </div>
      )}

      {showUpload && (
        <CsvUpload
          onClose={() => setShowUpload(false)}
          onDone={() => { setShowUpload(false); void load() }}
        />
      )}
    </>
  )
}
