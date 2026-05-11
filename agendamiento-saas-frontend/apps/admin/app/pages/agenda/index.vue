<script setup lang="ts">
import type { Appointment, PaginatedResponse, Doctor, Room, Membership } from '@agendamiento/shared'

definePageMeta({ middleware: ['tenant', 'auth'] })

const { apiFetch } = useApi()

// ── Week navigation ───────────────────────────────────────────────────────────
const baseDate = ref(startOfWeek(new Date()))
const weekDays = computed(() => Array.from({ length: 7 }, (_, i) => addDays(baseDate.value, i)))
const weekLabel = computed(() => `${fmtShort(weekDays.value[0])} – ${fmtShort(weekDays.value[6])}`)

// ── State ─────────────────────────────────────────────────────────────────────
const doctors      = ref<Doctor[]>([])
const appointments = ref<Appointment[]>([])
const selectedAppt = ref<Appointment | null>(null)
const popupAnchor  = ref<{ x: number; y: number } | null>(null)

function openPopup(appt: Appointment, evt: MouseEvent) {
  selectedAppt.value = appt
  const rect = (evt.currentTarget as HTMLElement).getBoundingClientRect()
  const POPUP_W = 320
  const POPUP_H = 420
  const x = Math.min(rect.right + 8, window.innerWidth  - POPUP_W - 8)
  const y = Math.min(rect.top,        window.innerHeight - POPUP_H - 8)
  popupAnchor.value = { x: Math.max(8, x), y: Math.max(8, y) }
}
function closePopup() { selectedAppt.value = null; popupAnchor.value = null }

// ── Clinical record edit ────────────────────────────────────────────────────
const savingClinical = ref(false)
const clinicalForm = reactive({
  weight_kg:      '' as string,
  height_cm:      '' as string,
  blood_pressure: '',
  heart_rate:     null as number | null,
  temperature_c:  '' as string,
  oxygen_sat:     null as number | null,
  clinical_notes: '',
})

watch(selectedAppt, (a) => {
  if (!a) return
  clinicalForm.weight_kg      = a.weight_kg      ?? ''
  clinicalForm.height_cm      = a.height_cm      ?? ''
  clinicalForm.blood_pressure = a.blood_pressure ?? ''
  clinicalForm.heart_rate     = a.heart_rate
  clinicalForm.temperature_c  = a.temperature_c  ?? ''
  clinicalForm.oxygen_sat     = a.oxygen_sat
  clinicalForm.clinical_notes = a.clinical_notes ?? ''
})

async function saveClinical() {
  if (!selectedAppt.value) return
  savingClinical.value = true
  try {
    const body: Record<string, any> = {
      blood_pressure: clinicalForm.blood_pressure,
      clinical_notes: clinicalForm.clinical_notes,
      heart_rate:     clinicalForm.heart_rate || null,
      oxygen_sat:     clinicalForm.oxygen_sat || null,
      weight_kg:      clinicalForm.weight_kg      === '' ? null : clinicalForm.weight_kg,
      height_cm:      clinicalForm.height_cm      === '' ? null : clinicalForm.height_cm,
      temperature_c:  clinicalForm.temperature_c  === '' ? null : clinicalForm.temperature_c,
    }
    const updated = await apiFetch<Appointment>(`/bookings/appointments/${selectedAppt.value.id}/`, {
      method: 'PATCH', body,
    })
    Object.assign(selectedAppt.value, updated)
    const idx = appointments.value.findIndex(a => a.id === updated.id)
    if (idx !== -1) appointments.value[idx] = { ...appointments.value[idx], ...updated }
  } finally {
    savingClinical.value = false
  }
}

async function updateStatus(appt: Appointment, newStatus: string) {
  try {
    await apiFetch(`/bookings/appointments/${appt.id}/`, {
      method: 'PATCH',
      body: { status: newStatus },
    })
    appt.status = newStatus as Appointment['status']
    if (selectedAppt.value?.id === appt.id) selectedAppt.value = { ...appt }
  } catch { /* silently ignore */ }
}

// ── Role-based view ──────────────────────────────────────────────────────────
const { isDoctor, isAdmin } = useRole()
const myDoctorId = ref<string | null>(null)

