// 對應後端 backend/schemas/user.py 的 UserResponse
export type UserRole = 'student' | 'teacher' | 'admin'

export interface CurrentUser {
  id: string
  email: string
  name: string
  phone_number: string | null
  birthdate: string | null
  sex: string | null
  role: UserRole
  is_active: boolean
  auth_provider: string
  application_status: string | null
  // 只用 Google 註冊、還沒設定密碼時為 false
  has_password?: boolean
  created_at: string
}
