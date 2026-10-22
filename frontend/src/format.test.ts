import { describe, expect, it } from 'vitest'
import { formatRupees, formatSpecs, problemText } from './format'

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
