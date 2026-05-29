# Agendamiento — App móvil (pacientes)

App nativa de **pacientes** del SaaS de agendamiento, construida con **Expo SDK 56 + React Native 0.85 + Expo Router + Nativewind**. Es la cuarta superficie del producto, complementa al admin web (Nuxt) y al sitio público.

> **Decisión arquitectónica (LLM Council 2026-05-15):** el admin **NO** se hace en RN. Esta app es solo para pacientes — buscar doctor, agendar, ver mis citas, perfil. Si en algún momento se evalúa un admin móvil, releer `memory/project_arquitectura_decisiones.md`.

---

## Stack

| Pieza | Versión / herramienta |
|---|---|
| Expo SDK | 56 |
| React Native | 0.85 |
| Router | expo-router 56 (file-based) |
| Estilos | Nativewind 4 + Tailwind 3.4 |
| Estado servidor | TanStack Query 5 |
| Estado cliente | Zustand 5 |
| HTTP | Axios |
| Auth | JWT (SimpleJWT) en `expo-secure-store` |
| Iconos | `@expo/vector-icons` (Ionicons) |
| Tipos | TypeScript 6, strict |

---

## Estructura

```
agendamiento-saas-mobile/
├── app/                          # Rutas (expo-router, file-based)
│   ├── _layout.tsx               # Root: providers, auth gate, splash
│   ├── index.tsx                 # Redirect según auth
│   ├── (auth)/                   # Grupo no autenticado
│   │   ├── login.tsx
│   │   └── register.tsx
│   ├── (tabs)/                   # Grupo con tab bar
│   │   ├── index.tsx             # Home: buscar doctores
│   │   ├── appointments.tsx      # Mis citas
│   │   └── profile.tsx           # Perfil
│   ├── doctor/[id].tsx           # Detalle de doctor
│   └── booking/                  # Wizard de reserva
│       ├── select-service.tsx
│       ├── select-slot.tsx
│       ├── confirm.tsx
│       └── success.tsx
├── src/
│   ├── components/               # UI compartida (Button, Input, Card…)
│   ├── config/env.ts             # Lee apiBaseUrl / tenantSlug
│   ├── lib/
│   │   ├── api.ts                # Axios + interceptors + refresh JWT
│   │   ├── queries.ts            # Funciones tipadas por endpoint
│   │   ├── format.ts             # Formato fechas/horas/$
│   │   └── storage.ts            # SecureStore wrapper
│   ├── providers/QueryProvider.tsx
│   ├── stores/                   # Zustand (auth, booking)
│   └── types/api.ts              # Tipos del backend
├── app.json
├── babel.config.js               # nativewind + worklets plugin
├── metro.config.js               # withNativeWind
├── tailwind.config.js
└── global.css
```

---

## Pre-requisitos

- Node 20+
- Backend Django corriendo en `localhost:8000` (ver `Makefile` en la raíz del repo)
- Para iOS: macOS + Xcode (simulador) **o** la app Expo Go en tu iPhone
- Para Android: Android Studio (emulador) **o** Expo Go en tu Android
- El tenant `clinica-a` ya existe en la base (`admin@clinica-a.com` / `Cl1n1c@Secure2024!`)

---

## Cómo correrlo

### 1) Levantar el backend Django

Desde la raíz del monorepo:

```bash
cd /Users/martin/Desktop/nexosoftdev/agendamiento-saas
python manage.py runserver 0.0.0.0:8000
```

Es importante que escuche en `0.0.0.0` (no `127.0.0.1`) para que el dispositivo físico pueda alcanzarlo.

### 2) Instalar deps (una sola vez)

```bash
cd agendamiento-saas-mobile
npm install --legacy-peer-deps
```

> `--legacy-peer-deps` es necesario por un conflicto de peer entre Nativewind 4 y React 19. Es seguro.

### 3) Arrancar la app

```bash
# Simulador iOS
npm run ios

# Emulador Android
npm run android

# Solo Metro (escanea el QR desde Expo Go)
npm start
```

---

