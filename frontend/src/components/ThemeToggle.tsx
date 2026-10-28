import { toggleTheme, useTheme } from '../theme'
import { MoonIcon, SunIcon } from './Icons'

interface Props {
  className?: string
  withLabel?: boolean
}

export function ThemeToggle({ className = 'icon-button', withLabel = false }: Props) {
  const theme = useTheme()
  const label = theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'
  return (
    <button type="button" className={className} onClick={toggleTheme} aria-label={label} title={label}>
      {theme === 'dark' ? <SunIcon size={18} /> : <MoonIcon size={18} />}
      {withLabel && <span className="nav-label">{theme === 'dark' ? 'Light mode' : 'Dark mode'}</span>}
    </button>
  )
}
