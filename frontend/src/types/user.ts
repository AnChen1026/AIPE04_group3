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
  created_at: string
}
