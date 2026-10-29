export type SpecValue = string | number | boolean

export interface Delivery {
  name: string
  phone: string
  address_line: string
  city: string
  state: string
  pincode: string
}

export interface ProductItem {
  id: string
  status?: 'not_found'
  position?: number
  name?: string
  brand?: string | null
  category?: string
  price?: number
  in_stock?: boolean
  key_specs?: Record<string, SpecValue>
  specs?: Record<string, SpecValue>
  units_left?: number
  description?: string | null
}

export type CartProblem = '' | 'out_of_stock' | 'not_enough_stock' | 'inactive'

export interface CartItem {
  product_id: string
  name: string
  quantity: number
  unit_price: number
  line_total: number
  problem: CartProblem
  units_left?: number
}

export interface SummaryItem {
  name: string
  quantity: number
  unit_price: number
  line_total: number
}

export interface OrderItem extends SummaryItem {
  product_id: string
}

export interface ProductsCard {
  type: 'products'
  items: ProductItem[]
}

export interface CartCard {
  type: 'cart'
  items: CartItem[]
  cart_total: number
  has_problems: boolean
}

export interface OrderConfirmationCard {
  type: 'order_confirmation'
  summary: {
    items: SummaryItem[]
    cart_total: number
    delivery: Delivery
    payment: string
  }
  pending_id: number
  expires_at: string
  show_save_address: boolean
}

export interface CancelConfirmationCard {
  type: 'cancel_confirmation'
  order_id: number
  items: { name: string; quantity: number }[]
  total: number
}

export interface OrderResultCard {
  type: 'order_placed' | 'order_cancelled'
  order_id: number
  status: 'placed' | 'cancelled'
  total: number
  items: OrderItem[]
  delivery: Delivery
}

export type Card =
  | ProductsCard
  | CartCard
  | OrderConfirmationCard
  | CancelConfirmationCard
  | OrderResultCard

export interface ChatReply {
  reply_text: string
  cards: Card[]
}

export interface HistoryMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  cards?: Card[] | null
}

export interface HistoryPage {
  messages: HistoryMessage[]
  has_more: boolean
}

export interface ButtonResult {
  status: string
  message: string
  cards: Card[]
  problems?: { name: string; problem: CartProblem; units_left?: number }[]
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  text: string
  cards: Card[]
  isError?: boolean
  time?: string
}
