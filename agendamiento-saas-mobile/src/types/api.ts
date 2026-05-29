/**
 * Contratos del backend Django. Mantener en sync con
 * los serializers de cada app y apirest/urls.py.
 */

export type UUID = string;
export type ISODate = string; // YYYY-MM-DD
export type ISOTime = string; // HH:mm
export type ISODateTime = string;

// ── Auth ─────────────────────────────────────────────────────────────────────
export interface LoginPayload {
  email: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  is_superuser?: boolean;
  must_change_password?: boolean;
  user?: AuthUser;
}

export interface AuthUser {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  first_name: string;
  last_name?: string;
  phone?: string;
  birth_date?: string;
}

export interface RegisterResponse {
  status: 'registered';
  message: string;
  email: string;
}

export interface ActivatePayload {
  token: string;
}

// ── Patient ──────────────────────────────────────────────────────────────────
export type Gender = 'male' | 'female' | 'other' | 'undisclosed' | '';
export type BloodType = 'A+' | 'A-' | 'B+' | 'B-' | 'AB+' | 'AB-' | 'O+' | 'O-' | 'unknown' | '';

/** Opción genérica para el componente Select. */
export interface SelectOption<V extends string> {
  value: V;
  label: string;
}

// ── Reseñas ──────────────────────────────────────────────────────────────────

export interface Review {
  id: number;
  doctor: UUID;
  doctor_name: string;
  author_name: string;
  appointment: UUID | null;
  rating: number; // 1-5
  comment: string;
  is_published: boolean;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface CreateReviewPayload {
  doctor: UUID;
  appointment?: UUID;
  rating: number; // 1-5
  comment?: string;
}

export interface CreateAnonymousReviewPayload {
  doctor: UUID;
  reviewer_name: string;
  reviewer_email: string;
  rating: number;
  comment?: string;
}

/** Respuesta de GET /public/places/postal-code/{cp}/ */
export interface PostalCodeInfo {
  postal_code: string;
  state: string;
  city: string;
  neighborhoods: string[];
  country: string;
  lat: number | null;
  lng: number | null;
  source: 'zippopotam' | 'google' | string;
}

export interface Patient {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone: string;
  birth_date: ISODate | null;
  gender: Gender;
  // Clínicos
  blood_type: BloodType;
  allergies: string;
  current_medications: string;
  medical_conditions: string;
  // Dirección
  address_street: string;
  address_neighborhood: string;
  address_city: string;
  address_state: string;
  address_zip: string;
  address_country: string;
  // Emergencia
  emergency_contact_name: string;
  emergency_contact_phone: string;
  emergency_contact_relation: string;
  // ID MX
  curp: string;
  rfc: string;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export type PatientUpdate = Partial<Omit<Patient, 'id' | 'email' | 'full_name' | 'created_at' | 'updated_at'>>;

// ── Tenant ───────────────────────────────────────────────────────────────────
export interface TenantPublic {
  // Los modelos del SaaS usan UUID como PK (apps/tenants/models.py:11
  // y shared/models.py:51). En el wire se serializan como strings.
  id: UUID;
  slug: string;
  name: string;
  logo_url?: string | null;
  primary_color?: string | null;
  custom_domain?: string | null;
}

// ── Catalog ──────────────────────────────────────────────────────────────────
export interface Branch {
  id: UUID;
  name: string;
  address?: string;
  phone?: string;
}

export interface Doctor {
  // UUID porque Doctor hereda de TenantScopedModel (PK = UUIDField).
  id: UUID;
  // El endpoint cross-clínica `/public/discover/doctors/` devuelve el nombre
  // completo ya armado. Los endpoints internos por-tenant aún devuelven
  // first/last_name separados, pero la app móvil solo consume el discover.
  full_name: string;
  specialty?: string;
  bio?: string;
  photo_url?: string | null;
  appointment_duration?: number;
  // Cada doctor sabe a qué clínica pertenece.
  tenant_id: UUID;
  tenant_slug: string;
  tenant_name: string;
  // Agregados de reseñas — null si no tiene reseñas todavía.
  avg_rating: number | null;
  review_count: number;
  // Próxima disponibilidad — solo se llena si se pidió ?with_next_slot=true.
  next_available: { date: ISODate; start: ISOTime } | null;
  // Distancia en km al usuario — solo presente si se pidió con lat/lng.
  // Si el doctor no tiene branch geocodificada, queda null.
  distance_km: number | null;
}

export interface DiscoverClinic {
  id: UUID;
  slug: string;
  name: string;
  doctor_count: number;
}

export interface Service {
  id: UUID;
  name: string;
  description?: string;
  duration: number; // minutos
  price?: number | null;
  is_active?: boolean;
}

// ── Slots ────────────────────────────────────────────────────────────────────
export interface Slot {
  start: ISOTime; // "HH:mm"
}

export interface SlotsResponse {
  slots: Slot[];
  date: ISODate;
}

// ── Appointment ──────────────────────────────────────────────────────────────
export interface AppointmentCreatePayload {
  doctor: UUID;
  service: UUID;
  patient_name: string;
  patient_email: string;
  patient_phone: string;
  date: ISODate;
  start_time: ISOTime;
  notes?: string;
}

export type AppointmentStatus =
  | 'pending'
  | 'confirmed'
  | 'cancelled'
  | 'completed'
  | 'no_show';

export interface Appointment {
  id: UUID;
  doctor: UUID;
  doctor_name: string;
  service: UUID;
  service_name: string;
  tenant_slug: string;
  tenant_name: string;
  patient: number | null; // Patient sí es int (apps.patients.models.Patient — no hereda de TenantScopedModel)
  patient_name: string;
  patient_email: string;
  patient_phone: string;
  date: ISODate;
  start_time: ISOTime;
  end_time: ISOTime;
  status: AppointmentStatus;
  notes?: string;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

// ── Errores ──────────────────────────────────────────────────────────────────
export interface DjangoApiError {
  detail?: string;
  error?: string;
  code?: string;
  [field: string]: unknown;
}
