import { ArrowRight, Eye, ListTree, ShieldCheck, Sparkles, WalletCards } from 'lucide-react'
import { Link } from 'react-router-dom'
import { GlassPanel } from '../components/base/GlassPanel'
import { PageHeader } from '../components/base/PageHeader'

const shortcuts = [
  { to: '/movimentacoes', title: 'Movimentações', description: 'Compromissos e realizações financeiras.', icon: Sparkles, status: 'Em preparação' },
  { to: '/contas', title: 'Contas', description: 'Cadastre onde seus recursos financeiros estão.', icon: WalletCards, status: 'Disponível' },
  { to: '/categorias', title: 'Categorias', description: 'Organize a natureza de receitas e despesas.', icon: ListTree, status: 'Disponível' },
]

const principles = [
  { title: 'Visão completa', description: 'Uma base preparada para reunir compromissos, realizações e planejamento sem confundir seus significados.', icon: Eye },
  { title: 'Mais controle', description: 'Dados organizados com rastreabilidade e uma interface que prioriza leitura rápida e consistência.', icon: ShieldCheck },
  { title: 'Decisões melhores', description: 'Uma arquitetura construída para transformar informações financeiras em contexto útil ao longo do tempo.', icon: Sparkles },
]

export function HomePage() {
  return (
    <div className="page-stack home-page">
      <GlassPanel className="home-hero">
        <PageHeader eyebrow="Seu espaço financeiro" title="Clareza para suas decisões financeiras." description="Gestão, planejamento e inteligência financeira pessoal em uma experiência simples, consistente e preparada para evoluir." />
        <div className="hero-orbit" aria-hidden="true"><span /><span /><span /></div>
      </GlassPanel>

      <section aria-labelledby="access-title">
        <div className="section-heading"><span className="section-label">Acesso rápido</span><h2 id="access-title">Comece por aqui</h2></div>
        <div className="shortcut-grid">
          {shortcuts.map((shortcut) => (
            <Link className="shortcut-card" to={shortcut.to} key={shortcut.to}>
              <span className="shortcut-card__icon"><shortcut.icon size={21} /></span>
              <span className="shortcut-card__status">{shortcut.status}</span>
              <h3>{shortcut.title}</h3><p>{shortcut.description}</p>
              <span className="shortcut-card__link">Acessar área <ArrowRight size={16} /></span>
            </Link>
          ))}
        </div>
      </section>

      <section className="principles-section" aria-labelledby="principles-title">
        <div className="section-heading"><span className="section-label">A proposta Aurora</span><h2 id="principles-title">Informação organizada para apoiar sua jornada.</h2></div>
        <div className="principles-grid">
          {principles.map((principle) => <article key={principle.title}><principle.icon size={20} aria-hidden="true" /><div><h3>{principle.title}</h3><p>{principle.description}</p></div></article>)}
        </div>
      </section>
    </div>
  )
}
