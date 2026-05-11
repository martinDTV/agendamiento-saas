export interface Room {
  id: string
  name: string
  branch: string
  branch_name: string
  capacity: number
  is_active: boolean
  created_at: string
}

export interface MeetingUser {
  id: number
  email: string
  full_name: string
}

export interface Meeting {
  id: string
  title: string
  description: string
  organizer: number
  organizer_name: string
  participants: number[]
  participants_detail: MeetingUser[]
  room: string | null
  room_name: string | null
  date: string
  start_time: string
  end_time: string
  created_at: string
}

export interface Membership {
  id: string
  user: number
  user_email: string
  user_uuid: string
  user_first_name: string
  user_last_name: string
  user_full_name: string
  role: string
  is_active: boolean
  created_at: string
}