async function ensureMyDoctor() {
  if (!isDoctor.value || myDoctorId.value) return
  try {
    const me = await apiFetch<{ id: string }>('/catalog/doctors/me/')
    myDoctorId.value = me.id
    selectedDoctor.value = me.id
  } catch { /* user has no doctor profile */ }
}

// ── Create meeting (click on empty calendar cell) ────────────────────────────
const rooms             = ref<Room[]>([])
const members           = ref<Membership[]>([])
const showCreateMeeting = ref(false)
const savingMeeting     = ref(false)
const meetingForm = reactive({
  title:        '',
  description:  '',
  organizer:    null as number | null,
  participants: [] as number[],
  room:         '',
  date:         '',
  start_time:   '',
  end_time:     '',
})

function openCreateMeeting(day: Date, evt: MouseEvent) {
  // Compute time from click Y position relative to the time-grid body
  const target = evt.currentTarget as HTMLElement
  const rect   = target.getBoundingClientRect()
  const offsetY = evt.clientY - rect.top
  const minutesFromStart = (offsetY / HOUR_PX) * 60
  // Snap to nearest 15-min slot
  const snapped = Math.floor(minutesFromStart / 15) * 15
  const totalMins = HOUR_START * 60 + snapped
  const sh = Math.floor(totalMins / 60)
  const sm = totalMins % 60
  const eh = Math.floor((totalMins + 30) / 60)
  const em = (totalMins + 30) % 60

  meetingForm.title        = ''
  meetingForm.description  = ''
  meetingForm.organizer    = members.value[0]?.user ?? null
  meetingForm.participants = []
  meetingForm.room         = ''
  meetingForm.date         = toISO(day)
  meetingForm.start_time   = `${String(sh).padStart(2, '0')}:${String(sm).padStart(2, '0')}`
  meetingForm.end_time     = `${String(eh).padStart(2, '0')}:${String(em).padStart(2, '0')}`
  showCreateMeeting.value  = true
}

async function saveMeeting() {
  savingMeeting.value = true
  try {
    await apiFetch('/meetings/meetings/', {
      method: 'POST',
      body: { ...meetingForm, room: meetingForm.room || null },
    })
    showCreateMeeting.value = false
  } finally {
    savingMeeting.value = false
  }
}

const roomItems = computed(() => [
  { label: 'Sin sala asignada', value: '' },
  ...rooms.value.map(r => ({ label: `${r.name} — ${r.branch_name}`, value: r.id })),
])
const memberItems = computed(() =>
  members.value.map(m => ({
    label: `${m.user_full_name}${m.role !== 'doctor' ? ` (${m.role})` : ''}`,
    value: m.user,
  }))
)
const selectedDoctor = ref<string>('all')
const loading = ref(false)

// ── Time grid config ──────────────────────────────────────────────────────────
const HOUR_START  = 8
const HOUR_END    = 20
const HOUR_PX     = 80
const TOTAL_HOURS = HOUR_END - HOUR_START
const hours       = Array.from({ length: TOTAL_HOURS }, (_, i) => HOUR_START + i)

// Current time indicator
const now = ref(new Date())
const nowTop = computed(() => {
  const mins   = now.value.getHours() * 60 + now.value.getMinutes()
  const offset = mins - HOUR_START * 60
  return offset < 0 ? -999 : (offset / 60) * HOUR_PX
})
let clockTimer: ReturnType<typeof setInterval>
onMounted(() => { clockTimer = setInterval(() => { now.value = new Date() }, 30000) })
onUnmounted(() => clearInterval(clockTimer))

// ── Data ─────────────────────────────────────────────────────────────────────
async function load() {
  loading.value = true
  try {
    const from = toISO(weekDays.value[0])
    const to   = toISO(weekDays.value[6])
    const [docs, appts, rms, mbs] = await Promise.all([
      apiFetch<PaginatedResponse<Doctor>>('/catalog/doctors/'),
      apiFetch<PaginatedResponse<Appointment>>('/bookings/appointments/', {
        params: {
          from_date: from,
          to_date: to,
          ...(selectedDoctor.value && selectedDoctor.value !== 'all' ? { doctor: selectedDoctor.value } : {})
        }
      }),
      apiFetch<PaginatedResponse<Room>>('/meetings/rooms/', { params: { active: 'true' } }),
      apiFetch<PaginatedResponse<Membership>>('/accounts/memberships/'),
    ])
    doctors.value      = docs.results
    appointments.value = appts.results
    rooms.value        = rms.results
    members.value      = mbs.results
  }
  finally { loading.value = false }
}

