import { useEffect, useLayoutEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import { ApiError, getHistory, logout, sendMessage } from './api'
import { getName, isLoggedIn } from './auth'
import { STORE_FOOTNOTE, STORE_TAGLINE, SUGGESTIONS } from './brand'
import { BrandMark } from './components/BrandMark'
import { CardView } from './components/CardView'
import { AlertIcon, CartIcon, CategoryIcon, MenuIcon, SendIcon } from './components/Icons'
import { LoginPage } from './components/LoginPage'
import { RichText } from './components/RichText'
import { Sidebar } from './components/Sidebar'
import { ThemeToggle } from './components/ThemeToggle'
import { formatTime, problemText } from './format'
import type { ButtonResult, Card, ChatMessage } from './types'
import './App.css'

const COMPOSER_MAX_HEIGHT = 160

let lastMessageId = 0
function makeMessage(role: ChatMessage['role'], text: string, cards: Card[] = [], isError = false, fromHistory = false): ChatMessage {
  lastMessageId += 1
  // History messages carry no time from the backend, so only messages from this session show one.
  const time = fromHistory ? undefined : new Date().toISOString()
  return { id: String(lastMessageId), role, text, cards, isError, time }
}

function buttonResultText(result: ButtonResult): string {
  const lines = [result.message]
  for (const p of result.problems ?? []) {
    lines.push(`• ${p.name}: ${problemText(p.problem, p.units_left)}`)
  }
  return lines.join('\n')
}

export default function App() {
  const [authed, setAuthed] = useState(isLoggedIn())
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [startError, setStartError] = useState<string | null>(null)
  const [ready, setReady] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const started = useRef(false)
  const scrollRef = useRef<HTMLElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (!authed) return
    if (started.current) return
    started.current = true
    getHistory()
      .then((history) => {
        setMessages(history.map((m) => makeMessage(m.role, m.content, [], false, true)))
        setReady(true)
      })
      .catch(() => setStartError('We could not reach the store right now.'))
  }, [authed])

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [messages, sending])

  // Grow the message box with its content, up to a limit, then scroll inside it.
  useLayoutEffect(() => {
    const el = inputRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, COMPOSER_MAX_HEIGHT)}px`
  }, [input, authed])

  useEffect(() => {
    if (!menuOpen) return
    const onKey = (event: globalThis.KeyboardEvent) => {
      if (event.key === 'Escape') setMenuOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [menuOpen])

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
      // Give the text back so the customer can resend it without retyping.
      setInput((current) => current || text)
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    void send(input)
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      void send(input)
    }
  }

  function handleButtonResult(result: ButtonResult) {
    addMessage(makeMessage('assistant', buttonResultText(result), result.cards))
  }

  function handleButtonError(text: string) {
    addMessage(makeMessage('assistant', text, [], true))
  }

  async function handleLogout() {
    setMenuOpen(false)
    await logout()
    setAuthed(false)
    setMessages([])
    setReady(false)
    started.current = false
  }

  function focusChat() {
    setMenuOpen(false)
    inputRef.current?.focus()
    const el = scrollRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }

  if (!authed) {
    return <LoginPage onLogin={() => setAuthed(true)} />
  }

  const name = getName()
  const firstName = name?.trim().split(/\s+/)[0] || null
  const canSend = ready && !sending
  const showWelcome = ready && messages.length === 0
  const status = startError ? 'Offline' : !ready ? 'Connecting…' : sending ? 'Typing…' : 'Online'
  const statusTone = startError ? 'off' : !ready || sending ? 'busy' : 'on'

  return (
    <div className="app">
      <Sidebar
        open={menuOpen}
        name={name}
        canSend={canSend}
        onClose={() => setMenuOpen(false)}
        onChat={focusChat}
        onSendMessage={(text) => void send(text)}
        onLogout={() => void handleLogout()}
      />

      <div className="workspace">
        <header className="chat-header">
          <button type="button" className="icon-button menu-button" onClick={() => setMenuOpen(true)} aria-label="Open menu">
            <MenuIcon size={19} />
          </button>
          <div className="chat-header-brand">
            <BrandMark />
            <div className="chat-header-text">
              <div className="chat-header-title">{firstName ? `Hi, ${firstName}` : 'Hi there'}</div>
              <div className="chat-header-sub">{STORE_TAGLINE}</div>
            </div>
          </div>
          <div className="chat-header-actions">
            <div className={`status-pill ${statusTone}`} aria-live="polite">
              <span className="status-dot" />
              {status}
            </div>
            <button
              type="button"
              className="icon-button mobile-only"
              onClick={() => void send("What's in my cart?")}
              disabled={!canSend}
              aria-label="View cart"
              title="View cart"
            >
              <CartIcon size={18} />
            </button>
            <ThemeToggle className="icon-button mobile-only" />
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
                <button type="button" className="btn btn-accent" onClick={() => window.location.reload()}>
                  Retry
                </button>
              </div>
            )}

            {!startError && !ready && (
              <div className="state-panel">
                <div className="loader" aria-label="Connecting" />
                <div className="state-text">Loading your conversation…</div>
              </div>
            )}

            {showWelcome && (
              <section className="welcome">
                <BrandMark size="lg" />
                <h1 className="welcome-title">
                  {firstName ? `Hi ${firstName}, what are you shopping for today?` : 'What are you shopping for today?'}
                </h1>
                <p className="welcome-text">
                  Tell me what you need. I'll find the right product, check live prices and stock, and help you order with
                  Cash on Delivery.
                </p>
                <div className="suggestions">
                  {SUGGESTIONS.map((s) => (
                    <button key={s.label} type="button" className="suggestion" onClick={() => void send(s.message)}>
                      <span className="suggestion-icon">
                        {s.icon === 'cart' ? <CartIcon size={19} /> : <CategoryIcon category={s.icon} size={19} />}
                      </span>
                      <span className="suggestion-text">
                        <span className="suggestion-label">{s.label}</span>
                        <span className="suggestion-hint">{s.hint}</span>
                      </span>
                    </button>
                  ))}
                </div>
              </section>
            )}

            {messages.map((message) => (
              <div key={message.id} className={`msg ${message.role}`}>
                {message.role === 'assistant' && <BrandMark size="sm" />}
                <div className="msg-body">
                  {message.text && (
                    <div className={message.isError ? 'bubble error' : 'bubble'} role={message.isError ? 'alert' : undefined}>
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
                  {message.time && (
                    <time className="msg-time" dateTime={message.time}>
                      {formatTime(message.time)}
                    </time>
                  )}
                </div>
              </div>
            ))}

            {sending && (
              <div className="msg assistant">
                <BrandMark size="sm" />
                <div className="msg-body">
                  <div className="bubble typing" role="status">
                    <span />
                    <span />
                    <span />
                    <span className="sr-only">Vanija is typing</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>

        <footer className="composer-wrap">
          <form className="composer" onSubmit={handleSubmit}>
            <textarea
              ref={inputRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={ready ? 'Type a message...' : 'Connecting…'}
              disabled={!canSend}
              aria-label="Message"
              autoComplete="off"
              autoFocus
            />
            <button type="submit" className="send-button" disabled={!canSend || !input.trim()} aria-label="Send message">
              {sending ? <span className="spinner" /> : <SendIcon size={18} />}
            </button>
          </form>
          <div className="composer-note">
            {STORE_FOOTNOTE}
            <span className="composer-keys"> · Enter to send, Shift + Enter for a new line</span>
          </div>
        </footer>
      </div>
    </div>
  )
}
