// 登入或註冊完成後要回去的頁面。只接受站內路徑，而且要是這個身分能進的地方。
export function safeRedirect(raw: unknown, role: string, fallback: string): string {
  const redirect = typeof raw === 'string' ? raw : ''
  if (!redirect.startsWith('/') || redirect.startsWith('//')) return fallback
  for (const area of ['teacher', 'student', 'admin']) {
    if (redirect.startsWith(`/${area}`) && role !== area) return fallback
  }
  // 聯繫老師只給學生；老師或管理員登入時回自己的後台
  if (redirect.includes('/contact') && role !== 'student') return fallback
  return redirect
}
