import { create } from 'zustand';

import * as queries from '@/lib/queries';
import { storage, STORAGE_KEYS } from '@/lib/storage';
import type { AuthUser, LoginPayload, RegisterPayload } from '@/types/api';

type AuthStatus = 'loading' | 'authenticated' | 'guest';

interface AuthState {
  status: AuthStatus;
  user: AuthUser | null;
  bootstrap: () => Promise<void>;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
}

/**
 * Estado global de auth — `bootstrap()` se llama una vez en el root layout
 * para hidratar desde SecureStore. Cuando no hay token, status='guest' y
 * el guard del layout (auth) redirige al login.
 */
export const useAuth = create<AuthState>((set, get) => ({
  status: 'loading',
  user: null,

  async bootstrap() {
    const [access, userRaw] = await Promise.all([
      storage.get(STORAGE_KEYS.accessToken),
      storage.get(STORAGE_KEYS.user),
    ]);
    if (!access) {
      set({ status: 'guest', user: null });
      return;
    }
    let user: AuthUser | null = null;
    if (userRaw) {
      try { user = JSON.parse(userRaw); } catch { user = null; }
    }
    set({ status: 'authenticated', user });
  },

  async login(payload) {
    const res = await queries.login(payload);
    await storage.set(STORAGE_KEYS.accessToken, res.access);
    await storage.set(STORAGE_KEYS.refreshToken, res.refresh);
    if (res.user) {
      await storage.set(STORAGE_KEYS.user, JSON.stringify(res.user));
    }
    set({ status: 'authenticated', user: res.user ?? null });
  },

  async register(payload) {
    await queries.registerPatient(payload);
    // El backend manda email de activación; no auto-login.
  },

  async logout() {
    const refresh = await storage.get(STORAGE_KEYS.refreshToken);
    await queries.logout(refresh);
    await storage.remove(STORAGE_KEYS.accessToken);
    await storage.remove(STORAGE_KEYS.refreshToken);
    await storage.remove(STORAGE_KEYS.user);
    set({ status: 'guest', user: null });
  },
}));

// Selectores convenientes
export const useIsAuthenticated = () => useAuth((s) => s.status === 'authenticated');
