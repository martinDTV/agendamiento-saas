<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const { apiFetch } = useApi()

interface Subscription {
  id: number
  tenant: string
  tenant_name: string
  tenant_slug: string
  plan_name: string
  plan_price_monthly: string
  status: string
  billing_cycle: string
  current_period_end: string
  discount_code: string | null
  notes: string
}

const subs = ref<Subscription[]>([])
const loading = ref(false)
const filterStatus = ref('all')

const STATUS_OPTIONS = [
  { label: 'Todos los estados', value: 'all' },
  { label: 'Trial', value: 'trial' },
  { label: 'Activa', value: 'active' },
  { label: 'Pago vencido', value: 'past_due' },
  { label: 'Cancelada', value: 'canceled' },
  { label: 'Suspendida', value: 'suspended' }
]

const STATUS_COLOR: Record<string, string> = {
  active: 'green', trial: 'blue', past_due: 'yellow', canceled: 'red', suspended: 'neutral'
}
const STATUS_LABEL: Record<string, string> = {
  active: 'Activa', trial: 'Trial', past_due: 'Vencida', canceled: 'Cancelada', suspended: 'Suspendida'
}

async function load() {
  loading.value = true
  try {
    const params: Record<string, string> = {}
    if (filterStatus.value && filterStatus.value !== 'all') params.status = filterStatus.value
    const res = await apiFetch<{ results: Subscription[] } | Subscription[]>(
      '/platform/subscriptions/', { params }
    )
    subs.value = Array.isArray(res) ? res : res.results
  } finally { loading.value = false }
}

watch(filterStatus, load)
onMounted(load)

const fmt = (n: number) => new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(n)
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Suscripciones <span class="text-slate-400 font-normal text-lg">({{ subs.length }})</span></h1>
    </div>

    <USelect
      v-model="filterStatus"
      :items="STATUS_OPTIONS"
      value-attribute="value"
      label-attribute="label"
      class="w-56"
    />

    <UCard :ui="{ body: 'p-0' }">
      <div v-if="loading" class="flex justify-center py-12">
        <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl text-primary-500" />
      </div>

      <table v-else class="w-full text-sm">
        <thead class="bg-slate-50">
          <tr>
            <th class="text-left px-4 py-3 font-medium text-slate-600">Tenant</th>
            <th class="text-left px-4 py-3 font-medium text-slate-600">Plan</th>
            <th class="text-right px-4 py-3 font-medium text-slate-600">Precio</th>
            <th class="text-left px-4 py-3 font-medium text-slate-600">Estado</th>
            <th class="text-left px-4 py-3 font-medium text-slate-600">Ciclo</th>
            <th class="text-left px-4 py-3 font-medium text-slate-600">Próximo cobro</th>
            <th class="text-left px-4 py-3 font-medium text-slate-600">Descuento</th>
            <th class="px-4 py-3" />
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr
            v-for="s in subs"
            :key="s.id"
            class="hover:bg-slate-50 cursor-pointer"
            @click="navigateTo(`/tenants/${s.tenant}`)"
          >
            <td class="px-4 py-3">
              <p class="font-medium text-slate-800">{{ s.tenant_name }}</p>
              <p class="text-xs text-slate-400 font-mono">{{ s.tenant_slug }}</p>
            </td>
            <td class="px-4 py-3 font-medium text-primary-600">{{ s.plan_name }}</td>
            <td class="px-4 py-3 text-right font-mono">{{ fmt(Number(s.plan_price_monthly)) }}</td>
            <td class="px-4 py-3">
              <UBadge :color="STATUS_COLOR[s.status]" variant="soft">
                {{ STATUS_LABEL[s.status] }}
              </UBadge>
            </td>
            <td class="px-4 py-3 capitalize text-slate-700">{{ s.billing_cycle === 'monthly' ? 'Mensual' : 'Anual' }}</td>
            <td class="px-4 py-3 font-mono text-xs text-slate-700">{{ s.current_period_end }}</td>
            <td class="px-4 py-3">
              <UBadge v-if="s.discount_code" color="purple" variant="soft" class="font-mono">
                {{ s.discount_code }}
              </UBadge>
              <span v-else class="text-slate-300 text-xs">—</span>
            </td>
            <td class="px-4 py-3">
              <UButton variant="ghost" icon="i-lucide-arrow-right" size="sm" />
            </td>
          </tr>
          <tr v-if="subs.length === 0">
            <td colspan="8" class="text-center py-12 text-slate-400">No hay suscripciones</td>
          </tr>
        </tbody>
      </table>
    </UCard>
  </div>
</template>
