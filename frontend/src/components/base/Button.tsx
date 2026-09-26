import type { ButtonHTMLAttributes, PropsWithChildren } from 'react'
import { LoaderCircle } from 'lucide-react'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'

interface ButtonProps extends PropsWithChildren<ButtonHTMLAttributes<HTMLButtonElement>> {
  variant?: ButtonVariant
  loading?: boolean
}

export function Button({
  children,
  className = '',
  variant = 'primary',
  loading = false,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`button button--${variant} ${className}`.trim()}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <LoaderCircle className="button__spinner" aria-hidden="true" />}
      {children}
    </button>
  )
}
