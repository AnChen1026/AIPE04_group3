// 後端都走 /backend，開發時由 Vite 轉給 FastAPI；正式部署時由伺服器做同樣的轉址
export const API_BASE = '/backend'

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

type Body = Record<string, unknown> | unknown[] | FormData

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: Body
  query?: Record<string, string | number | boolean | null | undefined>
}

export function apiUrl(path: string, query?: RequestOptions['query']): string {
  const url = new URL(API_BASE + path, window.location.origin)
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== null && value !== undefined && value !== '') url.searchParams.set(key, String(value))
  }
  return url.pathname + url.search
}

// 登入沿用 Session Cookie，所有請求都要帶 credentials
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, query, headers, ...init } = options
  const isForm = body instanceof FormData
  const response = await fetch(apiUrl(path, query), {
    credentials: 'include',
    ...init,
    headers: {
      Accept: 'application/json',
      ...(body && !isForm ? { 'Content-Type': 'application/json' } : {}),
      ...headers,
    },
    body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
  })

  if (!response.ok) {
    // FastAPI 的錯誤格式是 { detail: string } 或欄位錯誤陣列
    const data = await response.json().catch(() => null)
    throw new ApiError(response.status, errorMessage(response.status, data?.detail))
  }

  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

function errorMessage(status: number, detail: unknown): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return '資料格式不正確，請再檢查一次。'
  if (status === 401) return '請先登入。'
  if (status === 403) return '沒有使用權限。'
  if (status === 413) return '檔案太大，無法上傳。'
  return '系統忙碌中，請稍後再試。'
}
