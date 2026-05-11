export type AppointmentStatus = 'pending' | 'confirmed' | 'cancelled' | 'completed'

export interface Appointment {
  id: string
  doctor: string
  doctor_name: string
  service: string
  service_name: string
  patient_name: string
  patient_email: string
  patient_phone: string
  date: string
  start_time: string
  end_time: string
  status: AppointmentStatus
  notes: string

  // Clinical record
  clinical_notes: string
  weight_kg:      string | null
  height_cm:      string | null
  blood_pressure: string
  heart_rate:     number | null
  temperature_c:  string | null
  oxygen_sat:     number | null

  created_at: string
  updated_at: string
}

export interface Slot {
  start: string
  end: string
}
