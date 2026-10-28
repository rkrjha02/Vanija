import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import type { Card } from '../types'
import { CardView } from './CardView'

function render(card: Card): string {
  return renderToStaticMarkup(
    <CardView
      card={card}
      busy={false}
      onSendMessage={() => {}}
      onButtonResult={() => {}}
      onButtonError={() => {}}
    />,
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
    expect(html).toContain('RAM')
    expect(html).toContain('4 GB')
    expect(html).toContain('Out of stock')
  })

  it('offers Add to Cart and Details, and disables adding when out of stock', () => {
    const html = render({
      type: 'products',
      items: [{ id: 'PHN008', position: 1, name: 'Phone H', category: 'phone', price: 69999, in_stock: false, key_specs: {} }],
    })
    expect(html).toContain('Details')
    expect(html).toMatch(/<button[^>]*disabled=""[^>]*>Unavailable<\/button>/)
    expect(html).not.toContain('Add to Cart')
  })

  it('shows brand, category and an enabled Add to Cart for an in-stock product', () => {
    const html = render({
      type: 'products',
      items: [{ id: 'PHN001', position: 1, name: 'Phone A', brand: 'Acme', category: 'phone', price: 9999, in_stock: true, key_specs: {} }],
    })
    expect(html).toContain('Acme · Phones')
    expect(html).toContain('In stock')
    expect(html).toMatch(/<button[^>]*class="btn btn-accent btn-block"(?![^>]*disabled)[^>]*>.*?Add to Cart<\/button>/)
  })

  it('shows the detail layout when full specs are present', () => {
    const html = render({
      type: 'products',
      items: [
        { id: 'LAP001', name: 'Laptop A', category: 'laptop', price: 45999, in_stock: true, units_left: 3,
          description: 'A work laptop', specs: { ram_gb: 16, processor: 'Intel i5' } },
      ],
    })
    expect(html).toContain('product-detail')
    expect(html).toContain('A work laptop')
    expect(html).toContain('Intel i5')
    expect(html).toContain('Only 3 left')
    expect(html).toContain('Add to Cart')
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
    expect(html).not.toContain('Proceed to Order')
  })

  it('offers Proceed to Order when the cart has no problems', () => {
    const html = render({
      type: 'cart',
      items: [{ product_id: 'PHN001', name: 'Phone A', quantity: 1, unit_price: 9999, line_total: 9999, problem: '' }],
      cart_total: 9999,
      has_problems: false,
    })
    expect(html).toContain('Proceed to Order')
    expect(html).toContain('Total items')
  })

  it('shows an empty state instead of a zero total', () => {
    const html = render({ type: 'cart', items: [], cart_total: 0, has_problems: false })
    expect(html).toContain('Your cart is empty.')
    expect(html).not.toContain('₹0')
    expect(html).not.toContain('Proceed to Order')
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
    expect(html).toContain('Confirm Your Order')
    expect(html).toContain('Confirm Order')
    expect(html).toContain('Confirm and save address')
    expect(html).toContain('Cash on Delivery (COD)')
    expect(html).toContain('411001')
    expect(html).toContain('₹9,999')
    expect(html).toContain('Not now')
  })

  it('shows only one button for a saved address', () => {
    const html = render({ ...base, show_save_address: false })
    expect(html).toContain('Confirm Order')
    expect(html).not.toContain('save address')
  })
})

describe('cancel and result cards', () => {
  it('shows the cancel button', () => {
    const html = render({ type: 'cancel_confirmation', order_id: 7, items: [{ name: 'Phone A', quantity: 1 }], total: 9999 })
    expect(html).toContain('Cancel Order')
    expect(html).toContain('Order #7')
    expect(html).toContain('Are you sure you want to cancel this order?')
    expect(html).toContain('Confirm Cancellation')
    expect(html).toContain('No, keep my order')
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
    expect(html).toContain('Order Placed Successfully!')
    expect(html).toContain('#7')
    expect(html).toContain('Pay on delivery')
    expect(html).toContain('₹9,999')
  })

  it('shows a cancelled order without claiming a refund', () => {
    const html = render({
      type: 'order_cancelled',
      order_id: 7,
      status: 'cancelled',
      total: 9999,
      items: [{ product_id: 'PHN001', name: 'Phone A', quantity: 1, unit_price: 9999, line_total: 9999 }],
      delivery,
    })
    expect(html).toContain('Order Cancelled')
    expect(html).toContain('Your order has been cancelled successfully.')
    expect(html.toLowerCase()).not.toContain('refund')
  })
})
