import Constants from 'expo-constants';
import { Platform } from 'react-native';

type Extra = {
  apiBaseUrl?: string;
  tenantSlug?: string;
};

const extra = (Constants.expoConfig?.extra ?? {}) as Extra;

/**
 * Base URL del backend Django. En desarrollo localhost solo funciona en
 * el simulador iOS. Para Android emulator usar 10.0.2.2; para dispositivo
 * físico usar la IP de tu Mac en LAN (ej. http://192.168.1.50:8000).
 *
 * Se puede sobreescribir con la variable de entorno EXPO_PUBLIC_API_BASE_URL
 * (Expo la inyecta en `process.env` durante el bundling).
 */
function resolveApiBaseUrl(): string {
  const fromEnv = process.env.EXPO_PUBLIC_API_BASE_URL;
  if (fromEnv) return fromEnv;

  const configured = extra.apiBaseUrl ?? 'http://localhost:8000';

  // Heurística para Android: si el dev configuró localhost, traducir a 10.0.2.2.
  if (Platform.OS === 'android' && /localhost|127\.0\.0\.1/.test(configured)) {
    return configured.replace(/localhost|127\.0\.0\.1/, '10.0.2.2');
  }
  return configured;
}

export const ENV = {
  apiBaseUrl: resolveApiBaseUrl(),
  apiPrefix: '/rest/v1',
  tenantSlug: process.env.EXPO_PUBLIC_TENANT_SLUG ?? extra.tenantSlug ?? 'clinica-a',
} as const;
