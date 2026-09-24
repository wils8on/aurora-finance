import { Route, Routes } from 'react-router-dom'
import { AccountsPage } from '../features/accounts/AccountsPage'
import { CategoriesPage } from '../features/categories/CategoriesPage'
import { TransactionsPage } from '../features/transactions/TransactionsPage'
import { AppLayout } from '../layouts/AppLayout'
import { HomePage } from '../pages/HomePage'
import { NotFoundPage } from '../pages/NotFoundPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<HomePage />} />
        <Route path="movimentacoes" element={<TransactionsPage />} />
        <Route path="contas" element={<AccountsPage />} />
        <Route path="categorias" element={<CategoriesPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
