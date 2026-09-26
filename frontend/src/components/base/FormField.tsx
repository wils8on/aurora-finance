import type { PropsWithChildren } from 'react'

interface FormFieldProps extends PropsWithChildren {
  htmlFor: string
  label: string
  helper?: string
  error?: string
  required?: boolean
}

export function FormField({ htmlFor, label, helper, error, required, children }: FormFieldProps) {
  return (
    <div className="form-field">
      <label htmlFor={htmlFor}>
        {label}{required && <span aria-hidden="true"> *</span>}
      </label>
      {children}
      {error ? <p className="field-message field-message--error" id={`${htmlFor}-error`}>{error}</p> : helper ? <p className="field-message" id={`${htmlFor}-helper`}>{helper}</p> : null}
    </div>
  )
}
