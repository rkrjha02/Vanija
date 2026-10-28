import { useEffect, useRef, useState, type FormEvent } from 'react'
import { ApiError, getHistory, logout, sendMessage } from './api'
import { getName, isLoggedIn } from './auth'
import { STORE_NAME, STORE_TAGLINE, SUGGESTIONS } from './brand'
import { CardView } from './components/CardView'
import { AlertIcon, CartIcon, SendIcon, SettingsIcon, SparkIcon } from './components/Icons'
import { LoginPage } from './components/LoginPage'
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
  const [authed, setAuthed] = useState(isLoggedIn())
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [startError, setStartError] = useState<string | null>(null)
  const [ready, setReady] = useState(false)
  const started = useRef(false)
  const scrollRef = useRef<HTMLElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!authed) return
    if (started.current) return
    started.current = true
    getHistory()
      .then((history) => {
        setMessages(history.map((m) => makeMessage(m.role, m.content)))
        setReady(true)
      })
      .catch(() => setStartError('We could not reach the store right now.'))
  }, [authed])

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [messages, sending])

  function addMessage(message: ChatMessage) {
    setMessages((current) => [...current, message])
  }

  async function send(rawText: string) {
    const text = rawText.trim()
    if (!text || sending || !ready) return

    addMessage(makeMessage('user', text))
    setInput('')
    setSending(true)
    try {
      const reply = await sendMessage(text)
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

  async function handleLogout() {
    await logout()
    setAuthed(false)
    setMessages([])
    setReady(false)
    started.current = false
  }

  if (!authed) {
    return <LoginPage onLogin={() => setAuthed(true)} />
  }

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
              {startError ? 'Offline' : !ready ? 'Connecting…' : sending ? 'Typing…' : getName() ? `Hi, ${getName()}` : 'Shopping assistant · Online'}
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
          <button
            type="button"
            className="icon-button"
            onClick={() => void handleLogout()}
            aria-label="Log out"
            title={`Log out${getName() ? ` (${getName()})` : ''}`}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
          </button>
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

          {!startError && !ready && (
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
