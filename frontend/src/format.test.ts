import { describe, expect, it } from 'vitest'
import { categoryLabel, formatRupees, formatSpecs, problemText, specRows } from './format'

describe('formatRupees', () => {
  it('uses Indian digit grouping and no decimals for whole rupees', () => {
    expect(formatRupees(149999)).toBe('₹1,49,999')
  })

  it('shows paise when the amount is not whole', () => {
    expect(formatRupees(999.5)).toBe('₹999.50')
  })
})

describe('formatSpecs', () => {
  it('turns spec names into readable labels and skips false flags', () => {
    expect(formatSpecs({ ram_gb: 8, camera_mp: 50, noise_cancelling: false })).toEqual([
      '8 GB RAM',
      '50 MP camera',
    ])
  })
})

describe('problemText', () => {
  it('describes each cart problem', () => {
    expect(problemText('out_of_stock')).toBe('Out of stock')
    expect(problemText('not_enough_stock', 2)).toBe('Only 2 left')
    expect(problemText('inactive')).toBe('No longer available')
    expect(problemText('')).toBe('')
  })
})

describe('specRows', () => {
  it('turns specs into label and value pairs', () => {
    expect(specRows({ ram_gb: 8, battery_mah: 5000, noise_cancelling: true, refresh_rate: 120 })).toEqual([
      { label: 'RAM', value: '8 GB' },
      { label: 'Battery', value: '5,000 mAh' },
      { label: 'Noise cancelling', value: 'Yes' },
      { label: 'Refresh rate', value: '120' },
    ])
  })
})

describe('categoryLabel', () => {
  it('uses plural names for known categories', () => {
    expect(categoryLabel('phone')).toBe('Phones')
    expect(categoryLabel('tablet')).toBe('Tablet')
    expect(categoryLabel(undefined)).toBe('')
  })
})
