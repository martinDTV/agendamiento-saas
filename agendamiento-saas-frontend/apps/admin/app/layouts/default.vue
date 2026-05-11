<script setup lang="ts">
const auth = useAuthStore()
const tenant = useTenantStore()
const { isAdmin, isDoctor } = useRole()

useBranding()

const router = useRouter()
const currentPath = computed(() => router.currentRoute.value.path)

type NavItem = { label: string; icon?: string; to?: string; divider?: boolean; admin?: boolean }

const allNav: NavItem[] = [
  { label: 'Inicio',     icon: 'i-lucide-home',           to: '/' },
  { label: 'Agenda',     icon: 'i-lucide-calendar-days',  to: '/agenda' },
  { label: 'Citas',      icon: 'i-lucide-clock',          to: '/citas' },
  { label: 'Juntas',     icon: 'i-lucide-video',          to: '/juntas' },
  { divider: true, label: 'Catálogo', admin: true },
  { label: 'Sucursales', icon: 'i-lucide-building-2',     to: '/branches', admin: true },
  { label: 'Doctores',   icon: 'i-lucide-user-round',     to: '/doctors',  admin: true },
  { label: 'Servicios',  icon: 'i-lucide-clipboard-list', to: '/services', admin: true },
  { label: 'Salas',      icon: 'i-lucide-door-open',      to: '/salas',    admin: true },
  { divider: true, label: 'Análisis', admin: true },
  { label: 'Reportes',   icon: 'i-lucide-bar-chart-2',    to: '/reports',  admin: true },
  { divider: true, label: 'Atención al cliente' },
  { label: 'Soporte',    icon: 'i-lucide-message-circle', to: '/soporte' },
  { label: 'Agentes',    icon: 'i-lucide-users-round',    to: '/soporte/agentes', admin: true },
  { divider: true, label: 'Configuración' },
  { label: 'Equipo',     icon: 'i-lucide-users',          to: '/equipo',   admin: true },
  { label: 'Ajustes',    icon: 'i-lucide-settings',       to: '/ajustes' }
]

const nav = computed(() => allNav.filter(i => !i.admin || isAdmin.value))

const pageTitle = computed(() => {
  const found = nav.value.filter(n => !n.divider).find(n => n.to === currentPath.value)
  return found?.label ?? 'Panel de administración'
})

const dateLabel = computed(() =>
  new Date().toLocaleDateString('es-MX', { weekday: 'long', day: 'numeric', month: 'long' })
)

async function logout() {
  auth.logout()
  await navigateTo('/login')
}
</script>

<template>
  <UApp>
    <div class="flex h-screen bg-slate-50 dark:bg-slate-950 overflow-hidden">
      <!-- Sidebar -->
      <aside class="w-60 flex-shrink-0 bg-slate-900 flex flex-col">
        <!-- Brand -->
        <div class="h-16 flex items-center gap-3 px-4 border-b border-slate-800">
          <div class="w-8 h-8 rounded-xl bg-sage-600 flex items-center justify-center flex-shrink-0 shadow-lg shadow-sage-900/50">
            <UIcon name="i-lucide-calendar-heart" class="text-white text-sm" />
          </div>
          <div class="min-w-0">
            <p class="font-semibold text-sm text-white truncate leading-tight">
              {{ tenant.tenant?.name ?? '…' }}
            </p>
            <p class="text-[11px] text-slate-400 capitalize">{{ tenant.tenant?.plan }}</p>
          </div>
        </div>

        <!-- Nav -->
        <nav class="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          <template v-for="item in nav" :key="item.label">
            <p
              v-if="item.divider"
              class="px-3 pt-5 pb-1.5 text-[10px] font-semibold text-slate-500 uppercase tracking-widest"
            >
              {{ item.label }}
            </p>
            <NuxtLink
              v-else
              :to="item.to"
              class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150"
              :class="currentPath === item.to
                ? 'bg-sage-600 text-white shadow-sm'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'"
            >
              <UIcon :name="item.icon" class="flex-shrink-0 w-4 h-4" />
              {{ item.label }}
            </NuxtLink>
          </template>
        </nav>

        <!-- User footer -->
        <div class="p-3 border-t border-slate-800">
          <div class="flex items-center gap-2.5 px-2 py-2 mb-1">
            <div class="w-6 h-6 rounded-full bg-sage-700 flex items-center justify-center flex-shrink-0">
              <span class="text-[10px] font-bold text-white uppercase">
                {{ (auth.user?.email ?? 'U')[0] }}
              </span>
            </div>
            <p class="text-xs text-slate-400 truncate flex-1">
              {{ auth.user?.email }}
            </p>
          </div>
          <button
            class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium text-slate-500 hover:bg-slate-800 hover:text-red-400 transition-all duration-150"
            @click="logout"
          >
            <UIcon name="i-lucide-log-out" class="flex-shrink-0 w-4 h-4" />
            Cerrar sesión
          </button>
        </div>
      </aside>

      <!-- Main -->
      <div class="flex-1 flex flex-col overflow-hidden">
        <header class="h-16 flex items-center px-6 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <div>
            <h1 class="text-base font-semibold text-slate-800 dark:text-slate-100">
              {{ pageTitle }}
            </h1>
            <p class="text-xs text-slate-400 capitalize">{{ dateLabel }}</p>
          </div>
          <div class="ml-auto flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-sage-100 dark:bg-sage-900/40 flex items-center justify-center">
              <span class="text-xs font-bold text-sage-700 dark:text-sage-300 uppercase">
                {{ (auth.user?.email ?? 'U')[0] }}
              </span>
            </div>
          </div>
        </header>
        <main class="flex-1 overflow-auto p-6">
          <slot />
        </main>
      </div>
    </div>
  </UApp>
</template>
