export interface HealthResponse {
  status: string
}

export interface ApiError {
  code: string
  message: string
  field: string | null
  details: Record<string, unknown>
  request_id: string | null
}

export interface ApiErrorEnvelope {
  error: ApiError
}
