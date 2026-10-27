import { useEffect, useState, type KeyboardEvent } from 'react'
import { fetchCategories, fetchProduct, createProduct, updateProduct } from '../adminApi'

interface Props {
  productId: string | null
  onDone: () => void
}

interface SpecRow {
  key: string
  value: string
}

export function ProductForm({ productId, onDone }: Props) {
  const isEdit = productId !== null

  const [name, setName] = useState('')
  const [category, setCategory] = useState('')
  const [price, setPrice] = useState('')
  const [stock, setStock] = useState('')
  const [brand, setBrand] = useState('')
  const [shortDescription, setShortDescription] = useState('')
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState('')
  const [specs, setSpecs] = useState<SpecRow[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchCategories().then(setCategories).catch(() => {})
  }, [])

  useEffect(() => {
    if (!productId) return
    setLoading(true)
    fetchProduct(productId)
      .then((p) => {
        setName(p.name)
        setCategory(p.category)
        setPrice(String(p.price))
        setStock(String(p.stock))
        setBrand(p.brand ?? '')
        setShortDescription(p.short_description ?? '')
        setDescription(p.description ?? '')
        setTags(p.tags ?? [])
        if (p.specs) {
          setSpecs(Object.entries(p.specs).map(([key, value]) => ({ key, value: String(value) })))
        }
      })
      .catch(() => setError('Could not load product'))
      .finally(() => setLoading(false))
  }, [productId])

  function addTag(value: string) {
    const trimmed = value.trim()
    if (trimmed && !tags.includes(trimmed)) {
      setTags([...tags, trimmed])
    }
    setTagInput('')
  }

  function handleTagKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      addTag(tagInput)
    }
    if (e.key === 'Backspace' && !tagInput && tags.length > 0) {
      setTags(tags.slice(0, -1))
    }
  }

  function removeTag(index: number) {
    setTags(tags.filter((_, i) => i !== index))
  }

  function updateSpec(index: number, field: 'key' | 'value', value: string) {
    const next = [...specs]
    next[index] = { ...next[index], [field]: value }
    setSpecs(next)
  }

  function addSpecRow() {
    setSpecs([...specs, { key: '', value: '' }])
  }

  function removeSpecRow(index: number) {
    setSpecs(specs.filter((_, i) => i !== index))
  }

  function buildSpecsObj(): Record<string, string | number | boolean> | null {
    const validSpecs = specs.filter((s) => s.key.trim())
    if (validSpecs.length === 0) return null
    const obj: Record<string, string | number | boolean> = {}
    for (const s of validSpecs) {
      const v = s.value.trim()
      if (v === 'true') obj[s.key.trim()] = true
      else if (v === 'false') obj[s.key.trim()] = false
      else if (v !== '' && !isNaN(Number(v))) obj[s.key.trim()] = Number(v)
      else obj[s.key.trim()] = v
    }
    return obj
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (!name.trim()) { setError('Name is required'); return }
    if (!category.trim()) { setError('Category is required'); return }
    if (!price || Number(price) < 0) { setError('Price must be >= 0'); return }
    if (!stock || Number(stock) < 0) { setError('Stock must be >= 0'); return }

    const data: Record<string, unknown> = {
      name: name.trim(),
      category: category.trim().toLowerCase(),
      price: Number(price),
      stock: Number(stock),
    }
    if (brand.trim()) data.brand = brand.trim()
    if (shortDescription.trim()) data.short_description = shortDescription.trim()
    if (description.trim()) data.description = description.trim()
    if (tags.length > 0) data.tags = tags
    const specsObj = buildSpecsObj()
    if (specsObj) data.specs = specsObj

    setSaving(true)
    try {
      if (isEdit) {
        await updateProduct(productId, data)
      } else {
        await createProduct(data)
      }
      onDone()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div style={{ padding: 32, textAlign: 'center' }}>Loading...</div>
  }

  return (
    <form className="admin-form" onSubmit={handleSubmit}>
      <h2 style={{ marginTop: 0, marginBottom: 20 }}>{isEdit ? 'Edit Product' : 'Add Product'}</h2>

      {error && <div className="form-error">{error}</div>}

      <div className="field">
        <label htmlFor="pf-name">Name *</label>
        <input id="pf-name" type="text" value={name} onChange={(e) => setName(e.target.value)} />
      </div>

      <div className="field">
        <label htmlFor="pf-category">Category *</label>
        <input
          id="pf-category"
          type="text"
          list="category-list"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          placeholder="Type or select..."
        />
        <datalist id="category-list">
          {categories.map((c) => <option key={c} value={c} />)}
        </datalist>
      </div>

      <div style={{ display: 'flex', gap: 16 }}>
        <div className="field" style={{ flex: 1 }}>
          <label htmlFor="pf-price">Price (₹) *</label>
          <input id="pf-price" type="number" min="0" step="0.01" value={price} onChange={(e) => setPrice(e.target.value)} />
        </div>
        <div className="field" style={{ flex: 1 }}>
          <label htmlFor="pf-stock">Stock *</label>
          <input id="pf-stock" type="number" min="0" step="1" value={stock} onChange={(e) => setStock(e.target.value)} />
        </div>
      </div>

      <div className="field">
        <label htmlFor="pf-brand">Brand</label>
        <input id="pf-brand" type="text" value={brand} onChange={(e) => setBrand(e.target.value)} />
      </div>

      <div className="field">
        <label htmlFor="pf-short-desc">Short Description</label>
        <input id="pf-short-desc" type="text" value={shortDescription} onChange={(e) => setShortDescription(e.target.value)} />
      </div>

      <div className="field">
        <label htmlFor="pf-desc">Description</label>
        <textarea id="pf-desc" value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>

      <div className="field">
        <label>Tags</label>
        <div className="tags-input" onClick={() => document.getElementById('pf-tag-input')?.focus()}>
          {tags.map((tag, i) => (
            <span key={i} className="tag">
              {tag}
              <button type="button" onClick={() => removeTag(i)}>&times;</button>
            </span>
          ))}
          <input
            id="pf-tag-input"
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={handleTagKeyDown}
            onBlur={() => { if (tagInput.trim()) addTag(tagInput) }}
            placeholder={tags.length === 0 ? 'Type and press Enter...' : ''}
          />
        </div>
      </div>

      <div className="field">
        <label>Specs</label>
        <div className="specs-editor">
          {specs.map((row, i) => (
            <div key={i} className="spec-row">
              <input
                type="text"
                placeholder="Key (e.g. ram_gb)"
                value={row.key}
                onChange={(e) => updateSpec(i, 'key', e.target.value)}
              />
              <input
                type="text"
                placeholder="Value (e.g. 8)"
                value={row.value}
                onChange={(e) => updateSpec(i, 'value', e.target.value)}
              />
              <button type="button" className="btn btn-outline btn-sm" onClick={() => removeSpecRow(i)}>&times;</button>
            </div>
          ))}
          <button type="button" className="btn btn-outline btn-sm" onClick={addSpecRow}>+ Add spec</button>
        </div>
      </div>

      <div className="form-actions">
        <button type="submit" className="btn btn-accent" disabled={saving}>
          {saving ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Product'}
        </button>
        <button type="button" className="btn btn-outline" onClick={onDone}>Cancel</button>
      </div>
    </form>
  )
}
