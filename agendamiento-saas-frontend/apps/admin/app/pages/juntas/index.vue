<script setup lang="ts">
import type { Meeting, Room, Membership, PaginatedResponse } from '@agendamiento/shared'

definePageMeta({ middleware: ['tenant', 'auth'] })

const { apiFetch } = useApi()

const meetings  = ref<Meeting[]>([])
const rooms     = ref<Room[]>([])
const members   = ref<Membership[]>([])
const loading   = ref(false)
const showForm  = ref(false)
const saving    = ref(false)
const selected  = ref<Meeting | null>(null)

const form = reactive({
  title:        '',
  description:  '',
  organizer:    null as number | null,
  participants: [] as number[],
  room:         '',
  date:         '',
  start_time:   '',
  end_time:     '',
})

async function load() {
  loading.value = true
  try {
    const today = new Date().toISOString().slice(0, 10)
    const future = new Date(Date.now() + 30 * 864e5).toISOString().slice(0, 10)
    const [m, r, mb] = await Promise.all([
      apiFetch<PaginatedResponse<Meeting>>('/meetings/meetings/', {
        params: { from_date: today, to_date: future }
      }),
      apiFetch<PaginatedResponse<Room>>('/meetings/rooms/', { params: { active: 'true' } }),
      apiFetch<PaginatedResponse<Membership>>('/accounts/memberships/'),
    ])
    meetings.value = m.results
    rooms.value    = r.results
    members.value  = mb.results
  } finally { loading.value = false }
}

function openCreate() {
  selected.value = null
  form.title        = ''
  form.description  = ''
  form.organizer    = members.value[0]?.user ?? null
  form.participants = []
  form.room         = ''
  form.date         = ''
  form.start_time   = ''
  form.end_time     = ''
  showForm.value = true
}

async function save() {
  saving.value = true
  try {
    await apiFetch('/meetings/meetings/', {
      method: 'POST',
      body: {
        ...form,
        room: form.room || null,
      },
    })
    showForm.value = false
    await load()
  } finally { saving.value = false }
}

async function deleteMeeting(id: string) {
  await apiFetch(`/meetings/meetings/${id}/`, { method: 'DELETE' })
  meetings.value = meetings.value.filter(m => m.id !== id)
  if (selected.value?.id === id) selected.value = null
}

const roomItems = computed(() => [
  { label: 'Sin sala asignada', value: '' },
  ...rooms.value.map(r => ({ label: `${r.name} — ${r.branch_name}`, value: r.id }))
])

const memberItems = computed(() =>
  members.value.map(m => ({
    label: `${m.user_full_name}${m.role !== 'doctor' ? ` (${m.role})` : ''}`,
    value: m.user,
  }))
)

function fmtDate(d: string) {
  return new Date(d + 'T00:00').toLocaleDateString('es-MX', {
    weekday: 'short', day: 'numeric', month: 'short'
  })
}

function isToday(d: string) {
  return d === new Date().toISOString().slice(0, 10)
}

function isPast(m: Meeting) {
  return m.date < new Date().toISOString().slice(0, 10)
}

// Group by date
const byDate = computed(() => {
  const map = new Map<string, Meeting[]>()
  for (const m of meetings.value) {
    if (!map.has(m.date)) map.set(m.date, [])
    map.get(m.date)!.push(m)
  }
  return [...map.entries()].sort(([a], [b]) => a.localeCompare(b))
})

onMounted(load)
</script>

