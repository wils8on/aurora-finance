import { NavLink } from 'react-router-dom'
import {
  BarChart3,
  CircleDollarSign,
  Goal,
  House,
  Landmark,
  LayoutGrid,
  ListTree,
  ReceiptText,
  Sparkles,
  WalletCards,
  LogOut,
} from 'lucide-react'
import { useHealth } from '../../hooks/useHealth'
import type { AuthenticatedUser } from '../../types/api'

interface AppSidebarProps {
  isOpen: boolean
  onClose: () => void
  user: AuthenticatedUser
  onLogout: () => Promise<void>
}

const navigation = [
  { to: '/', label: 'Início', end: true, icon: House },
  { to: '/movimentacoes', label: 'Movimentações', icon: ReceiptText },
  { to: '/contas', label: 'Contas', icon: WalletCards },
  { to: '/categorias', label: 'Categorias', icon: ListTree },
]

const upcoming = [
  { label: 'Orçamento', icon: LayoutGrid },
  { label: 'Metas', icon: Goal },
  { label: 'Investimentos', icon: Landmark },
  { label: 'Relatórios', icon: BarChart3 },
]

export function AppSidebar({ isOpen, onClose, user, onLogout }: AppSidebarProps) {
  const { state: health, retry } = useHealth()
  return (
    <aside
      id="app-sidebar"
      className={`app-sidebar${isOpen ? ' app-sidebar--open' : ''}`}
      aria-label="Navegação principal"
    >
      <div className="sidebar-brand">
        <span className="brand-mark" aria-hidden="true"><Sparkles size={19} /></span>
        <div>
          <strong>Aurora</strong>
          <span>Finance</span>
        </div>
      </div>
      <nav className="sidebar-navigation">
        <span className="navigation-label">Navegação principal</span>
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
                <item.icon size={18} strokeWidth={1.8} aria-hidden="true" />
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <div className="sidebar-upcoming" aria-label="Funcionalidades em breve">
        <span className="navigation-label">Em breve</span>
        <ul>
          {upcoming.map((item) => (
            <li className="navigation-disabled" aria-disabled="true" key={item.label}>
              <item.icon size={18} strokeWidth={1.8} aria-hidden="true" />
              <span>{item.label}</span>
              <small>Em breve</small>
            </li>
          ))}
        </ul>
      </div>
      <div className={`sidebar-health sidebar-health--${health.kind}`} aria-live="polite">
        <CircleDollarSign size={18} aria-hidden="true" />
        <div>
          <strong>{health.kind === 'available' ? 'Sistema conectado' : health.kind === 'loading' ? 'Verificando sistema' : 'Sistema indisponível'}</strong>
          <span>{health.kind === 'available' ? 'API disponível' : health.kind === 'loading' ? 'Aguarde um instante' : 'Não foi possível conectar'}</span>
        </div>
        {health.kind === 'error' && <button type="button" onClick={retry}>Tentar novamente</button>}
      </div>
      <div className="sidebar-identity">
        <div><strong>{user.name}</strong><span>{user.email}</span></div>
        <button type="button" onClick={() => void onLogout()}><LogOut size={17} aria-hidden="true" />Sair</button>
      </div>
    </aside>
  )
}
