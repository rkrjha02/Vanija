import { useEffect, useRef, useState, type FormEvent } from 'react'
import { ApiError, sendMessage, startSession } from './api'
import { CardView } from './components/CardView'
import { problemText } from './format'
import type { ButtonResult, Card, ChatMessage } from './types'
import './App.css'

let lastMessageId = 0
function makeMessage(role: ChatMessage['role'], text: string, cards: Card[] = [], isError = false): ChatMessage {
  lastMessageId += 1
  return { id: String(lastMessageId), role, text, cards, isError }
}

function buttonResultText(result: ButtonResult): string {
  const lines = [result.message]
  for (const p of result.problems ?? []) {
    lines.push(`• ${p.name}: ${problemText(p.problem, p.units_left)}`)
  }
  return lines.join('\n')
}

export default function App() {
  const [customerId, setCustomerId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [startError, setStartError] = useState<string | null>(null)
  const started = useRef(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    // React runs effects twice in development; without this guard a first visit creates two customers.
    if (started.current) return
    started.current = true
    startSession()
      .then(({ customerId, history }) => {
        setCustomerId(customerId)
        setMessages(history.map((m) => makeMessage(m.role, m.content)))
      })
      .catch(() => setStartError('Could not reach the store. Is the backend running?'))
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending])

  function addMessage(message: ChatMessage) {
    setMessages((current) => [...current, message])
  }

  async function handleSend(event: FormEvent) {
    event.preventDefault()
    const text = input.trim()
    if (!text || sending || !customerId) return

    addMessage(makeMessage('user', text))
    setInput('')
    setSending(true)
    try {
      const reply = await sendMessage(customerId, text)
      addMessage(makeMessage('assistant', reply.reply_text, reply.cards))
    } catch (error) {
      const text =
        error instanceof ApiError && error.status === 0
          ? 'That took too long. Please try again.'
          : 'Could not reach the store. Please try again.'
      addMessage(makeMessage('assistant', text, [], true))
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  function handleButtonResult(result: ButtonResult) {
    addMessage(makeMessage('assistant', buttonResultText(result), result.cards))
  }

  function handleButtonError(text: string) {
    addMessage(makeMessage('assistant', text, [], true))
  }

  return (
    <div className="app">
      <header className="header">
        <div className="avatar" aria-hidden="true">E</div>
        <div>
          <div className="header-title">Electronics Store</div>
          <div className="header-subtitle">{sending ? 'typing…' : 'Phones, laptops, headphones · Cash on Delivery'}</div>
        </div>
      </header>

      <main className="messages" aria-live="polite">
        {startError && <div className="system-note error">{startError}</div>}
        {!startError && customerId && messages.length === 0 && (
          <div className="system-note">
            Hi! Ask me about phones, laptops or headphones, for example “phones under 15000”.
          </div>
        )}
        {messages.map((message) => (
          <div key={message.id} className={`row ${message.role}`}>
            <div className={message.isError ? 'bubble error' : 'bubble'}>
              {message.text && <div className="bubble-text">{message.text}</div>}
              {message.cards.map((card, index) => (
                <CardView
                  key={index}
                  card={card}
                  customerId={customerId ?? ''}
                  onButtonResult={handleButtonResult}
                  onButtonError={handleButtonError}
                />
              ))}
            </div>
          </div>
        ))}
        {sending && (
          <div className="row assistant">
            <div className="bubble typing" aria-label="typing">
              <span />
              <span />
              <span />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </main>

      <form className="composer" onSubmit={handleSend}>
        <input
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={customerId ? 'Type a message' : 'Connecting…'}
          disabled={!customerId || sending}
          aria-label="Message"
          autoFocus
        />
        <button type="submit" className="primary" disabled={!customerId || sending || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  )
}
