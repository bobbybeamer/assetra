const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
const normalizedBaseUrl = apiBaseUrl.replace(/\/$/, '')

export type ApiErrorData = Record<string, unknown> | string | null

export class ApiError extends Error {
  status: number
  data: ApiErrorData

  constructor(message: string, status: number, data: ApiErrorData = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function stringifyUnknown(value: unknown): string {
  if (Array.isArray(value)) {
    return value.map((item) => String(item)).join(', ')
  }
  return String(value)
}

async function buildApiError(response: Response, fallbackMessage: string): Promise<ApiError> {
  try {
    const data = (await response.json()) as ApiErrorData
    if (typeof data === 'string') {
      return new ApiError(data, response.status, data)
    }

    if (isRecord(data)) {
      if (typeof data.detail === 'string') {
        return new ApiError(data.detail, response.status, data)
      }
      if (Array.isArray(data.non_field_errors) && data.non_field_errors.length > 0) {
        return new ApiError(String(data.non_field_errors[0]), response.status, data)
      }
      const firstKey = Object.keys(data)[0]
      if (firstKey) {
        return new ApiError(`${firstKey}: ${stringifyUnknown(data[firstKey])}`, response.status, data)
      }
      return new ApiError(fallbackMessage, response.status, data)
    }
  } catch {
    // Fall through to plain-text attempt/default fallback.
  }

  try {
    const text = await response.text()
    if (text) {
      return new ApiError(text, response.status, text)
    }
  } catch {
    // Ignore text parse errors.
  }

  return new ApiError(fallbackMessage, response.status)
}

export function extractFieldErrors(data: ApiErrorData): Record<string, string> {
  if (!isRecord(data)) {
    return {}
  }

  const output: Record<string, string> = {}
  for (const [key, value] of Object.entries(data)) {
    output[key] = stringifyUnknown(value)
  }
  return output
}

export function extractErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError && error.message) {
    return error.message
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return fallback
}

export type TokenResponse = {
  access: string
  refresh: string
}

export type RefreshTokenResponse = {
  access: string
  refresh?: string
}

export type AuthContextResponse = {
  username: string
  tenant_id: string
  role: 'admin' | 'operator' | 'auditor' | 'read_only' | string
  can_write: boolean
}

export type AssetRecord = {
  id: number
  asset_tag?: string
  name?: string
  status?: string
  [key: string]: unknown
}

export type CreateAssetInput = {
  asset_tag: string
  name: string
  status?: string
}

export type UpdateAssetInput = {
  name?: string
  status?: string
}

export type SyncResponse = {
  server_time?: string
  accepted_scan_event_ids?: Array<number | string>
  asset_changes?: AssetRecord[]
  [key: string]: unknown
}

export const getHealthUrl = () => `${normalizedBaseUrl}/health/`
const getTokenUrl = () => `${normalizedBaseUrl}/api/v1/auth/token/`
const getTokenRefreshUrl = () => `${normalizedBaseUrl}/api/v1/auth/token/refresh/`
const getAuthContextUrl = () => `${normalizedBaseUrl}/api/v1/auth/context/`
const getAssetsUrl = () => `${normalizedBaseUrl}/api/v1/assets/`
const getAssetDetailUrl = (assetId: number) => `${normalizedBaseUrl}/api/v1/assets/${assetId}/`
const getSyncUrl = () => `${normalizedBaseUrl}/api/v1/sync/`

export async function pingHealth(): Promise<void> {
  const response = await fetch(getHealthUrl(), {
    headers: {
      Accept: 'application/json',
    },
  })

  if (!response.ok) {
    throw await buildApiError(response, `Health check failed: ${response.status}`)
  }
}

export async function login(username: string, password: string): Promise<TokenResponse> {
  const response = await fetch(getTokenUrl(), {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  })

  if (!response.ok) {
    throw await buildApiError(response, `Login failed: ${response.status}`)
  }

  return (await response.json()) as TokenResponse
}

export async function refreshAccessToken(refresh: string): Promise<RefreshTokenResponse> {
  const response = await fetch(getTokenRefreshUrl(), {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh }),
  })

  if (!response.ok) {
    throw await buildApiError(response, `Token refresh failed: ${response.status}`)
  }

  return (await response.json()) as RefreshTokenResponse
}

export async function getAuthContext(accessToken: string, tenantId: string): Promise<AuthContextResponse> {
  const response = await fetch(getAuthContextUrl(), {
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${accessToken}`,
      'X-Tenant-ID': tenantId,
    },
  })

  if (!response.ok) {
    throw await buildApiError(response, `Auth context request failed: ${response.status}`)
  }

  return (await response.json()) as AuthContextResponse
}

export async function listAssets(accessToken: string, tenantId: string): Promise<AssetRecord[]> {
  const response = await fetch(getAssetsUrl(), {
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${accessToken}`,
      'X-Tenant-ID': tenantId,
    },
  })

  if (!response.ok) {
    throw await buildApiError(response, `Assets request failed: ${response.status}`)
  }

  const payload = (await response.json()) as AssetRecord[] | { results?: AssetRecord[] }
  return Array.isArray(payload) ? payload : payload.results ?? []
}

export async function getAssetDetail(
  assetId: number,
  accessToken: string,
  tenantId: string,
): Promise<AssetRecord> {
  const response = await fetch(getAssetDetailUrl(assetId), {
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${accessToken}`,
      'X-Tenant-ID': tenantId,
    },
  })

  if (!response.ok) {
    throw await buildApiError(response, `Asset detail request failed: ${response.status}`)
  }

  return (await response.json()) as AssetRecord
}

export async function createAsset(
  input: CreateAssetInput,
  accessToken: string,
  tenantId: string,
): Promise<AssetRecord> {
  const response = await fetch(getAssetsUrl(), {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
      'X-Tenant-ID': tenantId,
    },
    body: JSON.stringify(input),
  })

  if (!response.ok) {
    throw await buildApiError(response, `Asset create failed: ${response.status}`)
  }

  return (await response.json()) as AssetRecord
}

export async function updateAsset(
  assetId: number,
  input: UpdateAssetInput,
  accessToken: string,
  tenantId: string,
): Promise<AssetRecord> {
  const response = await fetch(getAssetDetailUrl(assetId), {
    method: 'PATCH',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
      'X-Tenant-ID': tenantId,
    },
    body: JSON.stringify(input),
  })

  if (!response.ok) {
    throw await buildApiError(response, `Asset update failed: ${response.status}`)
  }

  return (await response.json()) as AssetRecord
}

export async function runSync(accessToken: string, tenantId: string): Promise<SyncResponse> {
  const response = await fetch(getSyncUrl(), {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
      'X-Tenant-ID': tenantId,
    },
    body: JSON.stringify({}),
  })

  if (!response.ok) {
    throw await buildApiError(response, `Sync request failed: ${response.status}`)
  }

  return (await response.json()) as SyncResponse
}
