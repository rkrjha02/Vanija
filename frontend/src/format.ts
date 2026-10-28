import type { CartProblem, SpecValue } from './types'

const wholeRupees = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})
const exactRupees = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

export function formatRupees(amount: number): string {
  return Number.isInteger(amount) ? wholeRupees.format(amount) : exactRupees.format(amount)
}

const SPEC_LABELS: Record<string, (value: SpecValue) => string | null> = {
  ram_gb: (v) => `${v} GB RAM`,
  storage_gb: (v) => `${v} GB storage`,
  battery_mah: (v) => `${v} mAh`,
  camera_mp: (v) => `${v} MP camera`,
  display_inch: (v) => `${v}" display`,
  processor: (v) => String(v),
  battery_hours: (v) => `${v} h battery`,
  noise_cancelling: (v) => (v ? 'Noise cancelling' : null),
  connectivity: (v) => String(v),
}

export function formatSpec(name: string, value: SpecValue): string | null {
  const label = SPEC_LABELS[name]
  if (label) return label(value)
  if (typeof value === 'boolean') return value ? name.replace(/_/g, ' ') : null
  return `${name.replace(/_/g, ' ')}: ${value}`
}

export function formatSpecs(specs: Record<string, SpecValue> | undefined): string[] {
  if (!specs) return []
  return Object.entries(specs)
    .map(([name, value]) => formatSpec(name, value))
    .filter((text): text is string => text !== null)
}

export function problemText(problem: CartProblem, unitsLeft?: number): string {
  switch (problem) {
    case 'out_of_stock':
      return 'Out of stock'
    case 'not_enough_stock':
      return unitsLeft === undefined ? 'Not enough stock' : `Only ${unitsLeft} left`
    case 'inactive':
      return 'No longer available'
    default:
      return ''
  }
}

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('en-IN', { hour: 'numeric', minute: '2-digit' })
}

// Label-value rows for the product cards, for example { ram_gb: 8 } -> { label: 'RAM', value: '8 GB' }.
const number = new Intl.NumberFormat('en-IN')
const SPEC_ROWS: Record<string, [string, (value: SpecValue) => string]> = {
  ram_gb: ['RAM', (v) => `${v} GB`],
  storage_gb: ['Storage', (v) => `${v} GB`],
  battery_mah: ['Battery', (v) => `${typeof v === 'number' ? number.format(v) : v} mAh`],
  camera_mp: ['Camera', (v) => `${v} MP`],
  display_inch: ['Display', (v) => `${v} inch`],
  processor: ['Processor', (v) => String(v)],
  battery_hours: ['Battery life', (v) => `${v} hours`],
  noise_cancelling: ['Noise cancelling', (v) => (v ? 'Yes' : 'No')],
  connectivity: ['Connectivity', (v) => String(v)],
}

export function specRows(specs: Record<string, SpecValue> | undefined): { label: string; value: string }[] {
  if (!specs) return []
  return Object.entries(specs).map(([name, value]) => {
    const known = SPEC_ROWS[name]
    if (known) return { label: known[0], value: known[1](value) }
    const label = name.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())
    return { label, value: typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value) }
  })
}

const CATEGORY_LABELS: Record<string, string> = { phone: 'Phones', laptop: 'Laptops', headphone: 'Headphones' }

export function categoryLabel(category: string | undefined): string {
  if (!category) return ''
  return CATEGORY_LABELS[category] ?? category.charAt(0).toUpperCase() + category.slice(1)
}
