<script setup lang="ts">
import type { Schedule, Doctor, Weekday, PaginatedResponse } from '@agendamiento/shared'

definePageMeta({ middleware: ['tenant', 'auth'] })

const route = useRoute()
const { apiFetch } = useApi()
const toast = useToast()

const doctor = ref<Doctor | null>(null)
const schedules = ref<Schedule[]>([])
const loading = ref(false)

const WEEKDAYS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

async function load() {
  loading.value = true
  try {
    const [doc, sched] = await Promise.all([
      apiFetch<Doctor>(`/catalog/doctors/${route.params.id}/`),
      apiFetch<PaginatedResponse<Schedule>>('/catalog/schedules/', { params: { doctor: route.params.id as string } })
    ])
    doctor.value = doc
    schedules.value = sched.results
  }
  finally { loading.value = false }
}

async function toggle(schedule: Schedule) {
  const newValue = !schedule.is_active
  schedule.is_active = newValue
  try {
    await apiFetch(`/catalog/schedules/${schedule.id}/`, {
      method: 'PATCH',
      body: { is_active: newValue }
    })
  }
  catch {
    schedule.is_active = !newValue
    toast.add({ title: 'Error al actualizar', color: 'error' })
  }
}

async function remove(schedule: Schedule) {
  await apiFetch(`/catalog/schedules/${schedule.id}/`, { method: 'DELETE' })
  toast.add({ title: 'Horario eliminado', color: 'primary' })
  load()
}

// Schedule form (create + edit)
const showForm = ref(false)
const editingId = ref<string | null>(null)
const form = ref({ weekday: 1 as Weekday, start_time: '09:00', end_time: '18:00' })
const saving = ref(false)

const usedWeekdays = computed(() => schedules.value.map(s => s.weekday))
const availableWeekdays = computed(() => {
  const used = editingId.value
    ? usedWeekdays.value.filter(w => w !== schedules.value.find(s => s.id === editingId.value)?.weekday)
    : usedWeekdays.value
  return WEEKDAYS.map((label, idx) => ({ label, value: idx }))
    .filter(w => !used.includes(w.value as Weekday))
})

const weekdayItems = computed(() =>
  availableWeekdays.value.map(w => ({ label: w.label, value: w.value }))
)

function openCreate() {
  editingId.value = null
  form.value = { weekday: availableWeekdays.value[0]?.value as Weekday ?? 1, start_time: '09:00', end_time: '18:00' }
  showForm.value = true
}

function openEdit(s: Schedule) {
  editingId.value = s.id
  form.value = {
    weekday: s.weekday,
    start_time: s.start_time.slice(0, 5),
    end_time: s.end_time.slice(0, 5)
  }
  showForm.value = true
}

function cancelForm() {
  showForm.value = false
  editingId.value = null
}

async function saveSchedule() {
  saving.value = true
  try {
    if (editingId.value) {
      await apiFetch(`/catalog/schedules/${editingId.value}/`, {
        method: 'PATCH',
        body: form.value
      })
      toast.add({ title: 'Horario actualizado', color: 'primary' })
    } else {
      await apiFetch('/catalog/schedules/', {
        method: 'POST',
        body: { doctor: route.params.id, ...form.value }
      })
      toast.add({ title: 'Horario agregado', color: 'primary' })
    }
    cancelForm()
    load()
  }
  catch (err: any) {
    const msg = err?.response?.data?.non_field_errors?.[0]
            ?? err?.response?.data?.weekday?.[0]
            ?? err?.response?.data?.end_time?.[0]
            ?? 'Error al guardar'
    toast.add({ title: msg, color: 'error' })
  }
  finally { saving.value = false }
}

onMounted(load)
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center gap-3">
      <UButton variant="ghost" icon="i-lucide-arrow-left" :to="'/doctors'" />
      <div>
        <h1 class="text-2xl font-bold">Horarios</h1>
        <p class="text-sm text-gray-500">{{ doctor?.full_name }}</p>
      </div>
    </div>

    <UCard :ui="{ body: 'p-0' }">
      <div v-if="loading" class="flex justify-center py-12">
        <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl text-sage-500" />
      </div>
      <table v-else class="w-full text-sm">
        <thead class="bg-gray-50 dark:bg-gray-800/50">
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Día</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Inicio</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Fin</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Activo</th>
            <th class="px-4 py-3" />
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
          <tr v-for="s in schedules" :key="s.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/30">
            <td class="px-4 py-3 font-medium">{{ s.weekday_label }}</td>
            <td class="px-4 py-3 font-mono text-gray-600">{{ s.start_time.slice(0, 5) }}</td>
            <td class="px-4 py-3 font-mono text-gray-600">{{ s.end_time.slice(0, 5) }}</td>
            <td class="px-4 py-3">
              <USwitch :model-value="s.is_active" @update:model-value="toggle(s)" />
            </td>
            <td class="px-4 py-3">
              <div class="flex gap-1 justify-end">
                <UButton size="xs" variant="ghost" icon="i-lucide-pencil" @click="openEdit(s)" />
                <UButton size="xs" variant="ghost" color="error" icon="i-lucide-trash-2" @click="remove(s)" />
              </div>
            </td>
          </tr>
          <tr v-if="schedules.length === 0">
            <td colspan="5" class="text-center py-8 text-gray-400">Sin horarios registrados</td>
          </tr>
        </tbody>
      </table>
    </UCard>

    <div>
      <UButton
        variant="outline"
        icon="i-lucide-plus"
        :disabled="availableWeekdays.length === 0"
        @click="openCreate"
      >
        Agregar horario
      </UButton>
    </div>

    <UModal v-model:open="showForm" :title="editingId ? 'Editar horario' : 'Nuevo horario'">
      <template #content>
        <form class="space-y-4 p-6" @submit.prevent="saveSchedule">
          <h3 class="text-base font-semibold text-slate-800">{{ editingId ? 'Editar horario' : 'Nuevo horario' }}</h3>
          <UFormField label="Día">
            <USelect v-model="form.weekday" :items="weekdayItems" value-attribute="value" label-attribute="label" class="w-full" />
          </UFormField>
          <div class="grid grid-cols-2 gap-3">
            <UFormField label="Hora inicio">
              <UInput v-model="form.start_time" type="time" class="w-full" />
            </UFormField>
            <UFormField label="Hora fin">
              <UInput v-model="form.end_time" type="time" class="w-full" />
            </UFormField>
          </div>
          <div class="flex justify-end gap-2 pt-2 border-t" style="border-color: #F3F4F6;">
            <UButton variant="ghost" color="neutral" @click="cancelForm">Cancelar</UButton>
            <UButton type="submit" :loading="saving">{{ editingId ? 'Guardar' : 'Agregar' }}</UButton>
          </div>
        </form>
      </template>
    </UModal>
  </div>
</template>
