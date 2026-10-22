import { API_BASE, request } from './http'
import type { CurrentUser } from '@/types/user'

export interface TeacherApplication {
  id: string
  teaching_subjects: string
  teaching_experience: string
  bio: string
  proof_file_name: string | null
  has_proof: boolean
  status: string
  created_at: string
  user: {
    id: string
    email: string
    name: string
    role: string
    is_active: boolean
  }
}

export const fetchApplications = () => request<TeacherApplication[]>('/api/admin/teacher-applications')
export const approveApplication = (id: string) =>
  request<TeacherApplication>(`/api/admin/teacher-applications/${id}/approve`, { method: 'POST' })
export const rejectApplication = (id: string) =>
  request<TeacherApplication>(`/api/admin/teacher-applications/${id}/reject`, { method: 'POST' })

export const fetchAdminTeachers = () => request<CurrentUser[]>('/api/admin/teachers')
export const fetchAdminStudents = () => request<CurrentUser[]>('/api/admin/students')

export interface PasswordResetRequest {
  id: string
  status: 'pending' | 'completed' | 'dismissed'
  created_at: string
  handled_at: string | null
  user: {
    id: string
    email: string
    name: string
    role: string
    auth_provider: string
  }
}

export const fetchPasswordResets = () => request<PasswordResetRequest[]>('/api/admin/password-reset-requests')
export const resetPassword = (id: string) =>
  request<{ request: PasswordResetRequest; temporary_password: string }>(`/api/admin/password-reset-requests/${id}/reset`, { method: 'POST' })
export const dismissPasswordReset = (id: string) =>
  request<PasswordResetRequest>(`/api/admin/password-reset-requests/${id}/dismiss`, { method: 'POST' })

export function proofUrl(id: string): string {
  return `${API_BASE}/api/admin/teacher-applications/${id}/proof`
}
