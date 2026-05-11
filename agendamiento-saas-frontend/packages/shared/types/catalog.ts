export interface Branch {
  id: string
  name: string
  address: string
  phone: string
  is_active: boolean
  created_at: string
}

export interface Doctor {
  id: string
  user: number
  email: string
  full_name: string
  branch: string | null
  branch_name: string | null
  specialty: string
  bio: string
  photo: string | null
  appointment_duration: number
  service_ids: string[]
  is_active: boolean
  created_at: string
}

export interface Service {
  id: string
  name: string
  description: string
  duration: number
  price: string
  color: string
  doctor_ids: string[]
  is_active: boolean
  created_at: string
}

export type Weekday = 0 | 1 | 2 | 3 | 4 | 5 | 6

export interface Schedule {
  id: string
  doctor: string
  weekday: Weekday
  weekday_label: string
  start_time: string
  end_time: string
  is_active: boolean
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
