import { useEffect, useRef, useState, type FormEvent } from 'react'
import { ApiError, sendMessage, startSession } from './api'
import { STORE_NAME, STORE_TAGLINE, SUGGESTIONS } from './brand'
import { CardView } from './components/CardView'
import { AlertIcon, CartIcon, SendIcon, SettingsIcon, SparkIcon } from './components/Icons'
import { RichText } from './components/RichText'
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

function StoreMark({ size = 'md' }: { size?: 'md' | 'lg' }) {
  return (
    <div className={`store-mark ${size}`} aria-hidden="true">
      <SparkIcon size={size === 'lg' ? 26 : 18} />
    </div>
  )
}

export default function App() {
  const [customerId, setCustomerId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [startError, setStartError] = useState<string | null>(null)
  const started = useRef(false)
  const scrollRef = useRef<HTMLElement>(null)
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
      .catch(() => setStartError('We could not reach the store right now.'))
  }, [])

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [messages, sending])

  function addMessage(message: ChatMessage) {
    setMessages((current) => [...current, message])
  }

  async function send(rawText: string) {
    const text = rawText.trim()
    if (!text || sending || !customerId) return

    addMessage(makeMessage('user', text))
    setInput('')
    setSending(true)
    try {
      const reply = await sendMessage(customerId, text)
      addMessage(makeMessage('assistant', reply.reply_text, reply.cards))
    } catch (error) {
      const errorText =
        error instanceof ApiError && error.status === 0
          ? 'That took too long. Please try again.'
          : 'Could not reach the store. Please try again.'
      addMessage(makeMessage('assistant', errorText, [], true))
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    void send(input)
  }

  function handleButtonResult(result: ButtonResult) {
    addMessage(makeMessage('assistant', buttonResultText(result), result.cards))
  }

  function handleButtonError(text: string) {
    addMessage(makeMessage('assistant', text, [], true))
  }

  const ready = customerId !== null && !startError
  const showWelcome = ready && messages.length === 0

  return (
    <div className="app">
      <header className="header">
        <div className="header-brand">
          <StoreMark />
          <div className="header-text">
            <div className="header-title">{STORE_NAME}</div>
            <div className="header-status" aria-live="polite">
              <span className={`status-dot ${startError ? 'off' : sending ? 'busy' : 'on'}`} />
              {startError ? 'Offline' : !customerId ? 'Connecting…' : sending ? 'Typing…' : 'Shopping assistant · Online'}
            </div>
          </div>
        </div>
        <div className="header-actions">
          <button
            type="button"
            className="icon-button"
            onClick={() => void send("What's in my cart?")}
            disabled={!ready || sending}
            aria-label="View cart"
            title="View cart"
          >
            <CartIcon size={18} />
          </button>
          <a
            href="/admin"
            className="icon-button"
            aria-label="Admin panel"
            title="Admin panel"
          >
            <SettingsIcon size={18} />
          </a>
        </div>
      </header>

      <main className="messages" ref={scrollRef}>
        <div className="messages-inner" aria-live="polite">
          {startError && (
            <div className="state-panel">
              <div className="state-icon bad">
                <AlertIcon size={22} />
              </div>
              <div className="state-title">{startError}</div>
              <div className="state-text">Please check your connection and try again.</div>
              <button type="button" className="btn btn-ink" onClick={() => window.location.reload()}>
                Retry
              </button>
            </div>
          )}

          {!startError && !customerId && (
            <div className="state-panel">
              <div className="loader" aria-label="Connecting" />
            </div>
          )}

          {showWelcome && (
            <section className="welcome">
              <StoreMark size="lg" />
              <h1 className="welcome-title">How can I help you today?</h1>
              <p className="welcome-text">
                Tell me what you're looking for. I'll find the right product, check live prices and stock, and help
                you order with Cash on Delivery.
              </p>
              <div className="suggestions">
                {SUGGESTIONS.map((s) => (
                  <button key={s.label} type="button" className="chip" onClick={() => void send(s.message)}>
                    {s.label}
                  </button>
                ))}
              </div>
            </section>
          )}

          {messages.map((message) => (
            <div key={message.id} className={`msg ${message.role}`}>
              {message.role === 'assistant' && <StoreMark />}
              <div className="msg-body">
                {message.text && (
                  <div className={message.isError ? 'bubble error' : 'bubble'}>
                    {message.isError && <AlertIcon size={16} />}
                    {message.role === 'assistant' && !message.isError ? (
                      <RichText text={message.text} />
                    ) : (
                      <span className="bubble-text">{message.text}</span>
                    )}
                  </div>
                )}
                {message.cards.map((card, index) => (
                  <CardView
                    key={index}
                    card={card}
                    customerId={customerId ?? ''}
                    busy={sending}
                    onSendMessage={(text) => void send(text)}
                    onButtonResult={handleButtonResult}
                    onButtonError={handleButtonError}
                  />
                ))}
              </div>
            </div>
          ))}

          {sending && (
            <div className="msg assistant">
              <StoreMark />
              <div className="msg-body">
                <div className="bubble typing" aria-label="Assistant is typing">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="composer-wrap">
        <form className="composer" onSubmit={handleSubmit}>
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={ready ? 'Ask about a product, your cart or an order…' : 'Connecting…'}
            disabled={!ready || sending}
            aria-label="Message"
            autoComplete="off"
            autoFocus
          />
          <button
            type="submit"
            className="send-button"
            disabled={!ready || sending || !input.trim()}
            aria-label="Send"
          >
            <SendIcon size={18} />
          </button>
        </form>
        <div className="composer-note">{STORE_TAGLINE}</div>
      </footer>
    </div>
  )
}
