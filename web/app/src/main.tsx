import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { loadBrand } from './config/brand'

async function bootstrap() {
  const brand = await loadBrand()

  // Apply brand to document
  document.title = brand.name
  const favicon = document.querySelector<HTMLLinkElement>('link[rel="icon"]')
  if (favicon) favicon.href = brand.faviconPath

  const themeLink = document.createElement('link')
  themeLink.rel = 'stylesheet'
  themeLink.href = brand.themePath
  document.head.appendChild(themeLink)

  // Sentry
  const sentryDsn = import.meta.env.VITE_SENTRY_DSN
  const sentry = window.Sentry
  if (sentryDsn && sentry) {
    sentry.init({
      dsn: sentryDsn,
      environment: import.meta.env.MODE,
      tracesSampleRate: 0.2,
    })
  }

  // Dynamic import ensures all modules see updated brand config
  const { default: App } = await import('./App')

  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}

bootstrap()