onMounted(async () => {
  await ensureMyDoctor()
  await load()
})

function forDay(day: Date): Appointment[] {
  const iso = toISO(day)
  return appointments.value
    .filter(a => a.date === iso)
    .sort((a, b) => a.start_time.localeCompare(b.start_time))
}

// ── Positioning ───────────────────────────────────────────────────────────────
function timeToMins(t: string): number {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}
function apptTop(appt: Appointment): number {
  const mins = timeToMins(appt.start_time) - HOUR_START * 60
  return Math.max(0, (mins / 60) * HOUR_PX)
}
function apptHeight(appt: Appointment): number {
  const start = timeToMins(appt.start_time)
  const end   = timeToMins(appt.end_time)
  const mins  = Math.max(end - start, 15)
  return Math.max((mins / 60) * HOUR_PX, 28)
}

// Sweep-line layout: active and cancelled are laid out independently
// so cancelled appointments never shrink active ones.
type Slot = { appt: Appointment; col: number; cols: number; mini: boolean }

function sweep(list: Appointment[]): { appt: Appointment; col: number; cols: number }[] {
  const colEnd: number[] = []
  const assigned: { appt: Appointment; col: number }[] = []
  for (const appt of list) {
    const s = timeToMins(appt.start_time)
    const e = timeToMins(appt.end_time)
    let col = colEnd.findIndex(et => et <= s)
    if (col === -1) { col = colEnd.length; colEnd.push(e) }
    else colEnd[col] = e
    assigned.push({ appt, col })
  }
  return assigned.map(({ appt, col }) => {
    const s = timeToMins(appt.start_time)
    const e = timeToMins(appt.end_time)
    const maxCol = assigned
      .filter(({ appt: o }) => timeToMins(o.start_time) < e && timeToMins(o.end_time) > s)
      .reduce((m, { col: c }) => Math.max(m, c), 0)
    return { appt, col, cols: maxCol + 1 }
  })
}

function layoutDay(day: Date): Slot[] {
  const all = forDay(day)
  if (all.length === 0) return []
  const active    = all.filter(a => a.status !== 'cancelled')
  const cancelled = all.filter(a => a.status === 'cancelled')
  return [
    ...sweep(active).map(s => ({ ...s, mini: false })),
    ...sweep(cancelled).map(s => ({ ...s, mini: true })),
  ]
}

// ── Status styles ─────────────────────────────────────────────────────────────
const STATUS_STYLE: Record<string, { bg: string; border: string; text: string; dot: string }> = {
  pending:   { bg: '#FEF3C7', border: '#D97706', text: '#92400E', dot: '#D97706' },
  confirmed: { bg: '#DCE8E0', border: '#5B7C6B', text: '#2E4235', dot: '#5B7C6B' },
  completed: { bg: '#DBEAFE', border: '#2563EB', text: '#1E3A8A', dot: '#2563EB' },
  cancelled: { bg: '#F3F4F6', border: '#9CA3AF', text: '#6B7280', dot: '#9CA3AF' },
}
const STATUS_LABEL: Record<string, string> = {
  pending: 'Pendiente', confirmed: 'Confirmada',
  completed: 'Completada', cancelled: 'Cancelada',
}

// ── Navigation ────────────────────────────────────────────────────────────────
function prevWeek() { baseDate.value = addDays(baseDate.value, -7); load() }
function nextWeek() { baseDate.value = addDays(baseDate.value, 7);  load() }
function goToday()  { baseDate.value = startOfWeek(new Date());     load() }

const doctorItems = computed(() => [
  { label: 'Todos los doctores', value: 'all' },
  ...doctors.value.map(d => ({ label: d.full_name, value: d.id }))
])

watch(selectedDoctor, load)

