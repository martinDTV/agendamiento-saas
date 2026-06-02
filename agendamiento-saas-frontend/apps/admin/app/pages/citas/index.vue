<script setup lang="ts">
import type { Appointment, PaginatedResponse } from '@agendamiento/shared'

definePageMeta({ middleware: ['tenant', 'auth'] })

const { apiFetch } = useApi()
const toast = useToast()

const filters = reactive({
  search: '',
  date: '',
  status: 'all',
  doctor: ''
})

const STATUS_OPTIONS = [
  { label: 'Todos los estados', value: 'all' },
  { label: 'Pendiente', value: 'pending' },
  { label: 'Confirmada', value: 'confirmed' },
  { label: 'Cancelada', value: 'cancelled' },
  { label: 'Completada', value: 'completed' }
]

const STATUS_COLOR: Record<string, string> = {
  pending: 'bg-amber-50 text-amber-600 ring-1 ring-amber-200',
  confirmed: 'bg-emerald-50 text-emerald-600 ring-1 ring-emerald-200',
  cancelled: 'bg-red-50 text-red-500 ring-1 ring-red-200',
  completed: 'bg-slate-100 text-slate-500 ring-1 ring-slate-200'
}

const STATUS_LABEL: Record<string, string> = {
  pending: 'Pendiente',
  confirmed: 'Confirmada',
  cancelled: 'Cancelada',
  completed: 'Completada'
}

const loading = ref(false)
const appointments = ref<Appointment[]>([])
const total = ref(0)

async function load() {
  loading.value = true
  try {
    const params: Record<string, string> = {}
    if (filters.search.trim()) params.search = filters.search.trim()
    if (filters.date) params.date = filters.date
    if (filters.status && filters.status !== 'all') params.status = filters.status
    if (filters.doctor) params.doctor = filters.doctor
    const res = await apiFetch<PaginatedResponse<Appointment>>('/bookings/appointments/', { params })
    appointments.value = res.results
    total.value = res.count
  }
  finally {
    loading.value = false
  }
}

async function updateStatus(appt: Appointment, status: string) {
  await apiFetch(`/bookings/appointments/${appt.id}/`, {
    method: 'PATCH',
    body: { status }
  })
  toast.add({ title: 'Estado actualizado', color: 'primary' })
  load()
}

// Debounce so typing in the search box doesn't fire a request per keystroke.
watchDebounced(filters, load, { immediate: true, debounce: 350, deep: true })
</script>

<template>
  <div class="space-y-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-900 dark:text-white">
          Citas
          <span class="text-slate-400 font-normal text-base ml-1">({{ total }})</span>
        </h1>
        <p class="text-sm text-slate-400 mt-0.5">Gestiona todas las citas del consultorio</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="flex gap-3 flex-wrap items-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4">
      <UInput
        v-model="filters.search"
        icon="i-lucide-search"
        placeholder="Buscar por nombre, correo o teléfono"
        class="w-full sm:w-80"
        :ui="{ trailing: 'pe-1' }"
      >
        <template v-if="filters.search" #trailing>
          <UButton
            color="neutral"
            variant="link"
            icon="i-lucide-x"
            aria-label="Limpiar búsqueda"
            @click="filters.search = ''"
          />
        </template>
      </UInput>
      <UInput v-model="filters.date" type="date" class="w-44" />
      <USelect v-model="filters.status" :items="STATUS_OPTIONS" value-attribute="value" label-attribute="label" class="w-52" />
    </div>

    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
      <div v-if="loading" class="flex justify-center py-16">
        <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl text-violet-500" />
      </div>

      <table v-else class="w-full text-sm">
        <thead class="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-800">
          <tr>
            <th class="text-left px-5 py-3.5 font-semibold text-xs text-slate-500 uppercase tracking-wide">Paciente</th>
            <th class="text-left px-5 py-3.5 font-semibold text-xs text-slate-500 uppercase tracking-wide">Servicio</th>
            <th class="text-left px-5 py-3.5 font-semibold text-xs text-slate-500 uppercase tracking-wide">Doctor</th>
            <th class="text-left px-5 py-3.5 font-semibold text-xs text-slate-500 uppercase tracking-wide">Fecha / Hora</th>
            <th class="text-left px-5 py-3.5 font-semibold text-xs text-slate-500 uppercase tracking-wide">Estado</th>
            <th class="px-5 py-3.5" />
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
          <tr v-for="a in appointments" :key="a.id" class="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
            <td class="px-5 py-3.5">
              <p class="font-medium text-slate-800 dark:text-slate-100">{{ a.patient_name }}</p>
              <p class="text-xs text-slate-400 mt-0.5">{{ a.patient_email }}</p>
            </td>
            <td class="px-5 py-3.5 text-slate-600 dark:text-slate-300">{{ a.service_name }}</td>
            <td class="px-5 py-3.5 text-slate-600 dark:text-slate-300">{{ a.doctor_name }}</td>
            <td class="px-5 py-3.5">
              <p class="text-slate-700 dark:text-slate-200 font-medium">{{ a.date }}</p>
              <p class="text-xs text-slate-400 font-mono">{{ a.start_time.slice(0, 5) }} – {{ a.end_time.slice(0, 5) }}</p>
            </td>
            <td class="px-5 py-3.5">
              <span class="text-xs font-semibold px-2.5 py-1 rounded-full" :class="STATUS_COLOR[a.status]">
                {{ STATUS_LABEL[a.status] }}
              </span>
            </td>
            <td class="px-5 py-3.5">
              <UDropdownMenu
                :items="[
                  [
                    { label: 'Confirmar', icon: 'i-lucide-check', click: () => updateStatus(a, 'confirmed'), disabled: a.status === 'confirmed' },
                    { label: 'Completada', icon: 'i-lucide-check-check', click: () => updateStatus(a, 'completed'), disabled: a.status === 'completed' },
                    { label: 'Cancelar', icon: 'i-lucide-x', color: 'error', click: () => updateStatus(a, 'cancelled'), disabled: a.status === 'cancelled' }
                  ]
                ]"
              >
                <UButton variant="ghost" icon="i-lucide-more-horizontal" size="sm" />
              </UDropdownMenu>
            </td>
          </tr>
          <tr v-if="appointments.length === 0">
            <td colspan="6" class="text-center py-16">
              <UIcon name="i-lucide-calendar-x" class="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <p class="text-sm text-slate-400">No hay citas con estos filtros</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
