<script setup lang="ts">
const auth = usePlatformAuthStore()
const settings = usePlatformSettingsStore()
const route = useRoute()

usePlatformBranding()

const nav = [
  { label: 'Dashboard', icon: 'i-lucide-layout-dashboard', to: '/' },
  { divider: true, label: 'Plataforma' },
  { label: 'Tenants', icon: 'i-lucide-building-2', to: '/tenants' },
  { label: 'Suscripciones', icon: 'i-lucide-credit-card', to: '/subscriptions' },
  { divider: true, label: 'Catálogo' },
  { label: 'Planes', icon: 'i-lucide-package', to: '/plans' },
  { label: 'Descuentos', icon: 'i-lucide-tag', to: '/discounts' },
  { divider: true, label: 'Configuración' },
  { label: 'Ajustes', icon: 'i-lucide-settings', to: '/ajustes' }
]

async function logout() {
  auth.logout()
  await navigateTo('/login')
}
</script>

<template>
  <UApp>
    <div class="flex h-screen bg-slate-50 overflow-hidden">
      <aside class="w-60 flex-shrink-0 bg-slate-900 text-slate-100 flex flex-col">
        <div class="h-14 flex items-center gap-2 px-4 border-b border-slate-800">
          <div v-if="settings.settings.logo_url" class="w-8 h-8 rounded-lg overflow-hidden flex items-center justify-center bg-white">
            <img :src="settings.settings.logo_url" alt="logo" class="w-full h-full object-contain" @error="($event.target as HTMLImageElement).style.display = 'none'">
          </div>
          <div v-else class="w-8 h-8 rounded-lg bg-primary-500 flex items-center justify-center">
            <UIcon name="i-lucide-shield" class="text-white text-sm" />
          </div>
          <div class="min-w-0">
            <p class="font-semibold text-sm truncate">{{ settings.settings.platform_name }}</p>
            <p class="text-[10px] text-primary-400 font-medium">Super Admin</p>
          </div>
        </div>

        <nav class="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          <template v-for="item in nav" :key="item.label">
            <p
              v-if="item.divider"
              class="px-2 pt-4 pb-1 text-[10px] font-semibold text-slate-500 uppercase tracking-wider"
            >{{ item.label }}</p>
            <UButton
              v-else
              :to="item.to"
              variant="ghost"
              :icon="item.icon"
              class="w-full justify-start text-slate-300 hover:bg-slate-800 hover:text-white"
              :class="route.path === item.to || (item.to !== '/' && route.path.startsWith(item.to))
                ? 'bg-slate-800 text-white' : ''"
            >
              {{ item.label }}
            </UButton>
          </template>
        </nav>

        <div class="p-3 border-t border-slate-800 space-y-1">
          <div class="flex items-center gap-2 px-2 py-1">
            <div class="w-7 h-7 rounded-full bg-primary-500/30 flex items-center justify-center flex-shrink-0">
              <UIcon name="i-lucide-user-round" class="text-primary-300 text-xs" />
            </div>
            <p class="text-xs text-slate-300 truncate flex-1">{{ auth.user?.email }}</p>
          </div>
          <UButton
            variant="ghost"
            icon="i-lucide-log-out"
            class="w-full justify-start text-sm text-slate-400 hover:text-red-300 hover:bg-slate-800"
            @click="logout"
          >Cerrar sesión</UButton>
        </div>
      </aside>

      <div class="flex-1 flex flex-col overflow-hidden">
        <header class="h-14 flex items-center px-6 border-b border-slate-200 bg-white">
          <h1 class="text-sm font-medium text-slate-600">
            Panel de control de la plataforma
          </h1>
        </header>
        <main :key="route.path" class="flex-1 overflow-auto p-6">
          <slot />
        </main>
      </div>
    </div>
  </UApp>
</template>
