import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import type { Card } from '../types'
import { CardView } from './CardView'

function render(card: Card): string {
  return renderToStaticMarkup(
    <CardView card={card} customerId="c1" onButtonResult={() => {}} onButtonError={() => {}} />,
  )
}

const delivery = {
  name: 'Ravi',
  phone: '9876543210',
  address_line: '12 MG Road',
  city: 'Pune',
  state: 'Maharashtra',
  pincode: '411001',
}

describe('products card', () => {
  it('shows price, stock and key specs', () => {
    const html = render({
      type: 'products',
      items: [
        { id: 'PHN001', position: 1, name: 'Phone A', price: 9999, in_stock: true, key_specs: { ram_gb: 4 } },
        { id: 'PHN008', position: 2, name: 'Phone H', price: 69999, in_stock: false, key_specs: {} },
      ],
    })
    expect(html).toContain('Phone A')
    expect(html).toContain('₹9,999')
    expect(html).toContain('4 GB RAM')
    expect(html).toContain('Out of stock')
  })
})

describe('cart card', () => {
  it('shows line totals, the cart total and item problems', () => {
    const html = render({
      type: 'cart',
      items: [
        { product_id: 'PHN002', name: 'Phone B', quantity: 3, unit_price: 14999, line_total: 44997, problem: 'not_enough_stock', units_left: 2 },
      ],
      cart_total: 44997,
      has_problems: true,
    })
    expect(html).toContain('3 × ₹14,999')
    expect(html).toContain('₹44,997')
    expect(html).toContain('Only 2 left')
    expect(html).toContain('need attention')
  })
})

describe('order confirmation card', () => {
  const base = {
    type: 'order_confirmation' as const,
    summary: {
      items: [{ name: 'Phone A', quantity: 1, unit_price: 9999, line_total: 9999 }],
      cart_total: 9999,
      delivery,
      payment: 'Cash on Delivery',
    },
    pending_id: 5,
    expires_at: '2026-10-22T10:30:00+00:00',
  }

  it('offers to save a new address', () => {
    const html = render({ ...base, show_save_address: true })
    expect(html).toContain('Confirm order')
    expect(html).toContain('Confirm and save address')
    expect(html).toContain('Cash on Delivery')
    expect(html).toContain('411001')
  })

  it('shows only one button for a saved address', () => {
    const html = render({ ...base, show_save_address: false })
    expect(html).toContain('Confirm order')
    expect(html).not.toContain('save address')
  })
})

describe('cancel and result cards', () => {
  it('shows the cancel button', () => {
    const html = render({ type: 'cancel_confirmation', order_id: 7, items: [{ name: 'Phone A', quantity: 1 }], total: 9999 })
    expect(html).toContain('Cancel order #7?')
    expect(html).toContain('Yes, cancel order')
  })

  it('shows a placed order with the amount to pay', () => {
    const html = render({
      type: 'order_placed',
      order_id: 7,
      status: 'placed',
      total: 9999,
      items: [{ product_id: 'PHN001', name: 'Phone A', quantity: 1, unit_price: 9999, line_total: 9999 }],
      delivery,
    })
    expect(html).toContain('Order #7 placed')
    expect(html).toContain('Pay on delivery')
  })
})
