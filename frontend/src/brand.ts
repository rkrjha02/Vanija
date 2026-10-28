export const STORE_NAME = 'Vanija'
export const STORE_TAGLINE = 'Your AI Shopping Assistant'
export const STORE_FOOTNOTE = 'Live prices and stock · Cash on Delivery'

export const SUGGESTIONS: { label: string; hint: string; icon: 'phone' | 'laptop' | 'headphone' | 'cart'; message: string }[] = [
  { label: 'Phones under ₹15,000', hint: 'Best value picks', icon: 'phone', message: 'Show me phones under 15000' },
  { label: 'Laptops for work', hint: 'Light and reliable', icon: 'laptop', message: 'I need a laptop for work' },
  { label: 'Wireless headphones', hint: 'With long battery life', icon: 'headphone', message: 'Show me wireless headphones' },
  { label: "What's in my cart?", hint: 'Review and order', icon: 'cart', message: "What's in my cart?" },
]

// Quick policy questions shown under Help. Each one is answered from the store's policy documents.
export const HELP_TOPICS: { label: string; message: string }[] = [
  { label: 'Returns', message: 'What is your return policy?' },
  { label: 'Warranty', message: 'What warranty do your products have?' },
  { label: 'Shipping', message: 'How does shipping and delivery work?' },
  { label: 'Cash on Delivery', message: 'How does Cash on Delivery work?' },
  { label: 'Cancellations', message: 'What is your cancellation policy?' },
]
