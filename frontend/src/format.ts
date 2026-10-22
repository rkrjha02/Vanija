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
