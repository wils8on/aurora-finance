import { useEffect, useState } from 'react'
import { Menu } from 'lucide-react'
import { Outlet, useLocation } from 'react-router-dom'
import { AppSidebar } from '../components/navigation/AppSidebar'
import { IconButton } from '../components/base/IconButton'
import { useAuth } from '../features/auth/AuthContext'

export function AppLayout() {
  const [isNavigationOpen, setNavigationOpen] = useState(false)
  const location = useLocation()
  const { user, logout } = useAuth()

  useEffect(() => {
    setNavigationOpen(false)
  }, [location.pathname])

  if (!user) return null

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Ir para o conteúdo principal
      </a>
      <AppSidebar
        isOpen={isNavigationOpen}
        onClose={() => setNavigationOpen(false)}
        user={user}
        onLogout={logout}
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
          <IconButton
            className="menu-button"
            label="Abrir menu"
            icon={<Menu size={21} />}
            aria-expanded={isNavigationOpen}
            aria-controls="app-sidebar"
            onClick={() => setNavigationOpen(true)}
          />
          <span className="mobile-brand">Aurora Finance</span>
        </header>
        <main id="main-content" className="main-content" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