<template>
  <div class="space-y-6">

    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-slate-800">Juntas</h2>
        <p class="text-sm text-slate-400">Programa reuniones internas con el equipo médico</p>
      </div>
      <UButton icon="i-lucide-plus" @click="openCreate">Nueva junta</UButton>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-16">
      <UIcon name="i-lucide-loader-2" class="animate-spin w-6 h-6 text-slate-400" />
    </div>

    <!-- Two-panel layout -->
    <div v-else class="flex gap-6 min-h-[500px]">

      <!-- Meeting list -->
      <div class="w-80 flex-shrink-0 space-y-4">
        <div v-if="byDate.length === 0" class="text-center py-12 text-slate-400">
          <UIcon name="i-lucide-video-off" class="w-8 h-8 mx-auto mb-2 opacity-40" />
          <p class="text-sm">Sin juntas programadas</p>
        </div>

        <div v-for="[date, dayMeetings] in byDate" :key="date">
          <!-- Date label -->
          <div class="flex items-center gap-2 mb-2">
            <div
              class="text-[11px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-md"
              :class="isToday(date)
                ? 'bg-emerald-100 text-emerald-700'
                : 'bg-slate-100 text-slate-500'"
            >
              {{ isToday(date) ? 'Hoy' : fmtDate(date) }}
            </div>
          </div>

          <!-- Cards -->
          <div class="space-y-2">
            <div
              v-for="m in dayMeetings"
              :key="m.id"
              class="bg-white border rounded-xl p-3 cursor-pointer transition-all hover:shadow-sm"
              :class="[
                selected?.id === m.id ? 'border-emerald-400 ring-1 ring-emerald-400/30' : 'border-slate-200',
                isPast(m) ? 'opacity-60' : '',
              ]"
              @click="selected = m"
            >
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0 flex-1">
                  <p class="text-sm font-semibold text-slate-800 truncate">{{ m.title }}</p>
                  <p class="text-xs text-slate-400 mt-0.5">
                    {{ m.start_time.slice(0, 5) }} – {{ m.end_time.slice(0, 5) }}
                  </p>
                </div>
                <div
                  class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                  style="background-color: #EEF2EE;"
                >
                  <UIcon name="i-lucide-video" class="w-3.5 h-3.5" style="color: #5B7C6B;" />
                </div>
              </div>
              <div v-if="m.room_name" class="flex items-center gap-1 mt-2 text-[11px] text-slate-400">
                <UIcon name="i-lucide-door-open" class="w-3 h-3" />
                {{ m.room_name }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Detail panel -->
      <div class="flex-1">
        <div
          v-if="!selected"
          class="h-full flex items-center justify-center text-slate-300 bg-slate-50 rounded-xl border border-dashed border-slate-200"
        >
          <div class="text-center">
            <UIcon name="i-lucide-mouse-pointer-click" class="w-8 h-8 mx-auto mb-2" />
            <p class="text-sm">Selecciona una junta para ver los detalles</p>
          </div>
        </div>

        <div
          v-else
          class="bg-white border rounded-xl overflow-hidden"
          style="border-color: #E5E7EB;"
        >
          <!-- Top bar -->
          <div class="h-1.5 bg-sage-600" />
          <div class="p-6">
            <div class="flex items-start justify-between gap-4 mb-4">
              <div>
                <h3 class="text-xl font-bold text-slate-800">{{ selected.title }}</h3>
                <p v-if="selected.description" class="text-sm text-slate-500 mt-1">
                  {{ selected.description }}
                </p>
              </div>
              <button
                class="text-red-400 hover:text-red-600 text-xs flex items-center gap-1 transition-colors"
                @click="deleteMeeting(selected.id)"
              >
                <UIcon name="i-lucide-trash-2" class="w-4 h-4" />
              </button>
            </div>

            <!-- Info grid -->
            <div class="grid grid-cols-2 gap-4 mb-6">
              <div class="flex items-center gap-3 text-sm text-slate-600">
                <div class="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center flex-shrink-0">
                  <UIcon name="i-lucide-calendar" class="w-4 h-4 text-slate-400" />
                </div>
                <div>
                  <p class="text-[11px] text-slate-400 uppercase font-semibold">Fecha</p>
                  <p>{{ fmtDate(selected.date) }}</p>
                </div>
              </div>
              <div class="flex items-center gap-3 text-sm text-slate-600">
                <div class="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center flex-shrink-0">
                  <UIcon name="i-lucide-clock" class="w-4 h-4 text-slate-400" />
                </div>
                <div>
                  <p class="text-[11px] text-slate-400 uppercase font-semibold">Hora</p>
                  <p>{{ selected.start_time.slice(0, 5) }} – {{ selected.end_time.slice(0, 5) }}</p>
                </div>
              </div>
              <div class="flex items-center gap-3 text-sm text-slate-600">
                <div class="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center flex-shrink-0">
                  <UIcon name="i-lucide-user-round" class="w-4 h-4 text-slate-400" />
                </div>
                <div>
                  <p class="text-[11px] text-slate-400 uppercase font-semibold">Organiza</p>
                  <p>{{ selected.organizer_name }}</p>
                </div>
              </div>
              <div v-if="selected.room_name" class="flex items-center gap-3 text-sm text-slate-600">
                <div class="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center flex-shrink-0">
                  <UIcon name="i-lucide-door-open" class="w-4 h-4 text-slate-400" />
                </div>
                <div>
                  <p class="text-[11px] text-slate-400 uppercase font-semibold">Sala</p>
                  <p>{{ selected.room_name }}</p>
                </div>
              </div>
            </div>

            <!-- Participants -->
            <div>
              <p class="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">
                Participantes ({{ selected.participants_detail?.length ?? 0 }})
              </p>
              <div
                v-if="!selected.participants_detail?.length"
                class="text-sm text-slate-400"
              >
                Sin participantes asignados
              </div>
              <div class="flex flex-wrap gap-2">
                <div
                  v-for="p in selected.participants_detail"
                  :key="p.id"
                  class="flex items-center gap-2 bg-slate-50 rounded-lg px-3 py-1.5"
                >
                  <div
                    class="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold text-white flex-shrink-0 bg-sage-600"
                  >
                    {{ p.full_name[0] }}
                  </div>
                  <div>
                    <p class="text-xs font-semibold text-slate-700">{{ p.full_name }}</p>
                    <p class="text-[10px] text-slate-400 truncate">{{ p.email }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create meeting modal -->
    <UModal v-model:open="showForm">
      <template #content>
        <div class="p-6 w-full max-w-lg">
          <h3 class="text-base font-semibold text-slate-800 mb-5">Nueva junta</h3>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Título *</label>
              <input
                v-model="form.title"
                type="text"
                placeholder="Revisión semanal del equipo"
                class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
                style="border-color: #D1D5DB;"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Descripción</label>
              <textarea
                v-model="form.description"
                rows="2"
                class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none resize-none"
                style="border-color: #D1D5DB;"
              />
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Fecha *</label>
                <input
                  v-model="form.date"
                  type="date"
                  class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none"
                  style="border-color: #D1D5DB;"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Sala</label>
                <USelect
                  v-model="form.room"
                  :items="roomItems"
                  value-attribute="value"
                  label-attribute="label"
                  class="w-full text-sm"
                />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Inicio *</label>
                <input
                  v-model="form.start_time"
                  type="time"
                  class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none"
                  style="border-color: #D1D5DB;"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Fin *</label>
                <input
                  v-model="form.end_time"
                  type="time"
                  class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none"
                  style="border-color: #D1D5DB;"
                />
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Organizador *</label>
              <USelect
                v-model="form.organizer"
                :items="memberItems"
                value-attribute="value"
                label-attribute="label"
                class="w-full"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">
                Participantes
              </label>
              <div class="space-y-1.5 max-h-36 overflow-y-auto">
                <label
                  v-for="m in members"
                  :key="m.id"
                  class="flex items-center gap-2.5 px-3 py-2 rounded-lg hover:bg-slate-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    :value="m.user"
                    v-model="form.participants"
                    class="rounded"
                  />
                  <span class="text-sm text-slate-700">{{ m.user_full_name }}</span>
                  <span class="text-xs text-slate-400 capitalize">{{ m.role }}</span>
                </label>
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-2 mt-6 pt-4 border-t" style="border-color: #F3F4F6;">
            <UButton variant="ghost" color="neutral" @click="showForm = false">Cancelar</UButton>
            <UButton
              :loading="saving"
              :disabled="!form.title || !form.date || !form.start_time || !form.end_time || !form.organizer"
              @click="save"
            >
              Crear junta
            </UButton>
          </div>
        </div>
      </template>
    </UModal>

  </div>
</template>
