/**
 * Endpoints tipados — una función por endpoint del backend Django.
 * Todas pasan por el cliente `api` que ya inyecta X-Tenant-Slug y JWT.
 */

import { api } from '@/lib/api';
import type {
  ActivatePayload,
  Appointment,
  AppointmentCreatePayload,
  AuthUser,
  Doctor,
  LoginPayload,
  LoginResponse,
  Patient,
  PatientUpdate,
  RegisterPayload,
  RegisterResponse,
  Service,
  SlotsResponse,
  TenantPublic,
} from '@/types/api';

// ── Auth ─────────────────────────────────────────────────────────────────────
export async function login(payload: LoginPayload): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/user/auth/login/', payload);
  return data;
}

export async function registerPatient(payload: RegisterPayload): Promise<RegisterResponse> {
  // Endpoint específico de pacientes — crea User (is_active=False) + Patient
  // + envía email de activación. NO devuelve tokens; el paciente debe activar
  // y luego hacer login.
  const { data } = await api.post<RegisterResponse>('/public/patients/register/', payload);
  return data;
}

export async function activatePatient(payload: ActivatePayload): Promise<{ email: string }> {
  const { data } = await api.post<{ status: 'activated'; email: string }>(
    '/public/patients/activate/',
    payload,
  );
  return { email: data.email };
}

// ── Perfil del paciente ──────────────────────────────────────────────────────
export async function fetchMyProfile(): Promise<Patient> {
  const { data } = await api.get<Patient>('/patients/me/');
  return data;
}

export async function updateMyProfile(patch: PatientUpdate): Promise<Patient> {
  const { data } = await api.patch<Patient>('/patients/me/', patch);
  return data;
}

export async function logout(refresh: string | null): Promise<void> {
  if (!refresh) return;
  try {
    await api.post('/user/auth/logout/', { refresh });
  } catch {
    // Ignoramos errores de logout — el cliente ya borró tokens locales.
  }
}

// ── Tenant ───────────────────────────────────────────────────────────────────
export async function fetchTenant(slug: string): Promise<TenantPublic> {
  const { data } = await api.get<TenantPublic>(`/tenants/resolve/${slug}/`);
  return data;
}

// ── Catálogo cross-clínica ───────────────────────────────────────────────────
// Estos endpoints son globales (no filtran por tenant). La app móvil los usa
// para que el paciente pueda descubrir doctores de cualquier clínica.

export async function fetchDoctors(filters?: {
  q?: string;
  specialty?: string;
  tenant?: string;
  /**
   * Si true, el backend calcula la próxima disponibilidad por doctor.
   * Es más caro (N queries) — solo activar en la pantalla Inicio donde
   * realmente lo mostramos.
   */
  with_next_slot?: boolean;
  /**
   * Ubicación del usuario para ordenar/filtrar por distancia. Si los pasas,
   * cada doctor traerá `distance_km`. Requiere ambos (lat + lng); si solo
   * mandas uno, el backend ignora ambos.
   */
  lat?: number;
  lng?: number;
  radius_km?: number;
}): Promise<Doctor[]> {
  const params: Record<string, string> = {};
  if (filters?.q) params.q = filters.q;
  if (filters?.specialty) params.specialty = filters.specialty;
  if (filters?.tenant) params.tenant = filters.tenant;
  if (filters?.with_next_slot) params.with_next_slot = 'true';
  if (filters?.lat !== undefined && filters?.lng !== undefined) {
    params.lat = String(filters.lat);
    params.lng = String(filters.lng);
    if (filters.radius_km !== undefined) {
      params.radius_km = String(filters.radius_km);
    }
  }

  const { data } = await api.get<Doctor[]>('/public/discover/doctors/', { params });
  return data;
}

export async function fetchClinics(): Promise<import('@/types/api').DiscoverClinic[]> {
  const { data } = await api.get<import('@/types/api').DiscoverClinic[]>(
    '/public/discover/clinics/',
  );
  return data;
}

export async function fetchServicesForDoctor(doctorId: string): Promise<Service[]> {
  // Los servicios dependen del doctor (cada doctor ofrece sus propios servicios
  // dentro de su clínica). Ya no hay un "catálogo de servicios" global.
  const { data } = await api.get<Service[]>('/public/discover/services/', {
    params: { doctor: doctorId },
  });
  return data;
}

// ── Slots ────────────────────────────────────────────────────────────────────
export async function fetchSlots(params: {
  doctor: string;
  service: string;
  date: string;
}): Promise<SlotsResponse> {
  const { data } = await api.get<SlotsResponse>('/public/slots/', { params });
  return data;
}

// ── Appointments ─────────────────────────────────────────────────────────────
export async function createAppointment(
  payload: AppointmentCreatePayload,
): Promise<Appointment> {
  const { data } = await api.post<Appointment>('/public/appointments/', payload);
  return data;
}

// ── Places (autocomplete por CP) ─────────────────────────────────────────────
export async function fetchPostalCode(
  cp: string,
): Promise<import('@/types/api').PostalCodeInfo> {
  // 404 si el CP no existe — propaga el error para que el caller lo muestre.
  const { data } = await api.get<import('@/types/api').PostalCodeInfo>(
    `/public/places/postal-code/${cp}/`,
  );
  return data;
}

export async function fetchMyAppointments(): Promise<Appointment[]> {
  // Endpoint específico del paciente — cross-tenant (todas sus citas en
  // cualquier clínica donde haya reservado).
  const { data } = await api.get<Appointment[]>('/patients/me/appointments/');
  return data;
}

export async function fetchAppointmentDetail(id: string): Promise<Appointment> {
  const { data } = await api.get<Appointment>(`/patients/me/appointments/${id}/`);
  return data;
}

export async function rescheduleAppointment(
  id: string,
  payload: { date: string; start_time: string },
): Promise<Appointment> {
  const { data } = await api.patch<Appointment>(
    `/patients/me/appointments/${id}/`, payload,
  );
  return data;
}

export async function cancelAppointment(id: string): Promise<Appointment> {
  const { data } = await api.delete<Appointment>(
    `/patients/me/appointments/${id}/`,
  );
  return data;
}

// ── Reviews ─────────────────────────────────────────────────────────────────

import type { Review, CreateReviewPayload, CreateAnonymousReviewPayload } from '@/types/api';

export async function fetchDoctorReviews(doctorId: string): Promise<Review[]> {
  const { data } = await api.get<Review[]>(`/public/reviews/doctor/${doctorId}/`);
  return data;
}

export async function createReview(payload: CreateReviewPayload): Promise<Review> {
  // Endpoint AUTENTICADO — el patient se infiere del JWT.
  const { data } = await api.post<Review>('/reviews/', payload);
  return data;
}

export async function createAnonymousReview(
  payload: CreateAnonymousReviewPayload,
): Promise<{ status: 'pending'; message: string; email: string }> {
  // Endpoint PÚBLICO — crea PendingReview y manda email de confirmación.
  // La reseña NO se publica hasta confirmar el link.
  const { data } = await api.post<{ status: 'pending'; message: string; email: string }>(
    '/public/reviews/', payload,
  );
  return data;
}
