import { request } from './http'
import type { CurrentUser } from '@/types/user'

export interface StudentRegisterInput {
  email: string
  password: string
  name: string
  phone_number: string
  birthdate: string
  sex: 'male' | 'female'
}

export interface TeacherRegisterInput extends StudentRegisterInput {
  password_confirm: string
  teaching_subjects: string
  teaching_experience: string
  bio: string
}

export function fetchCurrentUser(): Promise<CurrentUser> {
  return request<CurrentUser>('/api/auth/me')
}

export function login(email: string, password: string): Promise<CurrentUser> {
  return request<CurrentUser>('/api/auth/login', { method: 'POST', body: { email, password } })
}

export function logout(): Promise<{ message: string }> {
  return request('/api/auth/logout', { method: 'POST' })
}

export function registerStudent(input: StudentRegisterInput): Promise<CurrentUser> {
  return request<CurrentUser>('/api/auth/register', { method: 'POST', body: { ...input } })
}

// 老師註冊用表單格式，之後可以一起附證明文件
export function registerTeacher(input: TeacherRegisterInput, proof?: File | null): Promise<CurrentUser> {
  const form = new FormData()
  for (const [key, value] of Object.entries(input)) form.append(key, value)
  if (proof) form.append('proof_file', proof)
  return request<CurrentUser>('/api/auth/register/teacher', { method: 'POST', body: form })
}

export interface TeacherApplicationInput {
  teaching_subjects: string
  teaching_experience: string
  bio: string
}

// Google 註冊的老師補送申請資料，可附證明文件
export function submitTeacherApplication(input: TeacherApplicationInput, proof?: File | null): Promise<unknown> {
  const form = new FormData()
  for (const [key, value] of Object.entries(input)) form.append(key, value)
  if (proof) form.append('proof_file', proof)
  return request('/api/auth/teacher-application', { method: 'POST', body: form })
}

export function fetchGoogleUrl(role: 'student' | 'teacher', intent: 'login' | 'register'): Promise<{ url: string }> {
  return request('/api/auth/google-url', { query: { role, intent } })
}

export interface ProfileInput {
  name: string
  phone_number: string | null
  birthdate: string | null
  sex: 'male' | 'female'
}

// 學生、老師都能改自己的基本資料；Email 與角色不能在這裡改
export function updateMe(input: ProfileInput): Promise<CurrentUser> {
  return request<CurrentUser>('/api/auth/me', { method: 'PATCH', body: { ...input } })
}

// 忘記密碼（地端版本）：送出後由管理員在後台重設成臨時密碼。不管 Email 有沒有註冊都回同一句話
export function requestPasswordReset(email: string): Promise<{ message: string }> {
  return request('/api/auth/password-reset-requests', { method: 'POST', body: { email } })
}

// 修改自己的密碼。新密碼至少 8 個字元；還沒有密碼的 Google 帳號不用填目前密碼
export function changePassword(currentPassword: string | null, newPassword: string): Promise<{ message: string }> {
  return request('/api/auth/me/password', {
    method: 'POST',
    body: { current_password: currentPassword, new_password: newPassword },
  })
}
