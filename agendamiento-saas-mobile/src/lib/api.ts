import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';

import { ENV } from '@/config/env';
import { storage, STORAGE_KEYS } from '@/lib/storage';

/**
 * Cliente HTTP centralizado.
 *
 * - Base URL: `${ENV.apiBaseUrl}${ENV.apiPrefix}` → http://localhost:8000/rest/v1
 * - Header X-Tenant-Slug en TODAS las requests (el middleware del backend
 *   lo usa como fallback cuando Host no resuelve, ver
 *   apps/tenants/middleware.py:50-53).
 * - Inyecta Authorization: Bearer si hay access token en SecureStore.
 * - Si el backend responde 401, intenta refresh con el refresh token guardado.
 *   Si el refresh también falla, limpia el storage y propaga el error.
 */

let refreshPromise: Promise<string | null> | null = null;

// Cliente cross-clínica: NO mandamos X-Tenant-Slug porque el paciente puede
// reservar en cualquier clínica. Los endpoints del backend deducen el tenant
// del recurso enviado (doctor, appointment, etc.). Patient es global.
//
// Si en una versión futura quieres "fijar" una clínica favorita (ver memoria
// `project_app_movil_pacientes.md`), añade el header condicionalmente desde
// otro lado — no aquí.
export const api: AxiosInstance = axios.create({
  baseURL: `${ENV.apiBaseUrl}${ENV.apiPrefix}`,
  timeout: 20_000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

api.interceptors.request.use(async (config) => {
  const token = await storage.get(STORAGE_KEYS.accessToken);
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

async function performRefresh(): Promise<string | null> {
  const refresh = await storage.get(STORAGE_KEYS.refreshToken);
  if (!refresh) return null;

  try {
    // El endpoint TokenRefreshViewSet acepta {"refresh": "..."} y devuelve {"access": "..."}
    const res = await axios.post(
      `${ENV.apiBaseUrl}${ENV.apiPrefix}/user/auth/refresh-token/`,
      { refresh },
    );
    const newAccess: string | undefined = res.data?.access;
    if (!newAccess) return null;
    await storage.set(STORAGE_KEYS.accessToken, newAccess);
    return newAccess;
  } catch {
    return null;
  }
}

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original = error.config as (AxiosRequestConfig & { _retry?: boolean }) | undefined;
    const status = error.response?.status;

    if (status === 401 && original && !original._retry) {
      original._retry = true;
      refreshPromise = refreshPromise ?? performRefresh();
      const newAccess = await refreshPromise;
      refreshPromise = null;

      if (newAccess) {
        original.headers = original.headers ?? {};
        (original.headers as Record<string, string>).Authorization = `Bearer ${newAccess}`;
        return api(original);
      }

      // Refresh falló: limpiar credenciales para que el guard mande al login.
      await storage.remove(STORAGE_KEYS.accessToken);
      await storage.remove(STORAGE_KEYS.refreshToken);
      await storage.remove(STORAGE_KEYS.user);
    }
    return Promise.reject(error);
  },
);

/**
 * Convierte un AxiosError en un mensaje legible en español.
 * Maneja:
 *   - DRF: `{detail: "..."}` o `{error: "..."}`
 *   - Validation errors: `{campo: ["msg"]}` (toma el primero)
 *   - Throttling: 429
 *   - Sin red / timeout
 */
export function describeApiError(err: unknown): string {
  if (!axios.isAxiosError(err)) {
    return err instanceof Error ? err.message : 'Error desconocido.';
  }
  if (err.code === 'ECONNABORTED') return 'La solicitud tardó demasiado. Intenta otra vez.';
  if (!err.response) return 'No se pudo conectar con el servidor. Verifica tu conexión.';

  const { status, data } = err.response;
  if (status === 429) return 'Demasiados intentos. Espera unos segundos.';

  if (typeof data === 'string') return data;
  if (data && typeof data === 'object') {
    const obj = data as Record<string, unknown>;
    if (typeof obj.detail === 'string') return obj.detail;
    if (typeof obj.error === 'string') return obj.error;

    // Toma el primer error de campo
    for (const value of Object.values(obj)) {
      if (Array.isArray(value) && typeof value[0] === 'string') return value[0];
      if (typeof value === 'string') return value;
    }
  }
  return `Error ${status}.`;
}
