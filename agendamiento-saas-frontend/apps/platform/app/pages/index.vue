<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const { apiFetch } = useApi()

interface Dashboard {
  tenants: { total: number; active: number; inactive: number }
  subscriptions: { active: number; trial: number; canceled: number; total: number }
  revenue: { mrr: number; arr: number; currency: string }
  plans: Array<{ id: number; name: string; price_monthly: string; active_subs: number }>
}

const data = ref<Dashboard | null>(null)
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    data.value = await apiFetch<Dashboard>('/platform/dashboard/')
  } finally { loading.value = false }
}

onMounted(load)

const fmt = (n: number) => new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(n)
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-slate-900">Dashboard</h1>

    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl text-primary-500" />
    </div>

    <template v-else-if="data">
      <!-- Revenue -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <UCard class="bg-gradient-to-br from-primary-500 to-purple-600 text-white border-0">
          <p class="text-xs uppercase tracking-wide opacity-80">MRR</p>
          <p class="text-4xl font-bold mt-1">{{ fmt(data.revenue.mrr) }}</p>
          <p class="text-xs opacity-75 mt-1">Ingreso recurrente mensual</p>
        </UCard>
        <UCard class="bg-gradient-to-br from-emerald-500 to-teal-600 text-white border-0">
          <p class="text-xs uppercase tracking-wide opacity-80">ARR</p>
          <p class="text-4xl font-bold mt-1">{{ fmt(data.revenue.arr) }}</p>
          <p class="text-xs opacity-75 mt-1">Ingreso recurrente anual</p>
        </UCard>
      </div>

      <!-- KPIs -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <UCard>
          <div class="flex items-center gap-3">
            <UIcon name="i-lucide-building-2" class="text-2xl text-blue-500" />
            <div>
              <p class="text-2xl font-bold text-slate-900">{{ data.tenants.total }}</p>
              <p class="text-xs text-slate-500">Tenants totales</p>
            </div>
          </div>
        </UCard>
        <UCard>
          <div class="flex items-center gap-3">
            <UIcon name="i-lucide-check-circle" class="text-2xl text-green-500" />
            <div>
              <p class="text-2xl font-bold text-slate-900">{{ data.subscriptions.active }}</p>
              <p class="text-xs text-slate-500">Suscripciones activas</p>
            </div>
          </div>
        </UCard>
        <UCard>
          <div class="flex items-center gap-3">
            <UIcon name="i-lucide-clock" class="text-2xl text-yellow-500" />
            <div>
              <p class="text-2xl font-bold text-slate-900">{{ data.subscriptions.trial }}</p>
              <p class="text-xs text-slate-500">En periodo de prueba</p>
            </div>
          </div>
        </UCard>
        <UCard>
          <div class="flex items-center gap-3">
            <UIcon name="i-lucide-x-circle" class="text-2xl text-red-500" />
            <div>
              <p class="text-2xl font-bold text-slate-900">{{ data.subscriptions.canceled }}</p>
              <p class="text-xs text-slate-500">Canceladas</p>
            </div>
          </div>
        </UCard>
      </div>

      <!-- Plans distribution -->
      <UCard>
        <template #header>
          <p class="font-semibold text-slate-800">Distribución por plan</p>
        </template>

        <div v-if="data.plans.length === 0" class="text-center py-8 text-slate-400">
          No hay planes creados aún. <NuxtLink to="/plans" class="text-primary-500 underline">Crear plan</NuxtLink>
        </div>

        <table v-else class="w-full text-sm">
          <thead>
            <tr class="border-b border-slate-100">
              <th class="text-left py-2 font-medium text-slate-500">Plan</th>
              <th class="text-right py-2 font-medium text-slate-500">Precio mensual</th>
              <th class="text-right py-2 font-medium text-slate-500">Suscripciones activas</th>
              <th class="text-right py-2 font-medium text-slate-500">Ingreso</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in data.plans" :key="p.id" class="border-b border-slate-50">
              <td class="py-3 font-medium text-slate-800">{{ p.name }}</td>
              <td class="py-3 text-right font-mono text-slate-700">{{ fmt(Number(p.price_monthly)) }}</td>
              <td class="py-3 text-right">{{ p.active_subs }}</td>
              <td class="py-3 text-right font-mono font-semibold text-slate-900">
                {{ fmt(Number(p.price_monthly) * p.active_subs) }}
              </td>
            </tr>
          </tbody>
        </table>
      </UCard>
    </template>
  </div>
</template>