## Configuración: URL del backend y tenant

La app lee 3 valores (en orden de prioridad):

1. Variables de entorno `EXPO_PUBLIC_API_BASE_URL` y `EXPO_PUBLIC_TENANT_SLUG`
2. El bloque `extra` de `app.json`
3. Defaults: `http://localhost:8000` y `clinica-a`

### iOS simulador

`localhost:8000` funciona directamente.

### Android emulador

El código en `src/config/env.ts` **traduce automáticamente** `localhost` → `10.0.2.2` cuando detecta Android (esa es la IP del host visto desde el emulador AVD). No tienes que hacer nada.

### Dispositivo físico (iPhone/Android con Expo Go)

`localhost` no apunta a tu Mac. Necesitas tu IP en la LAN:

```bash
# Encuentra tu IP local
ipconfig getifaddr en0

# Arranca con esa IP
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.42:8000 npm start
```

Y asegúrate de que el backend escucha en `0.0.0.0`, no `127.0.0.1`.

### Cambiar de tenant

```bash
EXPO_PUBLIC_TENANT_SLUG=otra-clinica npm start
```

La app envía el header `X-Tenant-Slug` en todas las requests (ver `apps/tenants/middleware.py:50-53` del backend).

---

## Endpoints consumidos

| Método | Endpoint | Pantalla |
|---|---|---|
| POST | `/rest/v1/user/auth/login/` | `(auth)/login` |
| POST | `/rest/v1/user/auth/register/` | `(auth)/register` |
| POST | `/rest/v1/user/auth/refresh-token/` | Interceptor de Axios (auto) |
| POST | `/rest/v1/user/auth/logout/` | `(tabs)/profile` |
| GET  | `/rest/v1/public/catalog/doctors/` | `(tabs)/index`, `doctor/[id]` |
| GET  | `/rest/v1/public/catalog/services/` | `booking/select-service` |
| GET  | `/rest/v1/public/slots/?doctor=&service=&date=` | `booking/select-slot` |
| POST | `/rest/v1/public/appointments/` | `booking/confirm` |
| GET  | `/rest/v1/bookings/appointments/` | `(tabs)/appointments` |

Todos los contratos están tipados en `src/types/api.ts`. Si cambia un serializer en el backend, actualizar ahí.

---

## Comandos útiles

```bash
# Type-check sin emitir
npx tsc --noEmit

# Verificar que las deps están alineadas a la SDK de Expo
npx expo install --check

# Generar un bundle de producción (validación)
npx expo export --platform ios --output-dir dist
npx expo export --platform android --output-dir dist

# Lint
npm run lint
```

---

## Decisiones técnicas

- **JWT en `expo-secure-store`** (Keychain iOS / Keystore Android). En web cae a AsyncStorage (solo dev).
- **Refresh automático**: el interceptor de respuesta de Axios atrapa 401, intenta refresh, reintenta la request original. Si el refresh falla, limpia storage y el guard del root layout patea al login.
- **Auth gate único** en `app/_layout.tsx` — usa `useSegments()` de expo-router para decidir si redirigir a `(auth)/login` o `(tabs)`.
- **Wizard de booking en Zustand**: la reserva se construye paso a paso (doctor → servicio → fecha → hora → datos), persiste durante la navegación, se resetea al confirmar o salir.
- **Diseño mobile-first**: Tailwind con paleta `brand-*` (índigo). Tipografía system. Touch targets ≥ 44pt.

---

## Próximos pasos sugeridos

- **Push notifications** (`expo-notifications`) para recordatorios — ventaja gratis sobre WhatsApp pagado.
- **Deep linking** desde el correo de confirmación: `agendamiento://booking/{id}`.
- **Modo invitado** (booking sin cuenta) — usar el mismo `POST /public/appointments/` que la app ya hace.
- **EAS Build** para distribuir a TestFlight / Play Internal antes del primer pago.
- Cuando se decida lanzar: app store screenshots, descripción, política de privacidad (la URL aún no la tienes — pendiente con el setup de NexoSoftDev).
