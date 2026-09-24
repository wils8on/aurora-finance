import { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { AppSidebar } from '../components/navigation/AppSidebar'

export function AppLayout() {
  const [isNavigationOpen, setNavigationOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    setNavigationOpen(false)
  }, [location.pathname])

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Ir para o conteúdo principal
      </a>
      <AppSidebar
        isOpen={isNavigationOpen}
        onClose={() => setNavigationOpen(false)}
      />
      {isNavigationOpen && (
        <button
          className="sidebar-backdrop"
          type="button"
          aria-label="Fechar menu"
          onClick={() => setNavigationOpen(false)}
        />
      )}
      <div className="app-workspace">
        <header className="mobile-header">
          <button
            className="menu-button"
            type="button"
            aria-label="Abrir menu"
            aria-expanded={isNavigationOpen}
            aria-controls="app-sidebar"
            onClick={() => setNavigationOpen(true)}
          >
            <span aria-hidden="true">☰</span>
          </button>
          <span className="mobile-brand">Aurora Finance</span>
        </header>
        <main id="main-content" className="main-content" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
