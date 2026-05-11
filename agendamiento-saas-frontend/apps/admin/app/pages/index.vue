<script setup lang="ts">
import type { PaginatedResponse, Appointment } from '@agendamiento/shared'

definePageMeta({ middleware: ['tenant', 'auth'] })

const { apiFetch } = useApi()
const auth = useAuthStore()

const today = new Date().toISOString().slice(0, 10)

const { data: todayData } = await useAsyncData('dashboard-today', () =>
  apiFetch<PaginatedResponse<Appointment>>('/bookings/appointments/', {
    params: { date: today }
  })
)

const todayAppts = computed(() => todayData.value?.results ?? [])
const pending = computed(() => todayAppts.value.filter(a => a.status === 'pending').length)
const confirmed = computed(() => todayAppts.value.filter(a => a.status === 'confirmed').length)
const total = computed(() => todayAppts.value.length)

const STATUS_COLOR: Record<string, string> = {
  pending: 'text-amber-600 bg-amber-50 ring-1 ring-amber-200',
  confirmed: 'text-sage-700 bg-sage-100 ring-1 ring-sage-300',
  cancelled: 'text-red-500 bg-red-50 ring-1 ring-red-200',
  completed: 'text-slate-500 bg-slate-100 ring-1 ring-slate-200'
}

const STATUS_LABEL: Record<string, string> = {
  pending: 'Pendiente',
  confirmed: 'Confirmada',
  cancelled: 'Cancelada',
  completed: 'Completada'
}

const kpis = computed(() => [
  {
    label: 'Citas hoy',
    value: total.value,
    icon: 'i-lucide-calendar',
    iconBg: 'bg-sage-100 dark:bg-sage-900/40',
    iconColor: 'text-sage-700 dark:text-sage-300',
    valueCls: 'text-slate-900 dark:text-white'
  },
  {
    label: 'Confirmadas',
    value: confirmed.value,
    icon: 'i-lucide-check-circle-2',
    iconBg: 'bg-sage-100 dark:bg-sage-900/40',
    iconColor: 'text-sage-700 dark:text-sage-300',
    valueCls: 'text-sage-700 dark:text-sage-300'
  },
  {
    label: 'Pendientes',
    value: pending.value,
    icon: 'i-lucide-clock-4',
    iconBg: 'bg-amber-100 dark:bg-amber-900/40',
    iconColor: 'text-amber-600 dark:text-amber-400',
    valueCls: 'text-amber-600 dark:text-amber-400'
  }
])
</script>

<template>
  <div class="space-y-6">
    <!-- Greeting -->
    <div>
      <h1 class="text-2xl font-bold text-slate-900 dark:text-white">
        Hola, {{ auth.user?.first_name || auth.user?.email }} 👋
      </h1>
      <p class="text-sm text-slate-400 mt-0.5 capitalize">
        {{ new Date().toLocaleDateString('es-MX', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }) }}
      </p>
    </div>

    <!-- KPIs -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div
        v-for="kpi in kpis"
        :key="kpi.label"
        class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 flex items-center gap-4"
      >
        <div :class="['w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0', kpi.iconBg]">
          <UIcon :name="kpi.icon" :class="['w-6 h-6', kpi.iconColor]" />
        </div>
        <div>
          <p class="text-xs font-medium text-slate-400 uppercase tracking-wide">{{ kpi.label }}</p>
          <p :class="['text-3xl font-bold leading-none mt-1', kpi.valueCls]">{{ kpi.value }}</p>
        </div>
      </div>
    </div>

    <!-- Today's appointments -->
    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
      <div class="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-800">
        <h2 class="font-semibold text-slate-800 dark:text-slate-100">Citas de hoy</h2>
        <UButton to="/citas" variant="ghost" size="sm" trailing-icon="i-lucide-arrow-right" class="text-sage-700">
          Ver todas
        </UButton>
      </div>

      <div v-if="todayAppts.length === 0" class="text-center py-12">
        <UIcon name="i-lucide-calendar-x" class="w-10 h-10 text-slate-300 mx-auto mb-3" />
        <p class="text-sm text-slate-400">No hay citas agendadas para hoy</p>
      </div>

      <div v-else class="divide-y divide-slate-100 dark:divide-slate-800">
        <div v-for="a in todayAppts" :key="a.id" class="flex items-center gap-4 px-5 py-3.5 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
          <div class="w-12 text-center flex-shrink-0">
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-300 font-mono">
              {{ a.start_time.slice(0, 5) }}
            </span>
          </div>
          <div class="w-1 h-8 rounded-full bg-sage-200 dark:bg-sage-800 flex-shrink-0" />
          <div class="flex-1 min-w-0">
            <p class="font-medium text-sm text-slate-800 dark:text-slate-100 truncate">{{ a.patient_name }}</p>
            <p class="text-xs text-slate-400 truncate">{{ a.service_name }} · {{ a.doctor_name }}</p>
          </div>
          <span
            class="text-xs font-semibold px-2.5 py-1 rounded-full flex-shrink-0"
            :class="STATUS_COLOR[a.status]"
          >
            {{ STATUS_LABEL[a.status] }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
