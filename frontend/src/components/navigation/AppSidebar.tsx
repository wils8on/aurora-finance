import { NavLink } from 'react-router-dom'

interface AppSidebarProps {
  isOpen: boolean
  onClose: () => void
}

const navigation = [
  { to: '/', label: 'Início', end: true },
  { to: '/movimentacoes', label: 'Movimentações' },
  { to: '/contas', label: 'Contas' },
  { to: '/categorias', label: 'Categorias' },
]

export function AppSidebar({ isOpen, onClose }: AppSidebarProps) {
  return (
    <aside
      id="app-sidebar"
      className={`app-sidebar${isOpen ? ' app-sidebar--open' : ''}`}
      aria-label="Navegação principal"
    >
      <div className="sidebar-brand">
        <span className="brand-mark" aria-hidden="true">A</span>
        <div>
          <strong>Aurora</strong>
          <span>Finance</span>
        </div>
      </div>
      <nav className="sidebar-navigation">
        <span className="navigation-label">Navegação</span>
        <ul>
          {navigation.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.end}
                onClick={onClose}
                className={({ isActive }) =>
                  `navigation-link${isActive ? ' navigation-link--active' : ''}`
                }
              >
                <span className="navigation-dot" aria-hidden="true" />
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <p className="sidebar-note">Foundation web · v0.1</p>
    </aside>
  )
}
