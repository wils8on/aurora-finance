import type {
  Category,
  CategoryCreate,
  Subcategory,
  SubcategoryCreate,
} from '../types/api'
import { apiGet, apiPost } from './client'

export function listCategories(): Promise<Category[]> {
  return apiGet<Category[]>('/categories')
}

export function createCategory(payload: CategoryCreate): Promise<Category> {
  return apiPost<Category, CategoryCreate>('/categories', payload)
}

export function listSubcategories(categoryId: number): Promise<Subcategory[]> {
  return apiGet<Subcategory[]>(`/categories/${categoryId}/subcategories`)
}

export function createSubcategory(
  categoryId: number,
  payload: SubcategoryCreate,
): Promise<Subcategory> {
  return apiPost<Subcategory, SubcategoryCreate>(
    `/categories/${categoryId}/subcategories`,
    payload,
  )
}
