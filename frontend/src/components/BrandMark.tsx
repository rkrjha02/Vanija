import { BrandGlyph } from './Icons'

const GLYPH_SIZE = { sm: 15, md: 19, lg: 28 }

export function BrandMark({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  return (
    <div className={`store-mark ${size}`} aria-hidden="true">
      <BrandGlyph size={GLYPH_SIZE[size]} />
    </div>
  )
}
