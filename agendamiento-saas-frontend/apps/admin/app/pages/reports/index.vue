<script setup lang="ts">
definePageMeta({ middleware: ['tenant', 'auth', 'admin-only'] })

const { apiFetch } = useApi()
const { $api } = useNuxtApp()

interface NamedTotal { id: string, name: string, total: number, revenue: number }
interface TrendPoint { date: string, total: number }
interface OccupancyCell { weekday: number, hour: number, total: number }

interface ReportData {
  from_date: string
  to_date: string
  total: number
  by_status: Record<string, number>
  cancellation_rate: number
  completion_rate: number
  revenue_total: number
  by_doctor: NamedTotal[]
  by_service: NamedTotal[]
  trend: TrendPoint[]
  trend_granularity: 'day' | 'month'
  occupancy: OccupancyCell[]
}

const today = new Date().toISOString().slice(0, 10)
const thirtyDaysAgo = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10)

const fromDate = ref(thirtyDaysAgo)
const toDate = ref(today)
const data = ref<ReportData | null>(null)
const loading = ref(false)
const exporting = ref(false)

const WEEKDAYS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
const NAVY = '#274C77'
const VIOLET = '#A78BFA'

const statusLabels: Record<string, string> = {
  pending: 'Pendientes',
  confirmed: 'Confirmadas',
  completed: 'Completadas',
  cancelled: 'Canceladas'
}
const statusColors: Record<string, string> = {
  pending: 'text-yellow-600',
  confirmed: 'text-blue-600',
  completed: 'text-green-600',
  cancelled: 'text-red-500'
}

const currency = (n: number) =>
  new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 }).format(n)

async function load() {
  loading.value = true
  try {
    data.value = await apiFetch<ReportData>('/reports/appointments/', {
      params: { from_date: fromDate.value, to_date: toDate.value }
    })
  }
  finally { loading.value = false }
}

