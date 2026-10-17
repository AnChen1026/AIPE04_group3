export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

// 登入沿用 Session Cookie，所有請求都要帶 credentials
export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    credentials: 'include',
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      ...init.headers,
    },
  })

  if (!response.ok) {
    // FastAPI 的錯誤格式是 { detail: string }
    const body = await response.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : '系統忙碌中，請稍後再試。'
    throw new ApiError(response.status, detail)
  }

  return response.json() as Promise<T>
}
