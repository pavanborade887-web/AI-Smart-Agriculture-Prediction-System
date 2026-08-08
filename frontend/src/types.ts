export type Role = 'farmer' | 'admin'
export interface User { id: number; full_name: string; email: string; role: Role; is_active: boolean; created_at: string }
export interface AuthResponse { access_token: string; refresh_token: string; token_type: string; user: User }
