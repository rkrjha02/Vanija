import type { ReactNode } from 'react'

// Renders the small Markdown subset LLMs use (bold, bullet and numbered lists) as React elements, never as raw HTML.

function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith('**') && part.endsWith('**') && part.length > 4 ? <strong key={i}>{part.slice(2, -2)}</strong> : part.replace(/\*\*/g, ''),
  )
}

type Block = { kind: 'p'; lines: string[] } | { kind: 'ul' | 'ol'; items: string[] }

export function RichText({ text }: { text: string }) {
  const blocks: Block[] = []
  for (const raw of text.split('\n')) {
    const line = raw.trimEnd()
    const bullet = line.match(/^\s*[-*•]\s+(.*)$/)
    const numbered = line.match(/^\s*\d+[.)]\s+(.*)$/)
    const last = blocks[blocks.length - 1]
    if (bullet || numbered) {
      const kind = bullet ? 'ul' : 'ol'
      const item = (bullet ?? numbered)![1]
      if (last?.kind === kind) last.items.push(item)
      else blocks.push({ kind, items: [item] })
    } else if (line.trim() === '') {
      blocks.push({ kind: 'p', lines: [] })
    } else {
      const heading = line.replace(/^#{1,6}\s+/, '')
      if (last?.kind === 'p' && last.lines.length > 0) last.lines.push(heading)
      else blocks.push({ kind: 'p', lines: [heading] })
    }
  }

  return (
    <div className="rich-text">
      {blocks.map((block, i) => {
        if (block.kind === 'p') {
          if (block.lines.length === 0) return null
          return (
            <p key={i}>
              {block.lines.map((l, j) => (
                <span key={j}>
                  {j > 0 && <br />}
                  {inline(l)}
                </span>
              ))}
            </p>
          )
        }
        const List = block.kind
        return (
          <List key={i}>
            {block.items.map((item, j) => (
              <li key={j}>{inline(item)}</li>
            ))}
          </List>
        )
      })}
    </div>
  )
}
