<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const { apiFetch } = useApi()

interface TenantPlatform {
  id: string
  slug: string
  name: string
  type: string
  plan: string
  plan_display: string | null
  is_active: boolean
  created_at: string
  member_count: number
  subscription: null | {
    id: number
    plan_name: string
    status: string
    billing_cycle: string
    current_period_end: string
  }
}

const tenants = ref<TenantPlatform[]>([])
const loading = ref(false)
const search = ref('')
const showNewModal = ref(false)

async function load() {
  loading.value = true
  try {
    const params: Record<string, string> = {}
    if (search.value) params.q = search.value
    const res = await apiFetch<{ count: number; results: TenantPlatform[] } | TenantPlatform[]>(
      '/platform/tenants/', { params }
    )
    tenants.value = Array.isArray(res) ? res : res.results
  } finally { loading.value = false }
}

const STATUS_COLOR: Record<string, string> = {
  active: 'green', trial: 'blue', past_due: 'yellow', canceled: 'red', suspended: 'neutral'
}
const STATUS_LABEL: Record<string, string> = {
  active: 'Activa', trial: 'Prueba', past_due: 'Vencida', canceled: 'Cancelada', suspended: 'Suspendida'
}

let timer: ReturnType<typeof setTimeout> | null = null
watch(search, () => {
  if (timer) clearTimeout(timer)
  timer = setTimeout(load, 300)
})

onMounted(load)
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Tenants <span class="text-slate-400 font-normal text-lg">({{ tenants.length }})</span></h1>
      <UButton icon="i-lucide-plus" @click="showNewModal = true">Nuevo tenant</UButton>
    </div>

    <UInput v-model="search" placeholder="Buscar por nombre o slug…" icon="i-lucide-search" class="max-w-sm" />

    <NewTenantModal v-model:open="showNewModal" @created="load" />

    <UCard :ui="{ body: 'p-0' }">
      <div v-if="loading" class="flex justify-center py-12">
        <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl text-primary-500" />
      </div>

      <table v-else class="w-full text-sm">
        <thead class="bg-slate-50">
          <tr>
            <th class="text-left px-4 py-3 font-medium text-slate-600">Tenant</th>
            <th class="text-left px-4 py-3 font-medium text-slate-600">Tipo</th>
            <th class="text-left px-4 py-3 font-medium text-slate-600">Plan</th>
            <th class="text-left px-4 py-3 font-medium text-slate-600">Estado suscripción</th>
            <th class="text-left px-4 py-3 font-medium text-slate-600">Miembros</th>
            <th class="text-left px-4 py-3 font-medium text-slate-600">Activo</th>
            <th class="px-4 py-3" />
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr
            v-for="t in tenants"
            :key="t.id"
            class="hover:bg-slate-50 cursor-pointer"
            @click="navigateTo(`/tenants/${t.id}`)"
          >
            <td class="px-4 py-3">
              <p class="font-medium text-slate-800">{{ t.name }}</p>
              <p class="text-xs text-slate-400 font-mono">{{ t.slug }}</p>
            </td>
            <td class="px-4 py-3 text-slate-700 capitalize">{{ t.type }}</td>
            <td class="px-4 py-3">
              <span v-if="t.plan_display" class="font-medium text-slate-700">{{ t.plan_display }}</span>
              <span v-else class="text-slate-400 italic">Sin asignar</span>
            </td>
            <td class="px-4 py-3">
              <UBadge v-if="t.subscription" :color="STATUS_COLOR[t.subscription.status]" variant="soft">
                {{ STATUS_LABEL[t.subscription.status] }}
              </UBadge>
              <span v-else-if="t.plan === 'free'" class="text-slate-400 text-xs italic">Sin suscripción</span>
              <span v-else class="text-slate-300 text-xs">—</span>
            </td>
            <td class="px-4 py-3 text-slate-700">{{ t.member_count }}</td>
            <td class="px-4 py-3">
              <UBadge :color="t.is_active ? 'green' : 'red'" variant="soft" size="sm">
                {{ t.is_active ? 'Activo' : 'Inactivo' }}
              </UBadge>
            </td>
            <td class="px-4 py-3">
              <UButton variant="ghost" icon="i-lucide-arrow-right" size="sm" />
            </td>
          </tr>
          <tr v-if="tenants.length === 0">
            <td colspan="7" class="text-center py-12 text-slate-400">No hay tenants</td>
          </tr>
        </tbody>
      </table>
    </UCard>
  </div>
</template>