// ── Date helpers ──────────────────────────────────────────────────────────────
function startOfWeek(d: Date): Date {
  const r    = new Date(d)
  const diff = d.getDay() === 0 ? -6 : 1 - d.getDay()
  r.setDate(d.getDate() + diff)
  r.setHours(0, 0, 0, 0)
  return r
}
function addDays(d: Date, n: number): Date {
  const r = new Date(d); r.setDate(d.getDate() + n); return r
}
function toISO(d: Date)      { return d.toISOString().slice(0, 10) }
function fmtShort(d: Date)   { return d.toLocaleDateString('es-MX', { day: 'numeric', month: 'short' }) }
function fmtWeekday(d: Date) { return d.toLocaleDateString('es-MX', { weekday: 'short' }).replace('.', '').toUpperCase() }
function isToday(d: Date)    { return toISO(d) === toISO(new Date()) }
function fmtHour(h: number)  { return h < 12 ? `${h} AM` : h === 12 ? '12 PM' : `${h - 12} PM` }
</script>

<template>
  <div class="flex flex-col h-full -m-6 bg-white dark:bg-slate-900">

    <!-- ── Toolbar ─────────────────────────────────────────────────────────── -->
    <div
      class="flex flex-wrap items-center justify-between gap-3 px-6 py-3 border-b bg-white dark:bg-slate-900 flex-shrink-0"
      style="border-color: #E5E7EB;"
    >
      <div>
        <h1 class="text-lg font-semibold text-slate-800 dark:text-slate-100">Agenda</h1>
        <p class="text-xs text-slate-400 capitalize">
          {{ new Date().toLocaleDateString('es-MX', { weekday: 'long', day: 'numeric', month: 'long' }) }}
        </p>
      </div>

      <div class="flex items-center gap-2 flex-wrap">
        <USelect
          v-if="isAdmin"
          v-model="selectedDoctor"
          :items="doctorItems"
          value-attribute="value"
          label-attribute="label"
          class="w-48 text-sm"
        />

        <button
          class="text-sm font-medium px-3 py-1.5 rounded-md border transition-colors hover:bg-slate-50 dark:hover:bg-slate-800"
          style="border-color: #D1D5DB; color: #374151;"
          @click="goToday"
        >
          Hoy
        </button>

        <div class="flex items-center rounded-md border overflow-hidden" style="border-color: #D1D5DB;">
          <button
            class="px-2 py-1.5 text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors border-r"
            style="border-color: #D1D5DB;"
            @click="prevWeek"
          >
            <UIcon name="i-lucide-chevron-left" class="w-4 h-4" />
          </button>
          <span class="text-sm font-medium text-slate-700 dark:text-slate-200 px-3 min-w-36 text-center">
            {{ weekLabel }}
          </span>
          <button
            class="px-2 py-1.5 text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors border-l"
            style="border-color: #D1D5DB;"
            @click="nextWeek"
          >
            <UIcon name="i-lucide-chevron-right" class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- ── Loading ─────────────────────────────────────────────────────────── -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <UIcon name="i-lucide-loader-2" class="animate-spin w-6 h-6 text-slate-400" />
    </div>

    <!-- ── Calendar grid ───────────────────────────────────────────────────── -->
    <div v-else class="flex-1 overflow-auto">
      <div class="flex min-w-[640px]">

        <!-- Time gutter -->
        <div class="w-16 flex-shrink-0 bg-white dark:bg-slate-900">
          <!-- Corner -->
          <div class="h-[60px] border-b border-r" style="border-color: #E5E7EB;" />
          <!-- Hour labels centered ON each line -->
          <div class="relative border-r" style="border-color: #E5E7EB; height: calc(var(--total-h) * 1px);"
               :style="`height: ${TOTAL_HOURS * HOUR_PX}px;`">
            <div
              v-for="h in hours"
              :key="h"
              class="absolute right-0 flex items-center justify-end pr-2 pointer-events-none"
              :style="`top: ${(h - HOUR_START) * HOUR_PX}px;`"
            >
              <span
                class="text-[10px] font-medium text-slate-400 select-none"
                style="transform: translateY(-50%);"
              >{{ fmtHour(h) }}</span>
            </div>
          </div>
        </div>

        <!-- Day columns -->
        <div class="flex-1 grid grid-cols-7">
          <div
            v-for="day in weekDays"
            :key="toISO(day)"
            class="border-r last:border-r-0"
            style="border-color: #E5E7EB;"
          >
            <!-- Day header -->
            <div
              class="h-[60px] flex flex-col items-center justify-center gap-0.5 border-b sticky top-0 z-10 bg-white dark:bg-slate-900"
              style="border-color: #E5E7EB;"
            >
              <span
                class="text-[10px] font-semibold tracking-widest"
                :style="isToday(day) ? 'color: #5B7C6B;' : 'color: #9CA3AF;'"
              >
                {{ fmtWeekday(day) }}
              </span>
              <div
                class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors"
                :style="isToday(day)
                  ? 'background-color: #5B7C6B; color: white;'
                  : 'color: #111827;'"
              >
                {{ day.getDate() }}
              </div>
            </div>

            <!-- Time grid body -->
            <div
              class="relative cursor-pointer"
              :style="`height: ${TOTAL_HOURS * HOUR_PX}px;`"
              @click="openCreateMeeting(day, $event)"
            >
              <!-- Hour lines (full width) -->
              <div
                v-for="h in hours"
                :key="h"
                class="absolute w-full border-t"
                :style="`top: ${(h - HOUR_START) * HOUR_PX}px; border-color: #E5E7EB;`"
              />

              <!-- Half-hour dashed lines -->
              <div
                v-for="h in hours"
                :key="`half-${h}`"
                class="absolute w-full border-t border-dashed"
                :style="`top: ${(h - HOUR_START) * HOUR_PX + HOUR_PX / 2}px; border-color: #F3F4F6;`"
              />

              <!-- Today column tint -->
              <div
                v-if="isToday(day)"
                class="absolute inset-0 pointer-events-none"
                style="background-color: rgba(91,124,107,0.03);"
              />

              <!-- Current time indicator -->
              <template v-if="isToday(day) && nowTop >= 0 && nowTop <= TOTAL_HOURS * HOUR_PX">
                <div
                  class="absolute left-0 right-0 z-20 pointer-events-none"
                  :style="`top: ${nowTop}px;`"
                >
                  <div class="relative flex items-center">
                    <div
                      class="absolute w-3 h-3 rounded-full -left-1.5 flex-shrink-0"
                      style="background-color: #5B7C6B;"
                    />
                    <div class="w-full h-[2px]" style="background-color: #5B7C6B;" />
                  </div>
                </div>
              </template>

              <!-- Appointments -->
              <template v-for="{ appt, col, cols, mini } in layoutDay(day)" :key="appt.id">
                <!-- Cancelled: thin strip on the right edge -->
                <div
                  v-if="mini"
                  class="absolute rounded-[3px] overflow-hidden cursor-pointer opacity-50 hover:opacity-80 transition-opacity"
                  :style="{
                    top:        `${apptTop(appt) + 1}px`,
                    height:     `${apptHeight(appt) - 2}px`,
                    right:      `${col * 10 + 2}px`,
                    width:      '8px',
                    backgroundColor: STATUS_STYLE.cancelled.border,
                  }"
                  :title="`${appt.patient_name} — Cancelada`"
                />

                <!-- Active appointments: full sweep-line layout -->
                <div
                  v-else
                  class="absolute overflow-hidden cursor-pointer transition-all duration-100 hover:z-30 hover:shadow-md rounded-[4px]"
                  :style="{
                    top:             `${apptTop(appt) + 1}px`,
                    height:          `${apptHeight(appt) - 2}px`,
                    left:            `calc(${(col / cols) * 100}% + 2px)`,
                    width:           `calc(${(1 / cols) * 100}% - 4px)`,
                    backgroundColor: (STATUS_STYLE[appt.status] ?? STATUS_STYLE.pending).bg,
                    borderLeft:      `3px solid ${(STATUS_STYLE[appt.status] ?? STATUS_STYLE.pending).border}`,
                    color:           (STATUS_STYLE[appt.status] ?? STATUS_STYLE.pending).text,
                    paddingLeft:     '6px',
                    paddingRight:    '4px',
                    paddingTop:      '2px',
                    paddingBottom:   '2px',
                  }"
                  @click.stop="openPopup(appt, $event)"
                >
                  <p class="text-[10px] font-semibold font-mono leading-none mb-0.5 opacity-80">
                    {{ appt.start_time?.slice(0, 5) }}
                  </p>
                  <p class="text-[11px] font-semibold leading-tight truncate">
                    {{ appt.patient_name }}
                  </p>
                  <p
                    v-if="apptHeight(appt) > 46"
                    class="text-[10px] leading-tight truncate opacity-70 mt-0.5"
                  >
                    {{ appt.service_name }}
                  </p>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Legend ──────────────────────────────────────────────────────────── -->
    <div
      class="flex items-center gap-4 px-6 py-2 border-t bg-white dark:bg-slate-900 flex-shrink-0 flex-wrap"
      style="border-color: #E5E7EB;"
    >
      <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Estado</span>
      <div
        v-for="(style, key) in STATUS_STYLE"
        :key="key"
        class="flex items-center gap-1.5 text-[11px] font-medium"
        :style="`color: ${style.text};`"
      >
        <span class="w-2 h-2 rounded-full flex-shrink-0" :style="`background-color: ${style.dot};`" />
        {{ STATUS_LABEL[key] }}
      </div>
    </div>

    <!-- ── Create meeting modal (click on empty cell) ──────────────────────── -->
    <UModal v-model:open="showCreateMeeting">
      <template #content>
        <div class="p-6 w-full max-w-lg">
          <div class="flex items-center gap-2 mb-5">
            <div
              class="w-9 h-9 rounded-lg flex items-center justify-center"
              style="background-color: #EEF2EE;"
            >
              <UIcon name="i-lucide-video" class="w-4 h-4" style="color: #5B7C6B;" />
            </div>
            <div>
              <h3 class="text-base font-semibold text-slate-800">Nueva junta</h3>
              <p class="text-xs text-slate-400">
                {{ meetingForm.date }} · {{ meetingForm.start_time }}
              </p>
            </div>
          </div>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Título *</label>
              <input
                v-model="meetingForm.title"
                type="text"
                placeholder="Ej. Reunión clínica semanal"
                class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none"
                style="border-color: #D1D5DB;"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Descripción</label>
              <textarea
                v-model="meetingForm.description"
                rows="2"
                class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none resize-none"
                style="border-color: #D1D5DB;"
              />
            </div>

            <div class="grid grid-cols-3 gap-3">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Fecha *</label>
                <input
                  v-model="meetingForm.date"
                  type="date"
                  class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none"
                  style="border-color: #D1D5DB;"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Inicio *</label>
                <input
                  v-model="meetingForm.start_time"
                  type="time"
                  class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none"
                  style="border-color: #D1D5DB;"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Fin *</label>
                <input
                  v-model="meetingForm.end_time"
                  type="time"
                  class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none"
                  style="border-color: #D1D5DB;"
                />
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Sala</label>
              <USelect
                v-model="meetingForm.room"
                :items="roomItems"
                value-attribute="value"
                label-attribute="label"
                class="w-full"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Organizador *</label>
              <USelect
                v-model="meetingForm.organizer"
                :items="memberItems"
                value-attribute="value"
                label-attribute="label"
                class="w-full"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">Participantes</label>
              <div class="space-y-1 max-h-32 overflow-y-auto border rounded-lg p-2" style="border-color: #E5E7EB;">
                <label
                  v-for="m in members"
                  :key="m.id"
                  class="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-slate-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    :value="m.user"
                    v-model="meetingForm.participants"
                  />
                  <span class="text-sm text-slate-700">{{ m.user_full_name }}</span>
                  <span class="text-xs text-slate-400 ml-auto capitalize">{{ m.role }}</span>
                </label>
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-2 mt-6 pt-4 border-t" style="border-color: #F3F4F6;">
            <button
              class="px-4 py-2 text-sm font-medium text-slate-600 border rounded-lg hover:bg-slate-50 transition-colors"
              style="border-color: #D1D5DB;"
              @click="showCreateMeeting = false"
            >
              Cancelar
            </button>
            <button
              class="px-4 py-2 text-sm font-semibold text-white rounded-lg transition-colors disabled:opacity-60"
              style="background-color: #5B7C6B;"
              :disabled="savingMeeting || !meetingForm.title || !meetingForm.organizer"
              @click="saveMeeting"
            >
              {{ savingMeeting ? 'Creando…' : 'Crear junta' }}
            </button>
          </div>
        </div>
      </template>
    </UModal>

    <!-- ── Appointment detail popup ──────────────────────────────────────── -->
    <Teleport to="body">
      <div
        v-if="selectedAppt && popupAnchor"
        class="fixed inset-0 z-50"
        @click.self="closePopup"
      >
        <div
          class="absolute bg-white rounded-xl shadow-2xl border w-80"
          style="border-color: #E5E7EB; max-height: 90vh; overflow-y: auto;"
          :style="{
            left: `${popupAnchor.x}px`,
            top:  `${popupAnchor.y}px`,
          }"
          @click.stop
        >
          <!-- Header colored strip -->
          <div
            class="h-1.5 rounded-t-xl"
            :style="`background-color: ${(STATUS_STYLE[selectedAppt.status] ?? STATUS_STYLE.pending).border};`"
          />

          <div class="p-4">
            <!-- Top row -->
            <div class="flex items-start justify-between gap-2 mb-3">
              <div class="flex-1 min-w-0">
                <p class="text-base font-bold text-slate-800 leading-tight">
                  {{ selectedAppt.patient_name }}
                </p>
                <p class="text-sm text-slate-500 mt-0.5">{{ selectedAppt.service_name }}</p>
              </div>
              <button
                class="text-slate-400 hover:text-slate-600 flex-shrink-0 p-0.5 rounded"
                @click="closePopup"
              >
                <UIcon name="i-lucide-x" class="w-4 h-4" />
              </button>
            </div>

            <!-- Status badge -->
            <span
              class="inline-flex items-center gap-1.5 text-xs font-semibold px-2 py-0.5 rounded-full mb-3"
              :style="{
                backgroundColor: (STATUS_STYLE[selectedAppt.status] ?? STATUS_STYLE.pending).bg,
                color: (STATUS_STYLE[selectedAppt.status] ?? STATUS_STYLE.pending).text,
              }"
            >
              <span
                class="w-1.5 h-1.5 rounded-full"
                :style="`background-color: ${(STATUS_STYLE[selectedAppt.status] ?? STATUS_STYLE.pending).dot};`"
              />
              {{ STATUS_LABEL[selectedAppt.status] ?? selectedAppt.status }}
            </span>

            <!-- Details list -->
            <div class="space-y-2 text-sm mb-4">
              <div class="flex items-center gap-2 text-slate-600">
                <UIcon name="i-lucide-calendar" class="w-4 h-4 text-slate-400 flex-shrink-0" />
                <span>{{ new Date(selectedAppt.date + 'T00:00').toLocaleDateString('es-MX', { weekday: 'long', day: 'numeric', month: 'long' }) }}</span>
              </div>
              <div class="flex items-center gap-2 text-slate-600">
                <UIcon name="i-lucide-clock" class="w-4 h-4 text-slate-400 flex-shrink-0" />
                <span>{{ selectedAppt.start_time?.slice(0, 5) }} – {{ selectedAppt.end_time?.slice(0, 5) }}</span>
              </div>
              <div class="flex items-center gap-2 text-slate-600">
                <UIcon name="i-lucide-user-round" class="w-4 h-4 text-slate-400 flex-shrink-0" />
                <span>{{ selectedAppt.doctor_name }}</span>
              </div>
              <div v-if="selectedAppt.patient_phone" class="flex items-center gap-2 text-slate-600">
                <UIcon name="i-lucide-phone" class="w-4 h-4 text-slate-400 flex-shrink-0" />
                <span>{{ selectedAppt.patient_phone }}</span>
              </div>
              <div v-if="selectedAppt.patient_email" class="flex items-center gap-2 text-slate-600">
                <UIcon name="i-lucide-mail" class="w-4 h-4 text-slate-400 flex-shrink-0" />
                <span class="truncate">{{ selectedAppt.patient_email }}</span>
              </div>
              <div v-if="selectedAppt.notes" class="flex items-start gap-2 text-slate-600">
                <UIcon name="i-lucide-file-text" class="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
                <span class="text-xs">{{ selectedAppt.notes }}</span>
              </div>
            </div>

            <!-- Status actions -->
            <div class="border-t pt-3" style="border-color: #F3F4F6;">
              <p class="text-[11px] font-semibold text-slate-400 uppercase tracking-wide mb-2">Cambiar estado</p>
              <div class="flex flex-wrap gap-1.5">
                <button
                  v-for="(st, key) in STATUS_STYLE"
                  :key="key"
                  class="text-xs font-medium px-2.5 py-1 rounded-lg border transition-all"
                  :class="selectedAppt.status === key ? 'opacity-40 cursor-default' : 'hover:shadow-sm'"
                  :style="{
                    backgroundColor: st.bg,
                    borderColor: st.border,
                    color: st.text,
                  }"
                  :disabled="selectedAppt.status === key"
                  @click="updateStatus(selectedAppt, key)"
                >
                  {{ STATUS_LABEL[key] }}
                </button>
              </div>
            </div>

            <!-- Clinical record (vitals + notes) -->
            <div class="border-t pt-3 mt-3" style="border-color: #F3F4F6;">
              <p class="text-[11px] font-semibold text-slate-400 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                <UIcon name="i-lucide-stethoscope" class="w-3 h-3" />
                Notas clínicas
              </p>

              <!-- Vitals grid -->
              <div class="grid grid-cols-3 gap-2 mb-2">
                <div>
                  <label class="text-[10px] font-medium text-slate-500">Peso (kg)</label>
                  <input
                    v-model="clinicalForm.weight_kg"
                    type="number" step="0.01" placeholder="—"
                    class="w-full text-xs border rounded px-1.5 py-1 mt-0.5 focus:outline-none focus:ring-1 focus:ring-sage-500"
                    style="border-color: #E5E7EB;"
                  />
                </div>
                <div>
                  <label class="text-[10px] font-medium text-slate-500">Talla (cm)</label>
                  <input
                    v-model="clinicalForm.height_cm"
                    type="number" step="0.1" placeholder="—"
                    class="w-full text-xs border rounded px-1.5 py-1 mt-0.5 focus:outline-none focus:ring-1 focus:ring-sage-500"
                    style="border-color: #E5E7EB;"
                  />
                </div>
                <div>
                  <label class="text-[10px] font-medium text-slate-500">Presión</label>
                  <input
                    v-model="clinicalForm.blood_pressure"
                    type="text" placeholder="120/80"
                    class="w-full text-xs border rounded px-1.5 py-1 mt-0.5 focus:outline-none focus:ring-1 focus:ring-sage-500"
                    style="border-color: #E5E7EB;"
                  />
                </div>
                <div>
                  <label class="text-[10px] font-medium text-slate-500">FC (lpm)</label>
                  <input
                    v-model.number="clinicalForm.heart_rate"
                    type="number" placeholder="—"
                    class="w-full text-xs border rounded px-1.5 py-1 mt-0.5 focus:outline-none focus:ring-1 focus:ring-sage-500"
                    style="border-color: #E5E7EB;"
                  />
                </div>
                <div>
                  <label class="text-[10px] font-medium text-slate-500">Temp (°C)</label>
                  <input
                    v-model="clinicalForm.temperature_c"
                    type="number" step="0.1" placeholder="—"
                    class="w-full text-xs border rounded px-1.5 py-1 mt-0.5 focus:outline-none focus:ring-1 focus:ring-sage-500"
                    style="border-color: #E5E7EB;"
                  />
                </div>
                <div>
                  <label class="text-[10px] font-medium text-slate-500">SpO₂ (%)</label>
                  <input
                    v-model.number="clinicalForm.oxygen_sat"
                    type="number" min="0" max="100" placeholder="—"
                    class="w-full text-xs border rounded px-1.5 py-1 mt-0.5 focus:outline-none focus:ring-1 focus:ring-sage-500"
                    style="border-color: #E5E7EB;"
                  />
                </div>
              </div>

              <label class="text-[10px] font-medium text-slate-500">Observaciones</label>
              <textarea
                v-model="clinicalForm.clinical_notes"
                rows="3"
                placeholder="Motivo de consulta, diagnóstico, plan de tratamiento, etc."
                class="w-full text-xs border rounded px-2 py-1.5 mt-0.5 resize-none focus:outline-none focus:ring-1 focus:ring-sage-500"
                style="border-color: #E5E7EB;"
              />

              <div class="flex justify-end mt-2">
                <UButton
                  size="xs"
                  :loading="savingClinical"
                  @click="saveClinical"
                >
                  Guardar notas
                </UButton>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>
