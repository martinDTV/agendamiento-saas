<script setup lang="ts">
definePageMeta({ middleware: ['tenant', 'auth'] })

const { apiFetch } = useApi()

interface SupportAgent {
  user_id: number
  email: string
  full_name: string
  role: string
  is_online: boolean
  total_conversations: number
  open_conversations: number
  closed_conversations: number
  last_active: string | null
}

const agents = ref<SupportAgent[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await apiFetch<SupportAgent[] | { results: SupportAgent[] }>('/support/agents/')
    agents.value = Array.isArray(res) ? res : res.results
  } finally {
    loading.value = false
  }
}

const ROLE_LABEL: Record<string, string> = {
  owner: 'Propietario',
  admin: 'Admin',
  support: 'Soporte'
}

const ROLE_COLOR: Record<string, string> = {
  owner: 'bg-purple-100 text-purple-700 ring-purple-200',
  admin: 'bg-blue-100 text-blue-700 ring-blue-200',
  support: 'bg-orange-100 text-orange-700 ring-orange-200'
}

function formatLastActive(iso: string | null): string {
  if (!iso) return 'Sin actividad'
  const diff = Date.now() - new Date(iso).getTime()
  if (diff < 60000) return 'Hace instantes'
  if (diff < 3600000) return `Hace ${Math.floor(diff / 60000)} min`
  if (diff < 86400000) return `Hace ${Math.floor(diff / 3600000)} h`
  return new Date(iso).toLocaleDateString('es-MX', { day: 'numeric', month: 'short' })
}

onMounted(load)
</script>

<template>
  <div class="space-y-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-900 dark:text-white">Agentes de soporte</h1>
        <p class="text-sm text-slate-400 mt-0.5">{{ agents.length }} agentes asignados a este tenant</p>
      </div>
      <div class="flex gap-2">
        <UButton variant="ghost" icon="i-lucide-refresh-cw" size="sm" @click="load">Actualizar</UButton>
        <UButton variant="outline" to="/soporte" icon="i-lucide-inbox">
          Ver bandeja
        </UButton>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center py-16">
      <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl text-violet-500" />
    </div>

    <div v-else-if="agents.length === 0" class="bg-white rounded-2xl border border-slate-200 p-16 text-center">
      <UIcon name="i-lucide-users" class="w-12 h-12 text-slate-300 mx-auto mb-3" />
      <p class="text-sm text-slate-400">No hay agentes asignados.</p>
      <p class="text-xs text-slate-400 mt-1">Invitá miembros con rol "Soporte" desde Equipo.</p>
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <NuxtLink
        v-for="agent in agents"
        :key="agent.user_id"
        :to="`/soporte/agentes/${agent.user_id}`"
        class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 hover:shadow-md hover:border-violet-300 transition-all"
      >
        <div class="flex items-start justify-between mb-3">
          <div class="w-12 h-12 rounded-full bg-violet-100 flex items-center justify-center text-lg font-bold text-violet-700 uppercase">
            {{ agent.full_name[0] }}
          </div>
          <span
            class="text-[10px] font-medium px-2 py-1 rounded ring-1 inline-flex items-center gap-1"
            :class="agent.is_online
              ? 'bg-emerald-100 text-emerald-700 ring-emerald-200'
              : 'bg-slate-100 text-slate-500 ring-slate-200'"
          >
            <span class="w-1.5 h-1.5 rounded-full" :class="agent.is_online ? 'bg-emerald-500' : 'bg-slate-400'" />
            {{ agent.is_online ? 'En línea' : 'Offline' }}
          </span>
        </div>

        <p class="font-semibold text-slate-800 dark:text-slate-100 truncate">{{ agent.full_name }}</p>
        <p class="text-xs text-slate-400 mt-0.5 truncate">{{ agent.email }}</p>

        <span
          class="inline-block mt-2 text-[10px] font-medium px-2 py-0.5 rounded ring-1"
          :class="ROLE_COLOR[agent.role] ?? 'bg-slate-100 text-slate-500 ring-slate-200'"
        >
          {{ ROLE_LABEL[agent.role] ?? agent.role }}
        </span>

        <div class="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 grid grid-cols-3 gap-2">
          <div>
            <p class="text-lg font-bold text-slate-800">{{ agent.total_conversations }}</p>
            <p class="text-[10px] text-slate-400 uppercase tracking-wide">Total</p>
          </div>
          <div>
            <p class="text-lg font-bold text-emerald-600">{{ agent.open_conversations }}</p>
            <p class="text-[10px] text-slate-400 uppercase tracking-wide">Abiertas</p>
          </div>
          <div>
            <p class="text-lg font-bold text-slate-500">{{ agent.closed_conversations }}</p>
            <p class="text-[10px] text-slate-400 uppercase tracking-wide">Cerradas</p>
          </div>
        </div>

        <p class="text-[11px] text-slate-400 mt-3">
          <UIcon name="i-lucide-clock" class="w-3 h-3 inline -mt-0.5" />
          {{ formatLastActive(agent.last_active) }}
        </p>
      </NuxtLink>
    </div>
  </div>
</template>
