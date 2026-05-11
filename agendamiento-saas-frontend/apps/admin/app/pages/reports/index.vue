<script setup lang="ts">
definePageMeta({ middleware: ['tenant', 'auth', 'admin-only'] })

const { apiFetch } = useApi()

interface ReportData {
  from_date: string
  to_date: string
  total: number
  by_status: Record<string, number>
  by_doctor: { id: string; name: string; total: number }[]
  by_service: { id: string; name: string; total: number }[]
}

const today = new Date().toISOString().slice(0, 10)
const thirtyDaysAgo = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10)

const fromDate = ref(thirtyDaysAgo)
const toDate = ref(today)
const data = ref<ReportData | null>(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    data.value = await apiFetch<ReportData>('/reports/appointments/', {
      params: { from_date: fromDate.value, to_date: toDate.value }
    })
  }
  finally { loading.value = false }
}

const statusColors: Record<string, string> = {
  pending: 'text-yellow-600',
  confirmed: 'text-blue-600',
  completed: 'text-green-600',
  cancelled: 'text-red-500'
}
const statusLabels: Record<string, string> = {
  pending: 'Pendientes',
  confirmed: 'Confirmadas',
  completed: 'Completadas',
  cancelled: 'Canceladas'
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-end gap-4 justify-between">
      <h1 class="text-2xl font-bold">Reportes</h1>
      <div class="flex items-end gap-3">
        <UFormField label="Desde">
          <UInput v-model="fromDate" type="date" />
        </UFormField>
        <UFormField label="Hasta">
          <UInput v-model="toDate" type="date" />
        </UFormField>
        <UButton :loading="loading" @click="load">Actualizar</UButton>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center py-16">
      <UIcon name="i-lucide-loader-2" class="animate-spin text-3xl text-sage-500" />
    </div>

    <template v-else-if="data">
      <!-- KPI row -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <UCard>
          <p class="text-3xl font-bold text-gray-900 dark:text-white">{{ data.total }}</p>
          <p class="text-sm text-gray-500 mt-1">Total citas</p>
        </UCard>
        <UCard v-for="(key) in ['pending', 'confirmed', 'completed', 'cancelled']" :key="key">
          <p class="text-3xl font-bold" :class="statusColors[key]">{{ data.by_status[key] ?? 0 }}</p>
          <p class="text-sm text-gray-500 mt-1">{{ statusLabels[key] }}</p>
        </UCard>
      </div>

      <div class="grid md:grid-cols-2 gap-4">
        <!-- By doctor -->
        <UCard>
          <template #header>
            <p class="font-semibold">Por doctor</p>
          </template>
          <table class="w-full text-sm">
            <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
              <tr v-for="row in data.by_doctor" :key="row.id" class="flex items-center justify-between py-2">
                <td class="text-gray-700 dark:text-gray-300">{{ row.name || '—' }}</td>
                <td class="font-semibold text-gray-900 dark:text-white">{{ row.total }}</td>
              </tr>
              <tr v-if="data.by_doctor.length === 0">
                <td class="text-center py-6 text-gray-400">Sin datos</td>
              </tr>
            </tbody>
          </table>
        </UCard>

        <!-- By service -->
        <UCard>
          <template #header>
            <p class="font-semibold">Por servicio</p>
          </template>
          <table class="w-full text-sm">
            <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
              <tr v-for="row in data.by_service" :key="row.id" class="flex items-center justify-between py-2">
                <td class="text-gray-700 dark:text-gray-300">{{ row.name }}</td>
                <td class="font-semibold text-gray-900 dark:text-white">{{ row.total }}</td>
              </tr>
              <tr v-if="data.by_service.length === 0">
                <td class="text-center py-6 text-gray-400">Sin datos</td>
              </tr>
            </tbody>
          </table>
        </UCard>
      </div>
    </template>
  </div>
</template>
