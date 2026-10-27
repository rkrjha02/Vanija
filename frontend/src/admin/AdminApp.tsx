import { useState } from 'react'
import { STORE_NAME } from '../brand'
import { ProductList } from './ProductList'
import { ProductForm } from './ProductForm'
import './admin.css'

type View = { page: 'list' } | { page: 'form'; productId: string | null }

export function AdminApp() {
  const [view, setView] = useState<View>({ page: 'list' })

  return (
    <div className="admin">
      <header className="admin-header">
        <div>
          <h1>{STORE_NAME} <span style={{ fontWeight: 450, color: 'var(--text-muted)' }}>/</span> Admin</h1>
        </div>
        <div className="admin-header-actions">
          <a href="/" className="btn btn-outline btn-sm">Back to Chat</a>
        </div>
      </header>

      <div className="admin-body">
        {view.page === 'list' && (
          <ProductList
            onAdd={() => setView({ page: 'form', productId: null })}
            onEdit={(id) => setView({ page: 'form', productId: id })}
          />
        )}
        {view.page === 'form' && (
          <ProductForm
            productId={view.productId}
            onDone={() => setView({ page: 'list' })}
          />
        )}
      </div>
    </div>
  )
}
