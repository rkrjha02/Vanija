import type { ButtonResult, Card } from '../types'
import { CancelConfirmationCard } from './CancelConfirmationCard'
import { CartCard } from './CartCard'
import { OrderConfirmationCard } from './OrderConfirmationCard'
import { OrderResultCard } from './OrderResultCard'
import { ProductsCard } from './ProductsCard'

interface Props {
  card: Card
  customerId: string
  onButtonResult: (result: ButtonResult) => void
  onButtonError: (message: string) => void
}

export function CardView({ card, customerId, onButtonResult, onButtonError }: Props) {
  switch (card.type) {
    case 'products':
      return <ProductsCard card={card} />
    case 'cart':
      return <CartCard card={card} />
    case 'order_confirmation':
      return (
        <OrderConfirmationCard
          card={card}
          customerId={customerId}
          onResult={onButtonResult}
          onError={onButtonError}
        />
      )
    case 'cancel_confirmation':
      return (
        <CancelConfirmationCard
          card={card}
          customerId={customerId}
          onResult={onButtonResult}
          onError={onButtonError}
        />
      )
    case 'order_placed':
    case 'order_cancelled':
      return <OrderResultCard card={card} />
  }
}
