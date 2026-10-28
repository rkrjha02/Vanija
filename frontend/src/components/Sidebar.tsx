import { useState } from 'react'
import { HELP_TOPICS, STORE_NAME, STORE_TAGLINE } from '../brand'
import { BrandMark } from './BrandMark'
import { CartIcon, ChatIcon, ChevronIcon, HelpIcon, LogoutIcon, XIcon } from './Icons'
import { ThemeToggle } from './ThemeToggle'

interface Props {
  open: boolean
  name: string | null
  canSend: boolean
  onClose: () => void
  onChat: () => void
  onSendMessage: (text: string) => void
  onLogout: () => void
}

// Every item here is wired to something that already works: Cart and Help send normal chat messages.
export function Sidebar({ open, name, canSend, onClose, onChat, onSendMessage, onLogout }: Props) {
  const [helpOpen, setHelpOpen] = useState(false)
  const displayName = name?.trim() || 'Customer'
  const firstName = displayName.split(/\s+/)[0]

  function sendAndClose(text: string) {
    onSendMessage(text)
    onClose()
  }

  return (
    <>
      <aside className={open ? 'sidebar open' : 'sidebar'} aria-label="Main navigation">
        <div className="sidebar-brand">
          <BrandMark />
          <div className="sidebar-brand-text">
            <div className="sidebar-name">{STORE_NAME}</div>
            <div className="sidebar-tagline">{STORE_TAGLINE}</div>
          </div>
          <button type="button" className="sidebar-close" onClick={onClose} aria-label="Close menu">
            <XIcon size={18} />
          </button>
        </div>

        <nav className="sidebar-nav">
          <button type="button" className="nav-item active" aria-current="page" onClick={onChat}>
            <ChatIcon size={18} />
            <span className="nav-label">Chat</span>
          </button>
          <button type="button" className="nav-item" onClick={() => sendAndClose("What's in my cart?")} disabled={!canSend}>
            <CartIcon size={18} />
            <span className="nav-label">Cart</span>
          </button>
          <button
            type="button"
            className="nav-item"
            onClick={() => setHelpOpen((v) => !v)}
            aria-expanded={helpOpen}
            aria-controls="help-topics"
          >
            <HelpIcon size={18} />
            <span className="nav-label">Help</span>
            <ChevronIcon size={15} className={helpOpen ? 'nav-chevron open' : 'nav-chevron'} />
          </button>
          {helpOpen && (
            <ul id="help-topics" className="help-list">
              {HELP_TOPICS.map((topic) => (
                <li key={topic.label}>
                  <button type="button" className="help-item" onClick={() => sendAndClose(topic.message)} disabled={!canSend}>
                    {topic.label}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </nav>

        <div className="sidebar-foot">
          <ThemeToggle className="nav-item" withLabel />
          <div className="profile">
            <div className="avatar" aria-hidden="true">
              {firstName.charAt(0).toUpperCase()}
            </div>
            <div className="profile-text">
              <div className="profile-name" title={displayName}>
                {firstName}
              </div>
              <div className="profile-sub">Signed in</div>
            </div>
            <button type="button" className="profile-logout" onClick={onLogout} aria-label="Log out" title="Log out">
              <LogoutIcon size={17} />
            </button>
          </div>
        </div>
      </aside>
      <div className={open ? 'sidebar-scrim show' : 'sidebar-scrim'} onClick={onClose} aria-hidden="true" />
    </>
  )
}