async function exportExcel() {
  exporting.value = true
  try {
    const res = await $api.get('/reports/appointments/export/', {
      params: { from_date: fromDate.value, to_date: toDate.value },
      responseType: 'blob'
    })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `reporte-citas_${fromDate.value}_${toDate.value}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  }
  finally { exporting.value = false }
}

// ── Chart options ─────────────────────────────────────────────────────────
const statusPie = computed(() => {
  const d = data.value
  if (!d) return {}
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      data: [
        { value: d.by_status.pending, name: 'Pendientes', itemStyle: { color: '#EAB308' } },
        { value: d.by_status.confirmed, name: 'Confirmadas', itemStyle: { color: '#3B82F6' } },
        { value: d.by_status.completed, name: 'Completadas', itemStyle: { color: '#22C55E' } },
        { value: d.by_status.cancelled, name: 'Canceladas', itemStyle: { color: '#EF4444' } }
      ]
    }]
  }
})

const trendLine = computed(() => {
  const d = data.value
  if (!d) return {}
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 16, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: d.trend.map(p => p.date), axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{
      type: 'line',
      smooth: true,
      data: d.trend.map(p => p.total),
      itemStyle: { color: NAVY },
      areaStyle: { color: 'rgba(39,76,119,0.12)' },
      lineStyle: { width: 2 }
    }]
  }
})

const doctorBar = computed(() => buildBar(data.value?.by_doctor ?? [], NAVY))
const serviceBar = computed(() => buildBar(data.value?.by_service ?? [], VIOLET))

function buildBar(rows: NamedTotal[], color: string) {
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 8, right: 16, top: 16, bottom: 8, containLabel: true },
    xAxis: { type: 'value', minInterval: 1 },
    yAxis: { type: 'category', data: rows.map(r => r.name || '—').reverse(), axisLabel: { fontSize: 11 } },
    series: [{
      type: 'bar',
      data: rows.map(r => r.total).reverse(),
      itemStyle: { color, borderRadius: [0, 4, 4, 0] },
      barWidth: '60%'
    }]
  }
}

const occupancyHeat = computed(() => {
  const d = data.value
  if (!d) return {}
  const hours = Array.from({ length: 24 }, (_, h) => h).filter(h =>
    d.occupancy.some(c => c.hour === h)
  )
  const cells = d.occupancy.map(c => [hours.indexOf(c.hour), c.weekday, c.total])
  const max = Math.max(1, ...d.occupancy.map(c => c.total))
  return {
    tooltip: { position: 'top' },
    grid: { left: 50, right: 16, top: 16, bottom: 50, containLabel: true },
    xAxis: { type: 'category', data: hours.map(h => `${String(h).padStart(2, '0')}:00`), axisLabel: { fontSize: 9, rotate: 45 } },
    yAxis: { type: 'category', data: WEEKDAYS },
    visualMap: {
      min: 0, max, calculable: false, orient: 'horizontal', left: 'center', bottom: 0,
      inRange: { color: ['#EEF2F7', NAVY] }, textStyle: { fontSize: 10 }
    },
    series: [{
      type: 'heatmap',
      data: cells,
      label: { show: false },
      emphasis: { itemStyle: { shadowBlur: 6, shadowColor: 'rgba(0,0,0,0.2)' } }
    }]
  }
})

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
        <UButton
          color="neutral"
          variant="subtle"
          icon="i-lucide-file-spreadsheet"
          :loading="exporting"
          :disabled="!data || data.total === 0"
          @click="exportExcel"
        >
          Exportar Excel
        </UButton>
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
        <UCard>
          <p class="text-3xl font-bold text-gray-900 dark:text-white">{{ currency(data.revenue_total) }}</p>
          <p class="text-sm text-gray-500 mt-1">Ingreso estimado</p>
        </UCard>
        <UCard>
          <p class="text-3xl font-bold text-green-600">{{ data.completion_rate }}%</p>
          <p class="text-sm text-gray-500 mt-1">Finalización</p>
        </UCard>
        <UCard>
          <p class="text-3xl font-bold text-red-500">{{ data.cancellation_rate }}%</p>
          <p class="text-sm text-gray-500 mt-1">Cancelación</p>
        </UCard>
      </div>

      <!-- Status breakdown chips + pie -->
      <div class="grid lg:grid-cols-3 gap-4">
        <UCard class="lg:col-span-1">
          <template #header><p class="font-semibold">Citas por estado</p></template>
          <EChart :option="statusPie" />
        </UCard>
        <UCard class="lg:col-span-2">
          <template #header><p class="font-semibold">Tendencia ({{ data.trend_granularity === 'month' ? 'por mes' : 'por día' }})</p></template>
          <EChart :option="trendLine" />
        </UCard>
      </div>

      <!-- Doctor + service bars -->
      <div class="grid md:grid-cols-2 gap-4">
        <UCard>
          <template #header><p class="font-semibold">Citas por doctor</p></template>
          <EChart v-if="data.by_doctor.length" :option="doctorBar" />
          <p v-else class="text-center py-10 text-gray-400">Sin datos</p>
        </UCard>
        <UCard>
          <template #header><p class="font-semibold">Citas por servicio</p></template>
          <EChart v-if="data.by_service.length" :option="serviceBar" />
          <p v-else class="text-center py-10 text-gray-400">Sin datos</p>
        </UCard>
      </div>

      <!-- Revenue tables -->
      <div class="grid md:grid-cols-2 gap-4">
        <UCard>
          <template #header><p class="font-semibold">Ingreso por doctor</p></template>
          <table class="w-full text-sm">
            <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
              <tr v-for="row in data.by_doctor" :key="row.id" class="flex items-center justify-between py-2">
                <td class="text-gray-700 dark:text-gray-300">{{ row.name || '—' }}</td>
                <td class="font-semibold text-gray-900 dark:text-white">{{ currency(row.revenue) }}</td>
              </tr>
            </tbody>
          </table>
        </UCard>
        <UCard>
          <template #header><p class="font-semibold">Ingreso por servicio</p></template>
          <table class="w-full text-sm">
            <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
              <tr v-for="row in data.by_service" :key="row.id" class="flex items-center justify-between py-2">
                <td class="text-gray-700 dark:text-gray-300">{{ row.name }}</td>
                <td class="font-semibold text-gray-900 dark:text-white">{{ currency(row.revenue) }}</td>
              </tr>
            </tbody>
          </table>
        </UCard>
      </div>

      <!-- Occupancy heatmap -->
      <UCard>
        <template #header><p class="font-semibold">Ocupación por día y hora</p></template>
        <EChart v-if="data.occupancy.length" :option="occupancyHeat" />
        <p v-else class="text-center py-10 text-gray-400">Sin datos</p>
      </UCard>
    </template>
  </div>
</template>
