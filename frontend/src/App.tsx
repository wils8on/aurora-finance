import { AppRoutes } from './routes/AppRoutes'
import { AuthGate } from './features/auth/AuthGate'
import { AuthProvider } from './features/auth/AuthContext'

export default function App() {
  return <AuthProvider><AuthGate><AppRoutes /></AuthGate></AuthProvider>
}
