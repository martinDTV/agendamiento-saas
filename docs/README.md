# Agendamiento SaaS — Documentación Completa

Sistema de agendamiento médico multi-tenant construido con Django (backend) y Nuxt 4 (frontend monorepo). Permite que múltiples clínicas y doctores independientes tengan su propio portal de reservas, panel de administración, sitio público y portal médico bajo un mismo SaaS, con un panel de plataforma centralizado para gestionar todos los tenants y sus suscripciones.

---

## Índice

1. [Arquitectura general](#arquitectura-general)
2. [Stack tecnológico](#stack-tecnológico)
3. [Estructura del proyecto](#estructura-del-proyecto)
4. [Backend — Django](#backend--django)
5. [Frontend — Monorepo Nuxt 4](#frontend--monorepo-nuxt-4)
6. [Las 4 apps frontend en detalle](#las-4-apps-frontend-en-detalle)
7. [Variables de entorno](#variables-de-entorno)
8. [Cómo correr el proyecto](#cómo-correr-el-proyecto)
9. [API REST — Referencia de endpoints](#api-rest--referencia-de-endpoints)
10. [Modelo multi-tenant](#modelo-multi-tenant)
11. [Separación de auth: Plataforma vs Tenant](#separación-de-auth-plataforma-vs-tenant)
12. [Gestión de suscripciones](#gestión-de-suscripciones)
13. [Flujo de reserva pública](#flujo-de-reserva-pública)
14. [Tareas asíncronas (Celery)](#tareas-asíncronas-celery)
15. [Inteligencia artificial (Ollama)](#inteligencia-artificial-ollama)
16. [Tests](#tests)

---

## Arquitectura general

```
Internet
   │
   ├── miapp.com                    → Marketing (Nuxt, puerto 3000)
   ├── platform.miapp.com           → Panel de plataforma / Super-admin (Nuxt, puerto 3004)
   ├── {slug}.miapp.com             → Sitio público de reservas (Nuxt, puerto 3001)
   ├── admin.{slug}.miapp.com       → Panel admin del tenant (Nuxt, puerto 3002)
   │
   └── api.miapp.com                → Django REST API (puerto 8000)
                                          │
                                          ├── PostgreSQL  (datos)
                                          ├── Redis       (caché + Celery broker)
                                          └── Ollama      (IA local)
```

Cada tenant (clínica / doctor independiente) tiene su propio subdominio. El backend es **shared-schema** — todos los tenants comparten la misma base de datos con aislamiento a nivel de query mediante un campo `tenant` en cada modelo.

El **panel de plataforma** (`platform.miapp.com`) es una superficie aparte: gestiona todos los tenants, planes, suscripciones y descuentos. Los superusuarios solo pueden entrar ahí; los admins de tenant solo pueden entrar a su `admin.{slug}.miapp.com`. **No comparten sesión ni hay overlap.**

---

## Stack tecnológico

### Backend
| Tecnología | Versión | Uso |
|---|---|---|
| Python | 3.12 | Lenguaje (conda env: `agendamiento-saas`) |
| Django | 5.2.1 | Framework web |
| Django REST Framework | 3.16 | API REST |
| SimpleJWT | 5.5 | Autenticación JWT |
| `django-users-auth` | 2.4 | Lib propia — `email` como USERNAME_FIELD |
| `mozilla-django-oidc` | — | OIDC (no eliminar) |
| Celery + Beat | 5.4 / 2.8 | Tareas asíncronas y programadas |
| Redis | 5.0 | Broker Celery + caché |
| PostgreSQL | — | Base de datos principal |
| httpx | 0.28 | Cliente HTTP para Ollama |
| django-cors-headers | 4.7 | CORS |

### Frontend
| Tecnología | Versión | Uso |
|---|---|---|
| Nuxt | 4.4.4 | Framework SSR/SPA |
| Vue | 3.5 | UI |
| `@nuxt/ui` | 4.7 | Componentes (UButton, UCard, UModal, etc.) |
| Pinia | 3.0 | State management |
| Axios | 1.16 | Cliente HTTP |
| `vee-validate` + `zod` | 4.15 / 3.25 | Validación de formularios |
| TailwindCSS | 4.2 | Estilos |
| pnpm workspaces | 10.x | Monorepo |

---

## Estructura del proyecto

```
agendamiento-saas/                     ← Raíz del backend
├── manage.py
├── requirements.txt
├── pytest.ini                         ← Usa core.test_settings
├── .env / .env.example
├── docs/
│   └── README.md                      ← Este archivo
│
├── core/                              ← Configuración Django
│   ├── settings.py
│   ├── test_settings.py               ← Throttle off para tests
│   ├── celery.py                      ← Config Celery + BEAT_SCHEDULE
│   └── urls.py
│
├── apirest/
│   └── urls.py                        ← Rutas /rest/v1/ + wrapper login (rechaza superuser)
│
├── shared/                            ← Código compartido
│   ├── models.py                      ← TenantScopedModel, TenantManager
│   ├── viewsets.py                    ← TenantScopedViewSet
│   ├── pagination.py                  ← StandardPagination
│   └── throttles.py                   ← BookingCreateThrottle, SlotsThrottle
│
└── apps/
    ├── tenants/                       ← Tenant + middleware + resolución
    ├── accounts/                      ← Memberships, invitaciones, /me
    ├── catalog/                       ← Branch, Doctor, Service, Schedule
    ├── bookings/                      ← Appointment (con expediente clínico)
    ├── notifications/                 ← Emails de confirmación / recordatorio
    ├── reports/                       ← Reportes de citas
    ├── ai/                            ← Sugerencia de servicios (Ollama)
    ├── meetings/                      ← Sala de consulta (telemedicina)
    └── platform/                      ← ★ Plan, Subscription, Discount + endpoints super-admin

agendamiento-saas-frontend/            ← Monorepo Nuxt
├── package.json                       ← Scripts dev:marketing | dev:public | dev:admin | dev:platform
├── pnpm-workspace.yaml
├── packages/
│   └── shared/                        ← Tipos TS compartidos (@agendamiento/shared)
│       └── types/{auth,catalog,booking,tenant}.ts
│
└── apps/
    ├── marketing/                     ← Landing pública (puerto 3000)
    ├── public/                        ← Wizard de reservas paciente (puerto 3001)
    ├── admin/                         ← Panel del tenant (puerto 3002)
    └── platform/                      ← ★ Panel super-admin de la plataforma (puerto 3004)
```

---

## Backend — Django

### Apps y su responsabilidad

#### `apps/tenants`
- `Tenant`: slug, name, type (`solo`/`clinic`), plan (string legacy), settings (JSON con branding/timezone), custom_domain, is_active
- `TenantMiddleware`: resuelve tenant desde Host header. Fallback: header `X-Tenant-Slug` (SSR Nuxt y tests)
- Endpoints: `GET /tenants/resolve/{slug}/` (público, SSR), `GET/PATCH /tenants/me/` (owner/admin)

#### `apps/accounts`
- `Membership`: relación User ↔ Tenant con rol (`owner`/`admin`/`doctor`/`staff`)
- `InvitationToken`: invitaciones por email (expiran a 7 días)
- Permissions: `IsTenantMember`, `IsTenantDoctorOrAbove`, `IsTenantAdminOrOwner`, `IsTenantOwner`

#### `apps/catalog`
- `Branch`: sucursal
- `Doctor`: vinculado a User, especialidad, bio, duración predeterminada
- `Service`: servicio con duración, precio, color
- `Schedule`: horario semanal del doctor

`DoctorViewSet.create()` puede crear User + Membership + Doctor en una sola llamada.
Tiene action `me` (`GET /catalog/doctors/me/`) que devuelve el perfil del doctor autenticado.

#### `apps/bookings`
- `Appointment` con dos partes:
  - **Reserva:** doctor, servicio, paciente, fecha/hora, status (`pending`/`confirmed`/`cancelled`/`completed`), `notes` (notas internas)
  - **Expediente clínico** (lo llena el doctor durante/post consulta): `clinical_notes`, `weight_kg`, `height_cm`, `blood_pressure`, `heart_rate`, `temperature_c`, `oxygen_sat`
- `slots.py`: algoritmo que genera slots disponibles desde Schedule, descontando citas activas
- Permission: cualquier `IsTenantMember` puede leer y editar; en `get_queryset` los doctores ven solo sus propias citas
- Endpoints públicos (sin auth): `/public/slots/`, `/public/appointments/`
- Endpoints admin: `/bookings/appointments/` (filtros: `date`, `from_date`, `to_date`, `doctor`, `status`)

#### `apps/notifications`
- `task_send_confirmation`: email al crear cita
- `task_send_reminders`: tarea Beat cada 24 h, recordatorios para citas del día siguiente

#### `apps/reports`
- `GET /reports/appointments/?from_date=&to_date=`: total, por status, top doctores, top servicios

#### `apps/ai`
- `POST /public/ai/suggest/` con `{ "reason": "..." }` → IDs de servicios sugeridos
- Configurable: `OLLAMA_BASE_URL`, `OLLAMA_MODEL_TEXT`, `OLLAMA_TIMEOUT`
- Si Ollama no responde, devuelve `{ service_ids: [] }` sin romper

#### `apps/meetings`
- Salas de consulta (telemedicina) — endpoints en `/meetings/`

#### `apps/platform` ★
Panel de plataforma — solo accesible para `is_superuser=True`.

**Modelos:**
- `Plan`: nombre, slug, descripción, `price_monthly`, `price_yearly`, currency, `max_doctors`, `max_appointments_per_month`, `max_branches` (0 = ilimitado), `features` (JSON list), `is_active`, `is_public`, `sort_order`
- `Subscription`: `tenant` (OneToOne), `plan` (FK), `status` (`trial`/`active`/`past_due`/`canceled`/`suspended`), `billing_cycle` (`monthly`/`yearly`), `discount` (FK opcional), `started_at`, `current_period_end`, `trial_ends_at`, `canceled_at`, `notes`
- `Discount`: `code`, `description`, `discount_type` (`percent`/`fixed`), `value`, `applicable_plans` (M2M, vacío = todos), `valid_from`, `valid_until`, `max_uses`, `times_used`, `is_active`

**Endpoints (todos requieren `IsPlatformAdmin`):**
- `POST /platform/auth/login/` — rechaza no-superusers (403)
- `GET  /platform/auth/me/`
- `GET  /platform/dashboard/` — KPIs globales (MRR, ARR, conteos, distribución por plan)
- CRUD: `/platform/tenants/`, `/platform/plans/`, `/platform/subscriptions/`, `/platform/discounts/`

### Modelo multi-tenant (shared schema)

Todos los modelos de negocio heredan de `TenantScopedModel`:
```python
class TenantScopedModel(models.Model):
    tenant = ForeignKey(Tenant, ...)
    objects = TenantManager()    # filtra automáticamente por tenant
    _all = UnscopedManager()     # sin filtro (para tasks/admin)
```

`TenantScopedViewSet` inyecta el tenant en `perform_create` y filtra el queryset.

Los modelos del panel **`platform`** NO son tenant-scoped: `Plan`, `Subscription`, `Discount` son globales (vista global de toda la plataforma).

---

## Frontend — Monorepo Nuxt 4

### Scripts del workspace (desde `agendamiento-saas-frontend/`)
```bash
pnpm dev:marketing   # Marketing en puerto 3000
pnpm dev:public      # Sitio público de reservas en puerto 3001
pnpm dev:admin       # Panel admin del tenant en puerto 3002
pnpm dev:platform    # ★ Panel super-admin en puerto 3004
pnpm build:all       # Build de todas las apps
```

### Resolución de tenant en SSR (apps `public` y `admin`)
1. Plugin `tenant.server.ts` corre en Node de Nuxt al recibir cada request
2. Extrae el slug del Host header:
   - `clinica-a.miapp.com` → `clinica-a` (public)
   - `admin.clinica-a.miapp.com` → `clinica-a` (admin)
3. `GET /tenants/resolve/{slug}/` en Django
4. Hidrata el Pinia store
5. Middleware `tenant.ts` lanza 404 si el store no quedó cargado

Para dev local sin subdominio: variable `NUXT_TENANT_SLUG` en el `.env` del app.

> El panel **platform** NO usa resolución de tenant — es global y solo se accede en `localhost:3004` o `platform.miapp.com`.

### Autenticación
- **Tenant apps (admin/public):** JWT (access + refresh) en `localStorage` con keys `auth:access` / `auth:refresh`
- **Platform app:** JWT en `localStorage` con keys diferentes: `platform:access` / `platform:refresh` — sesiones independientes

---

## Las 4 apps frontend en detalle

### 1. `apps/marketing/` — puerto 3000
Landing page pública del SaaS. Sin auth, sin resolución de tenant. Es solo HTML/CSS para captar leads.

### 2. `apps/public/` — puerto 3001
Sitio de reservas para pacientes. Acceso por subdominio del tenant (`{slug}.miapp.com`).
- **Wizard de 6 pasos:** doctor → servicio → fecha → slot → datos → confirmación
- Sin auth (paciente anónimo)
- Tenant resuelto vía Host header en SSR

### 3. `apps/admin/` — puerto 3002
Panel del tenant. Acceso por `admin.{slug}.miapp.com`. Login JWT con email/password.

**Páginas:**
| Ruta | Descripción |
|---|---|
| `/login` | Login del tenant (rechaza superusers) |
| `/` | Dashboard con KPIs y citas de hoy |
| `/agenda` | Calendario semanal |
| `/citas` | Tabla de citas con filtros (fecha, status) |
| `/branches` | CRUD de sucursales |
| `/doctors` | CRUD de doctores (incluye crear User + Membership) |
| `/doctors/{id}/schedules` | Horarios del doctor |
| `/services` | CRUD de servicios |
| `/equipo` | Miembros e invitaciones |
| `/ajustes` | Nombre, timezone, color de branding |
| `/reports` | Reportes por período |

**Componentes:** `BranchModal`, `DoctorModal`, `ServiceModal`

**Roles que pueden entrar:** `owner`, `admin`, `doctor`, `staff` (todos los miembros del tenant). El backend filtra qué ve cada rol — los doctores ven solo sus propias citas.

### 4. `apps/platform/` ★ — puerto 3004
Panel de **super-administración** de la plataforma. Acceso por `platform.miapp.com`.

**Características distintivas:**
- **Sin tenant** — es global, no hay subdominio de tenant
- **localStorage keys distintas** (`platform:access`, `platform:refresh`)
- **Solo accesible para `is_superuser=True`** — el endpoint de login rechaza a cualquier otro usuario con 403
- Diseño visual **dark sidebar** para diferenciarlo del admin de tenant

**Páginas:**
| Ruta | Descripción |
|---|---|
| `/login` | Login solo para superusers |
| `/` | Dashboard con MRR, ARR, KPIs globales y distribución por plan |
| `/tenants` | Lista de todos los tenants con buscador, plan y status de suscripción |
| `/tenants/{id}` | Detalle: editar tenant + crear/modificar suscripción (cambiar plan, status, ciclo, descuento) |
| `/plans` | CRUD de planes con cards (nombre, precio mensual/anual, límites, features) |
| `/discounts` | CRUD de códigos de descuento con planes aplicables, vigencia, usos |
| `/subscriptions` | Lista global de suscripciones con filtro por status |

---

## Variables de entorno

### Backend (`agendamiento-saas/.env`)
```env
SECRET_KEY=...
SECRET_KEY_LOCAL=...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,.miapp.com

DATABASE_URL=postgresql://martin:1234@localhost:5432/agendamiento-saas
REDIS_URL=redis://127.0.0.1:6379/1
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
DEFAULT_FROM_EMAIL=noreply@miapp.com

PLATFORM_DOMAIN=miapp.com
CORS_ALLOW_ALL_ORIGINS=True

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_TEXT=gemma2:9b
OLLAMA_TIMEOUT=10
```

### Frontend Admin (`agendamiento-saas-frontend/apps/admin/.env`)
```env
NUXT_PUBLIC_API_BASE=http://localhost:8000/rest/v1
NUXT_PUBLIC_PLATFORM_DOMAIN=miapp.com
NUXT_TENANT_SLUG=clinica-a   # fallback para dev local
```

### Frontend Public (`agendamiento-saas-frontend/apps/public/.env`)
```env
NUXT_PUBLIC_API_BASE=http://localhost:8000/rest/v1
NUXT_PUBLIC_PLATFORM_DOMAIN=miapp.com
```

### Frontend Platform (`agendamiento-saas-frontend/apps/platform/.env`)
```env
NUXT_PUBLIC_API_BASE=http://localhost:8000/rest/v1
# No requiere PLATFORM_DOMAIN ni TENANT_SLUG — es global
```

---

## Cómo correr el proyecto

### Requisitos previos
- Python 3.12 + conda (entorno `agendamiento-saas`)
- Node.js 20+ + pnpm 10+
- PostgreSQL corriendo
- Redis corriendo (`redis-server`)
- (opcional) Ollama (`ollama serve`)

### 1. Backend

```bash
cd ~/Desktop/nexosoftdev/agendamiento-saas
conda activate agendamiento-saas

# Primera vez
pip install -r requirements.txt
python manage.py migrate

# Crear un superuser para acceder al panel /platform
python manage.py createsuperuser

# Correr Django
python manage.py runserver   # → http://localhost:8000
```

### 2. Celery (notificaciones por email)

```bash
cd ~/Desktop/nexosoftdev/agendamiento-saas
conda activate agendamiento-saas

# Worker
celery -A core worker -l info

# Beat (recordatorios cada 24 h)
celery -A core beat -l info
```

### 3. Frontend

```bash
cd ~/Desktop/nexosoftdev/agendamiento-saas/agendamiento-saas-frontend

# Primera vez
pnpm install

# Cualquier app (cada una en su propia terminal):
pnpm dev:marketing    # → http://localhost:3000
pnpm dev:public       # → http://{slug}.miapp.com:3001
pnpm dev:admin        # → http://localhost:3002 (con NUXT_TENANT_SLUG)
pnpm dev:platform     # → http://localhost:3004
```

### 4. /etc/hosts para subdominios (dev)

```bash
echo "127.0.0.1  clinica-a.miapp.com"        | sudo tee -a /etc/hosts
echo "127.0.0.1  admin.clinica-a.miapp.com"  | sudo tee -a /etc/hosts
echo "127.0.0.1  platform.miapp.com"         | sudo tee -a /etc/hosts
```

### 5. Crear el primer tenant

```bash
curl -X POST http://localhost:8000/rest/v1/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "Mi Clínica",
    "tenant_slug": "mi-clinica",
    "tenant_type": "clinic",
    "email": "admin@mi-clinica.com",
    "password": "MiPassword123!",
    "first_name": "Admin"
  }'
```

### 6. Tenant de desarrollo predefinido
- Slug: `clinica-a`
- Email: `admin@clinica-a.com`
- Pass: `Cl1n1c@Secure2024!`

---

## API REST — Referencia de endpoints

Base URL: `http://localhost:8000/rest/v1/`

### Auth (tenant)
| Método | Endpoint | Descripción |
|---|---|---|
| POST | `user/auth/login/` | Login → access + refresh tokens. **Rechaza superusers (403).** |
| POST | `user/auth/refresh-token/` | Renovar access |
| POST | `user/auth/logout/` | Blacklist refresh |
| POST | `accounts/register/` | Crear tenant + owner en un paso |

### Auth (platform / super-admin) ★
| Método | Endpoint | Descripción |
|---|---|---|
| POST | `platform/auth/login/` | Login solo para `is_superuser=True`. Rechaza tenant users (403). |
| GET | `platform/auth/me/` | Datos del platform admin actual |

### Tenant
| Método | Endpoint | Auth | Descripción |
|---|---|---|---|
| GET | `tenants/resolve/{slug}/` | No | Resolve por slug (SSR Nuxt) |
| GET | `tenants/me/` | Admin/Owner | Info del tenant actual |
| PATCH | `tenants/me/` | Admin/Owner | Actualizar nombre y settings |

### Platform — gestión global ★ (todos requieren `IsPlatformAdmin`)
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `platform/dashboard/` | KPIs globales (MRR, ARR, conteos, distribución) |
| GET/POST | `platform/tenants/` | CRUD global de tenants (con suscripción anidada) |
| GET/PATCH/DELETE | `platform/tenants/{id}/` | — |
| GET/POST | `platform/plans/` | CRUD de planes |
| GET/PATCH/DELETE | `platform/plans/{id}/` | — |
| GET/POST | `platform/subscriptions/` | CRUD de suscripciones |
| GET/PATCH/DELETE | `platform/subscriptions/{id}/` | — |
| GET/POST | `platform/discounts/` | CRUD de códigos de descuento |
| GET/PATCH/DELETE | `platform/discounts/{id}/` | — |

### Equipo (admin del tenant)
| Método | Endpoint | Auth | Descripción |
|---|---|---|---|
| GET | `accounts/me/` | Sí | Usuario actual + memberships |
| GET | `accounts/memberships/` | Admin | Listar miembros del tenant |
| PATCH | `accounts/memberships/{id}/` | Admin | Cambiar rol / desactivar |
| POST | `accounts/invitations/` | Admin | Invitar nuevo miembro |
| GET | `accounts/invitations/` | Admin | Pendientes |
| POST | `accounts/invitations/accept/{token}/` | No | Aceptar |

### Catálogo (admin)
| Método | Endpoint | Descripción |
|---|---|---|
| GET/POST | `catalog/branches/` | Sucursales |
| GET/PATCH/DELETE | `catalog/branches/{id}/` | — |
| GET/POST | `catalog/doctors/` | Doctores (POST también crea User + Membership) |
| GET | `catalog/doctors/me/` | Perfil del doctor autenticado |
| GET/PATCH/DELETE | `catalog/doctors/{id}/` | — |
| GET/POST | `catalog/services/` | Servicios |
| GET/POST | `catalog/schedules/` | Horarios (filtro: `?doctor={id}`) |
| PATCH/DELETE | `catalog/schedules/{id}/` | — |

### Reservas (admin / doctor)
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `bookings/appointments/` | Citas (filtros: `date`, `from_date`, `to_date`, `doctor`, `status`). Doctores ven solo las propias. |
| PATCH | `bookings/appointments/{id}/` | Actualizar status, notes, expediente clínico |

### Públicos (sin auth, requieren tenant en host o `X-Tenant-Slug`)
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `public/catalog/doctors/` | Doctores activos |
| GET | `public/catalog/services/` | Servicios activos |
| GET | `public/slots/?doctor=&service=&date=` | Slots disponibles |
| POST | `public/appointments/` | Crear cita |
| POST | `public/ai/suggest/` | Sugerir servicios por motivo |

### Reportes
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `reports/appointments/?from_date=&to_date=` | Métricas |

### Otros
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `health/` | Health check |
| GET | `meetings/...` | Salas de consulta |

---

## Modelo multi-tenant

```
Tenant
  ├── Membership (User × Tenant × Role)
  ├── Branch
  ├── Doctor (linked to User)
  │     └── Schedule (weekday + start_time + end_time)
  ├── Service
  └── Appointment (Doctor + Service + Patient + Clinical record)
```

**Aislamiento:** todos estos modelos heredan de `TenantScopedModel`. El `TenantManager.for_tenant(t)` filtra automáticamente por el tenant activo. El middleware `TenantMiddleware` resuelve `request.tenant` desde el host header en cada request.

**Modelos globales (no tenant-scoped):** `User`, `Plan`, `Subscription`, `Discount` — viven a nivel plataforma.

---

## Separación de auth: Plataforma vs Tenant

Hay **dos sistemas de auth completamente separados** que comparten la tabla `User` pero NO comparten endpoints ni sesiones:

### Tenant users (admin de clínica, doctor, staff)
- Login: `POST /rest/v1/user/auth/login/`
- **Si `is_superuser=True` → rechazado con 403** (wrapper `TenantAuthTokenViewset` en `apirest/urls.py`)
- Tokens en `localStorage` con keys `auth:access` / `auth:refresh`
- Acceso a: `apps/admin`, `apps/public`
- Filtros por tenant en cada query (Membership)

### Platform users (super-admin)
- Login: `POST /rest/v1/platform/auth/login/`
- **Si `is_superuser=False` → rechazado con 403**
- Tokens en `localStorage` con keys `platform:access` / `platform:refresh`
- Acceso a: `apps/platform` solamente
- Permission `IsPlatformAdmin` en TODOS los endpoints `/platform/*`

### Reglas de coexistencia
- Un superuser **NO puede** entrar a ningún panel de tenant.
- Un tenant admin **NO puede** entrar al panel de plataforma.
- Si necesitas ambos accesos, crea **dos cuentas separadas** (recomendado).
- Las sesiones son completamente independientes — puedes tener ambas tabs abiertas a la vez sin conflicto.

---

## Gestión de suscripciones

Las suscripciones viven en `apps.platform`. El flujo típico:

1. **Crear planes** desde `/platform/plans/`
   - Define precios mensual/anual, límites (`max_doctors`, `max_appointments_per_month`, `max_branches` — 0 = ilimitado), features
   - Marca `is_public=true` si quiere que aparezca en marketing

2. **Asignar suscripción a tenant** desde `/platform/tenants/{id}/`
   - Eligen plan, status (`trial`/`active`/...), ciclo (`monthly`/`yearly`), fecha de fin de período
   - Opcional: aplicar `Discount`

3. **Crear códigos de descuento** desde `/platform/discounts/`
   - `discount_type`: `percent` (ej. 20%) o `fixed` (ej. 500 MXN)
   - Opcional: limitar a planes específicos, vigencia, usos máximos

4. **Dashboard** muestra MRR (suma de `price_monthly` de suscripciones activas), ARR, distribución por plan, conteos por status.

> **Nota:** el `Tenant.plan` (string legacy) sigue existiendo pero es independiente de la `Subscription`. La fuente de verdad para el plan/billing es `Subscription`.

---

## Flujo de reserva pública

```
Paciente visita {slug}.miapp.com
        ↓
1. Selecciona doctor
2. Selecciona servicio (con sugerencia opcional de IA)
3. Selecciona fecha
4. Selecciona slot disponible (slots.py)
5. Ingresa nombre, email, teléfono
6. POST /public/appointments/ → Appointment (status: pending)
        ↓
Celery dispara task_send_confirmation
        ↓
Paciente recibe email
```

Más tarde, el doctor entra al admin, ve la cita y al completar la consulta llena el **expediente clínico**: `clinical_notes`, signos vitales (`weight_kg`, `height_cm`, `blood_pressure`, `heart_rate`, `temperature_c`, `oxygen_sat`).

---

## Tareas asíncronas (Celery)

| Task | Trigger | Descripción |
|---|---|---|
| `task_send_confirmation` | Al crear cita | Email de confirmación al paciente |
| `task_send_reminders` | Cada 24 h (Beat) | Recordatorios para citas del día siguiente |

```bash
celery -A core worker -l info    # terminal 1
celery -A core beat -l info      # terminal 2
```

`CELERY_BEAT_SCHEDULE` está registrado en `core/settings.py`.

---

## Inteligencia artificial (Ollama)

`POST /public/ai/suggest/` con `{ "reason": "..." }` devuelve los IDs de los servicios más relevantes del tenant para ese motivo de consulta.

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_TEXT=gemma2:9b
OLLAMA_TIMEOUT=10
```

```bash
# Instalar Ollama (https://ollama.ai)
ollama pull gemma2:9b
ollama serve
```

Si Ollama no responde, el endpoint devuelve `{ service_ids: [] }` sin romper.

---

## Tests

```bash
cd ~/Desktop/nexosoftdev/agendamiento-saas
conda activate agendamiento-saas

python -m pytest          # corre todos los tests
python -m pytest -v       # con detalle
python -m pytest apps/bookings/   # solo un módulo
```

Los tests usan `core.test_settings` (configurado en `pytest.ini`) que deshabilita el throttling para evitar falsos 429.

---

## Tips de desarrollo

- **El admin se traba al navegar** — `:key="route.path"` en `<main>` de `layouts/default.vue` (admin y platform)
- **Logout al refrescar** — el middleware `auth.ts` hace `if (import.meta.server) return`; los tokens viven en `localStorage`
- **Vite IPC error en Nuxt 4** — si pasa con `ssr: false`, cambiar a `ssr: true` (los plugins client-only siguen funcionando bien)
- **NUNCA eliminar** `django-users-auth` ni `mozilla-django-oidc`
- **Frontend SIEMPRE** en `agendamiento-saas/agendamiento-saas-frontend/`
- **Throttles deshabilitados en tests** — `core.test_settings` los pone en `10000/hour`
