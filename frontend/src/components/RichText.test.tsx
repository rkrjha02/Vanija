import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { RichText } from './RichText'

const render = (text: string) => renderToStaticMarkup(<RichText text={text} />)

describe('RichText', () => {
  it('renders bold and numbered lists without asterisks', () => {
    const html = render('Phones:\n\n1. **Phone A** – ₹8,999\n2. **Phone B** – ₹11,999')
    expect(html).toContain('<ol>')
    expect(html).toContain('<strong>Phone A</strong>')
    expect(html).not.toContain('**')
  })

  it('renders bullet lists', () => {
    const html = render('- **Price:** ₹11,999\n- **RAM:** 6 GB')
    expect(html).toContain('<ul>')
    expect(html).toContain('<li><strong>Price:</strong> ₹11,999</li>')
  })

  it('never turns text into HTML', () => {
    const html = render('<img src=x onerror=alert(1)> **hi**')
    expect(html).not.toContain('<img')
    expect(html).toContain('&lt;img')
  })
})
