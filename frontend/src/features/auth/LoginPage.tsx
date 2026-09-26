import { useState } from 'react'
import { Sparkles } from 'lucide-react'
import { ApiClientError } from '../../api/client'
import { Button } from '../../components/base/Button'
import { FormField } from '../../components/base/FormField'
import { Input } from '../../components/base/Input'
import { useAuth } from './AuthContext'

export function LoginPage() {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setError('')
    if (!email.trim() || !password) { setError('Informe email e senha.'); return }
    setBusy(true)
    try { await login(email, password) }
    catch (value) {
      const apiError = value as ApiClientError
      setError(apiError.status === 401 ? 'Email ou senha inválidos.' : 'Não foi possível entrar. Tente novamente.')
    } finally { setBusy(false) }
  }

  return <main className="login-page">
    <section className="login-panel" aria-labelledby="login-title">
      <div className="login-brand"><span className="brand-mark" aria-hidden="true"><Sparkles size={20} /></span><strong>Aurora Finance</strong></div>
      <span className="eyebrow">Acesso seguro</span>
      <h1 id="login-title">Entre na sua vida financeira</h1>
      <p>Use as credenciais provisionadas pelo administrador.</p>
      <form className="form-stack" onSubmit={submit} noValidate>
        <FormField htmlFor="login-email" label="Email" required><Input id="login-email" type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} /></FormField>
        <FormField htmlFor="login-password" label="Senha" required><Input id="login-password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} /></FormField>
        {error && <p className="login-error" role="alert">{error}</p>}
        <Button type="submit" loading={busy}>Entrar</Button>
      </form>
    </section>
  </main>
}
