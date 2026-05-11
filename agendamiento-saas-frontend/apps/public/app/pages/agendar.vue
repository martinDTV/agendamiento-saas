<script setup lang="ts">
import type { Doctor, Service, PaginatedResponse, Slot } from '@agendamiento/shared'

definePageMeta({ middleware: 'tenant' })

const booking = useBookingStore()
const { apiFetch } = useApi()
const toast = useToast()
const { content } = useContent()

const services = ref<Service[]>([])
const doctors = ref<Doctor[]>([])
const slots = ref<Slot[]>([])
const loadingSlots = ref(false)
const submitting = ref(false)
const reason = ref('')
const suggestedServiceIds = ref<string[]>([])
const suggestedDoctorIds = ref<string[]>([])
const loadingSuggest = ref(false)
const showReason = ref(false)

const today = new Date().toISOString().slice(0, 10)

// Sub-paso dentro del Step 1 (selección): 'service' | 'doctor' | 'date' | 'slot'
type SubStep = 'service' | 'doctor' | 'date' | 'slot'
const subStep = computed<SubStep>(() => {
  if (!booking.service) return 'service'
  if (!booking.doctor) return 'doctor'
  if (!booking.date) return 'date'
  return 'slot'
})

const subSteps: { id: SubStep; label: string; icon: string }[] = [
  { id: 'service', label: 'Servicio', icon: 'i-lucide-stethoscope' },
  { id: 'doctor',  label: 'Médico',   icon: 'i-lucide-user-round' },
  { id: 'date',    label: 'Fecha',    icon: 'i-lucide-calendar' },
  { id: 'slot',    label: 'Horario',  icon: 'i-lucide-clock' }
]

function isSubStepDone(id: SubStep): boolean {
  const order: SubStep[] = ['service', 'doctor', 'date', 'slot']
  return order.indexOf(id) < order.indexOf(subStep.value)
}

// Doctores filtrados por el servicio seleccionado.
const filteredDoctors = computed<Doctor[]>(() => {
  if (!booking.service) return []
  return doctors.value.filter(d =>
    d.is_active && (d.service_ids?.includes(booking.service!.id) ?? false)
  )
})

// Strip horizontal de 14 días desde hoy.
const dateStrip = computed(() => {
  const days = []
  const base = new Date()
  base.setHours(0, 0, 0, 0)
  for (let i = 0; i < 14; i++) {
    const d = new Date(base)
    d.setDate(base.getDate() + i)
    const iso = d.toISOString().slice(0, 10)
    days.push({
      iso,
      day: d.getDate(),
      weekday: d.toLocaleDateString('es-MX', { weekday: 'short' }).replace('.', ''),
      month: d.toLocaleDateString('es-MX', { month: 'short' }).replace('.', '')
    })
  }
  return days
})

const groupedSlots = computed(() => {
  const groups = { morning: [] as Slot[], afternoon: [] as Slot[], evening: [] as Slot[] }
  for (const s of slots.value) {
    const h = parseInt(s.start.slice(0, 2), 10)
    if (h < 12) groups.morning.push(s)
    else if (h < 18) groups.afternoon.push(s)
    else groups.evening.push(s)
  }
  return groups
})

async function loadCatalog() {
  const [s, d] = await Promise.all([
    apiFetch<PaginatedResponse<Service>>('/public/catalog/services/'),
    apiFetch<PaginatedResponse<Doctor>>('/public/catalog/doctors/')
  ])
  services.value = s.results.filter(x => x.is_active)
  doctors.value = d.results.filter(x => x.is_active)
}

async function loadSlots() {
  if (!booking.doctor || !booking.service || !booking.date) return
  loadingSlots.value = true
  slots.value = []
  try {
    slots.value = await apiFetch<Slot[]>('/public/slots/', {
      params: {
        doctor: booking.doctor.id,
        service: booking.service.id,
        date: booking.date
      }
    })
  }
  finally { loadingSlots.value = false }
}

watch([() => booking.doctor, () => booking.service, () => booking.date], loadSlots)

async function confirm() {
  if (!booking.slot || !booking.doctor || !booking.service || !booking.date) return
  submitting.value = true
  try {
    const res = await apiFetch<{ id: string }>('/public/appointments/', {
      method: 'POST',
      body: {
        doctor: booking.doctor.id,
        service: booking.service.id,
        date: booking.date,
        start_time: booking.slot.start,
        patient_name: booking.patientName,
        patient_email: booking.patientEmail,
        patient_phone: booking.patientPhone
      }
    })
    booking.appointmentId = res.id
    booking.goTo(3)
  }
  catch {
    toast.add({ title: 'No se pudo confirmar la cita. Intenta de nuevo.', color: 'error' })
  }
  finally { submitting.value = false }
}

async function getSuggestions() {
  if (!reason.value.trim()) return
  loadingSuggest.value = true
  try {
    const res = await apiFetch<{ service_ids: string[]; doctor_ids?: string[] }>('/public/ai/suggest/', {
      method: 'POST',
      body: { reason: reason.value }
    })
    suggestedServiceIds.value = res.service_ids
    suggestedDoctorIds.value = res.doctor_ids ?? []
    if (!booking.service && suggestedServiceIds.value.length > 0) {
      const s = services.value.find(x => x.id === suggestedServiceIds.value[0])
      if (s) booking.selectService(s)
    }
    if (!booking.doctor && suggestedDoctorIds.value.length > 0) {
      const d = filteredDoctors.value.find(x => x.id === suggestedDoctorIds.value[0])
        ?? doctors.value.find(x => x.id === suggestedDoctorIds.value[0])
      if (d) booking.selectDoctor(d)
    }
  }
  finally { loadingSuggest.value = false }
}

// Helpers para mostrar conteo de doctores por servicio
function doctorCountFor(s: Service): number {
  return doctors.value.filter(d => d.is_active && d.service_ids?.includes(s.id)).length
}

onMounted(loadCatalog)
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-10">
    <!-- Page title -->
    <div class="mb-6" v-if="booking.step < 3">
      <h1 class="text-2xl font-bold tracking-tight text-ink">{{ content.booking.pageTitle }}</h1>
      <p class="text-sm mt-1 text-ink-muted">{{ content.booking.pageSubtitle }}</p>
    </div>

    <!-- Step principal (1/2/3) -->
    <div v-if="booking.step < 3" class="flex items-center gap-3 mb-6">
      <template v-for="(label, i) in content.booking.stepLabels" :key="i">
        <div class="flex items-center gap-2">
          <div
            class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-all"
            :class="booking.step >= i + 1
              ? 'bg-sage-500 text-white'
              : 'bg-border text-ink-muted'"
          >
            <UIcon v-if="booking.step > i + 1" name="i-lucide-check" class="w-3 h-3" />
            <span v-else>{{ i + 1 }}</span>
          </div>
          <span
            class="text-sm font-medium"
            :class="booking.step === i + 1 ? 'text-ink' : 'text-ink-muted'"
          >
            {{ label }}
          </span>
        </div>
        <div v-if="i < 2" class="flex-1 h-px bg-border" />
      </template>
    </div>

    <!-- ── PASO 1: Selección lineal ── -->
    <template v-if="booking.step === 1">
      <!-- Sugerencia con IA (atajo para todo el paso 1) -->
      <section class="mb-5">
        <button
          type="button"
          class="w-full flex items-center justify-between gap-2 px-4 py-3 rounded-xl border border-sage-200 bg-sage-50 text-sage-700 hover:bg-sage-100 transition-all"
          @click="showReason = !showReason"
        >
          <span class="inline-flex items-center gap-2 text-sm font-medium">
            <UIcon name="i-lucide-sparkles" class="w-4 h-4" />
            ¿No sabés qué servicio elegir? Contanos qué te pasa
          </span>
          <UIcon
            :name="showReason ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
            class="w-4 h-4"
          />
        </button>
        <div v-if="showReason" class="mt-3 rounded-xl bg-white border border-sage-200 p-4">
          <div class="flex gap-2">
            <input
              v-model="reason"
              type="text"
              :placeholder="content.booking.step1.reasonPlaceholder"
              class="flex-1 text-sm px-3.5 py-2 rounded-lg border outline-none transition-all border-border-strong bg-white text-ink focus:border-sage-500"
              @keydown.enter.prevent="getSuggestions"
            />
            <button
              type="button"
              :disabled="!reason.trim() || loadingSuggest"
              class="flex items-center gap-1.5 text-sm font-medium px-4 py-2 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed bg-sage-500 hover:bg-sage-600 text-white"
              @click="getSuggestions"
            >
              <UIcon v-if="loadingSuggest" name="i-lucide-loader-2" class="w-3.5 h-3.5 animate-spin" />
              <UIcon v-else name="i-lucide-sparkles" class="w-3.5 h-3.5" />
              Sugerir
            </button>
          </div>
        </div>
      </section>

      <!-- Mini-stepper con los 4 sub-pasos -->
      <div class="grid grid-cols-4 gap-2 mb-6">
        <div
          v-for="s in subSteps"
          :key="s.id"
          class="flex flex-col items-center gap-1.5 p-2 rounded-lg transition-all"
          :class="subStep === s.id
            ? 'bg-sage-50 ring-1 ring-sage-200'
            : isSubStepDone(s.id)
              ? 'opacity-100'
              : 'opacity-50'"
        >
          <div
            class="w-7 h-7 rounded-full flex items-center justify-center text-white"
            :class="subStep === s.id
              ? 'bg-sage-500'
              : isSubStepDone(s.id)
                ? 'bg-sage-400'
                : 'bg-border'"
          >
            <UIcon v-if="isSubStepDone(s.id)" name="i-lucide-check" class="w-3.5 h-3.5" />
            <UIcon v-else :name="s.icon" class="w-3.5 h-3.5" />
          </div>
          <span class="text-[11px] font-medium text-ink-soft">{{ s.label }}</span>
        </div>
      </div>

      <!-- ── 1.1 SERVICIO ── -->
      <section
        v-if="subStep === 'service' || isSubStepDone('service')"
        class="bg-white rounded-2xl border border-border shadow-sm p-6 mb-4"
      >
        <header class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-stethoscope" class="w-4 h-4 text-sage-600" />
            <p class="text-sm font-semibold text-ink">1. Elegí el tipo de consulta</p>
          </div>
          <button
            v-if="booking.service"
            type="button"
            class="text-xs font-medium text-sage-600 hover:text-sage-700"
            @click="booking.service = null; booking.doctor = null; booking.slot = null"
          >
            Cambiar
          </button>
        </header>

        <!-- Resumen colapsado cuando ya se eligió y se está más adelante -->
        <div
          v-if="booking.service && subStep !== 'service'"
          class="flex items-center gap-3 p-3 rounded-xl bg-sage-50 border border-sage-200"
        >
          <span
            class="w-1.5 h-10 rounded-full flex-shrink-0"
            :style="{ backgroundColor: booking.service.color || '#6FA776' }"
          />
          <div class="flex-1 min-w-0">
            <p class="font-semibold text-sm text-ink">{{ booking.service.name }}</p>
            <p class="text-xs text-ink-soft">
              {{ booking.service.duration }} min · ${{ parseFloat(booking.service.price).toFixed(0) }} MXN
            </p>
          </div>
          <UIcon name="i-lucide-check-circle-2" class="w-5 h-5 text-sage-500" />
        </div>

        <!-- Grid de servicios -->
        <div v-else>
          <div v-if="services.length === 0" class="flex justify-center py-8">
            <UIcon name="i-lucide-loader-2" class="animate-spin w-6 h-6 text-ink-muted" />
          </div>
          <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              v-for="s in services"
              :key="s.id"
              type="button"
              :disabled="doctorCountFor(s) === 0"
              class="relative flex items-stretch rounded-xl border overflow-hidden text-left transition-all hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
              :class="suggestedServiceIds.includes(s.id)
                ? 'border-sage-300 bg-sage-50'
                : 'border-border bg-white hover:border-sage-300'"
              @click="booking.selectService(s)"
            >
              <span
                class="w-1.5 flex-shrink-0"
                :style="{ backgroundColor: s.color || '#6FA776' }"
              />
              <div class="flex-1 p-3.5 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <p class="font-semibold text-sm text-ink">{{ s.name }}</p>
                  <span
                    v-if="suggestedServiceIds.includes(s.id)"
                    class="text-[10px] font-medium px-1.5 py-0.5 rounded bg-sage-200 text-sage-700"
                  >
                    Sugerido
                  </span>
                </div>
                <p v-if="s.description" class="text-xs text-ink-soft line-clamp-2 mb-1.5">
                  {{ s.description }}
                </p>
                <div class="flex items-center gap-3 text-xs text-ink-soft">
                  <span class="inline-flex items-center gap-1">
                    <UIcon name="i-lucide-clock" class="w-3 h-3" />
                    {{ s.duration }} min
                  </span>
                  <span class="font-medium text-ink">${{ parseFloat(s.price).toFixed(0) }} MXN</span>
                  <span class="inline-flex items-center gap-1 ml-auto">
                    <UIcon name="i-lucide-user-round" class="w-3 h-3" />
                    {{ doctorCountFor(s) }} {{ doctorCountFor(s) === 1 ? 'médico' : 'médicos' }}
                  </span>
                </div>
              </div>
            </button>
          </div>
        </div>
      </section>

      <!-- ── 1.2 DOCTOR ── -->
      <section
        v-if="booking.service && (subStep === 'doctor' || isSubStepDone('doctor'))"
        class="bg-white rounded-2xl border border-border shadow-sm p-6 mb-4"
      >
        <header class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-user-round" class="w-4 h-4 text-sage-600" />
            <p class="text-sm font-semibold text-ink">2. Elegí el médico</p>
          </div>
          <button
            v-if="booking.doctor"
            type="button"
            class="text-xs font-medium text-sage-600 hover:text-sage-700"
            @click="booking.doctor = null; booking.slot = null"
          >
            Cambiar
          </button>
        </header>

        <!-- Resumen colapsado -->
        <div
          v-if="booking.doctor && subStep !== 'doctor'"
          class="flex items-center gap-3 p-3 rounded-xl bg-sage-50 border border-sage-200"
        >
          <div class="w-10 h-10 rounded-full overflow-hidden flex items-center justify-center text-sm font-bold bg-sage-100 text-sage-600 flex-shrink-0">
            <img v-if="booking.doctor.photo" :src="booking.doctor.photo" :alt="booking.doctor.full_name" class="w-full h-full object-cover">
            <template v-else>{{ booking.doctor.full_name?.[0]?.toUpperCase() }}</template>
          </div>
          <div class="flex-1 min-w-0">
            <p class="font-semibold text-sm text-ink truncate">{{ booking.doctor.full_name }}</p>
            <p class="text-xs text-ink-soft truncate">{{ booking.doctor.specialty || 'Médico General' }}</p>
          </div>
          <UIcon name="i-lucide-check-circle-2" class="w-5 h-5 text-sage-500" />
        </div>

        <!-- Grid de doctores filtrados por servicio -->
        <div v-else>
          <div v-if="filteredDoctors.length === 0" class="text-center py-6">
            <UIcon name="i-lucide-user-x" class="w-8 h-8 mx-auto mb-2 opacity-40 text-ink-muted" />
            <p class="text-sm text-ink-muted">No hay médicos disponibles para este servicio.</p>
          </div>
          <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <button
              v-for="d in filteredDoctors"
              :key="d.id"
              type="button"
              class="relative flex flex-col items-center text-center p-4 rounded-xl border transition-all hover:shadow-md"
              :class="suggestedDoctorIds.includes(d.id)
                ? 'border-sage-300 bg-sage-50'
                : 'border-border bg-white hover:border-sage-300'"
              @click="booking.selectDoctor(d)"
            >
              <span
                v-if="suggestedDoctorIds.includes(d.id)"
                class="absolute top-2 left-2 text-[10px] font-medium px-1.5 py-0.5 rounded bg-sage-200 text-sage-700 inline-flex items-center gap-1"
              >
                <UIcon name="i-lucide-sparkles" class="w-2.5 h-2.5" />
                Sugerido
              </span>
              <div class="w-16 h-16 rounded-full overflow-hidden flex items-center justify-center text-lg font-bold bg-sage-100 text-sage-600 mb-3 ring-2 ring-white shadow-sm">
                <img v-if="d.photo" :src="d.photo" :alt="d.full_name" class="w-full h-full object-cover">
                <template v-else>{{ d.full_name?.[0]?.toUpperCase() }}</template>
              </div>
              <p class="font-semibold text-sm text-ink leading-tight">{{ d.full_name }}</p>
              <p class="text-xs text-ink-soft mt-0.5">{{ d.specialty || 'Médico General' }}</p>
            </button>
          </div>
        </div>
      </section>

      <!-- ── 1.3 FECHA ── -->
      <section
        v-if="booking.doctor && (subStep === 'date' || isSubStepDone('date'))"
        class="bg-white rounded-2xl border border-border shadow-sm p-6 mb-4"
      >
        <header class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-calendar" class="w-4 h-4 text-sage-600" />
            <p class="text-sm font-semibold text-ink">3. Elegí la fecha</p>
          </div>
          <input
            :value="booking.date"
            type="date"
            :min="today"
            class="text-xs px-3 py-1.5 rounded-lg border outline-none transition-all border-border bg-white text-ink-soft focus:border-sage-500"
            @change="booking.selectDate(($event.target as HTMLInputElement).value)"
          />
        </header>
        <div class="flex gap-2 overflow-x-auto pb-2 -mx-1 px-1 scrollbar-hide">
          <button
            v-for="d in dateStrip"
            :key="d.iso"
            type="button"
            class="flex-shrink-0 flex flex-col items-center px-3.5 py-2.5 rounded-xl border min-w-[64px] transition-all"
            :class="booking.date === d.iso
              ? 'border-sage-500 bg-sage-500 text-white shadow-md'
              : 'border-border bg-white text-ink-soft hover:border-sage-300'"
            @click="booking.selectDate(d.iso)"
          >
            <span class="text-[10px] font-medium uppercase tracking-wide opacity-70">{{ d.weekday }}</span>
            <span class="text-lg font-bold leading-tight">{{ d.day }}</span>
            <span class="text-[10px] uppercase opacity-70">{{ d.month }}</span>
          </button>
        </div>
      </section>

      <!-- ── 1.4 HORARIO ── -->
      <section
        v-if="booking.date"
        class="bg-white rounded-2xl border border-border shadow-sm p-6 mb-4"
      >
        <header class="flex items-center gap-2 mb-4">
          <UIcon name="i-lucide-clock" class="w-4 h-4 text-sage-600" />
          <p class="text-sm font-semibold text-ink">4. Elegí el horario</p>
        </header>
        <div v-if="loadingSlots" class="flex justify-center py-8">
          <UIcon name="i-lucide-loader-2" class="animate-spin w-6 h-6 text-sage-500" />
        </div>
        <div v-else-if="slots.length === 0" class="text-center py-8">
          <UIcon name="i-lucide-calendar-x" class="w-10 h-10 mx-auto mb-3 opacity-40 text-ink-muted" />
          <p class="text-sm text-ink-muted">{{ content.booking.step1.slotsEmpty }}</p>
        </div>
        <div v-else class="space-y-5">
          <div v-if="groupedSlots.morning.length > 0">
            <div class="flex items-center gap-2 mb-2.5">
              <UIcon name="i-lucide-sunrise" class="w-3.5 h-3.5 text-sage-600" />
              <span class="text-xs font-semibold uppercase tracking-wide text-ink-muted">Mañana</span>
            </div>
            <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
              <button
                v-for="slot in groupedSlots.morning"
                :key="slot.start"
                type="button"
                class="px-3 py-2 rounded-lg border text-sm font-mono font-medium transition-all"
                :class="booking.slot?.start === slot.start
                  ? 'bg-sage-500 border-sage-500 text-white'
                  : 'border-border bg-white text-ink-soft hover:border-sage-300'"
                @click="booking.selectSlot(slot)"
              >
                {{ slot.start.slice(0, 5) }}
              </button>
            </div>
          </div>
          <div v-if="groupedSlots.afternoon.length > 0">
            <div class="flex items-center gap-2 mb-2.5">
              <UIcon name="i-lucide-sun" class="w-3.5 h-3.5 text-sage-600" />
              <span class="text-xs font-semibold uppercase tracking-wide text-ink-muted">Tarde</span>
            </div>
            <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
              <button
                v-for="slot in groupedSlots.afternoon"
                :key="slot.start"
                type="button"
                class="px-3 py-2 rounded-lg border text-sm font-mono font-medium transition-all"
                :class="booking.slot?.start === slot.start
                  ? 'bg-sage-500 border-sage-500 text-white'
                  : 'border-border bg-white text-ink-soft hover:border-sage-300'"
                @click="booking.selectSlot(slot)"
              >
                {{ slot.start.slice(0, 5) }}
              </button>
            </div>
          </div>
          <div v-if="groupedSlots.evening.length > 0">
            <div class="flex items-center gap-2 mb-2.5">
              <UIcon name="i-lucide-moon" class="w-3.5 h-3.5 text-sage-600" />
              <span class="text-xs font-semibold uppercase tracking-wide text-ink-muted">Noche</span>
            </div>
            <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
              <button
                v-for="slot in groupedSlots.evening"
                :key="slot.start"
                type="button"
                class="px-3 py-2 rounded-lg border text-sm font-mono font-medium transition-all"
                :class="booking.slot?.start === slot.start
                  ? 'bg-sage-500 border-sage-500 text-white'
                  : 'border-border bg-white text-ink-soft hover:border-sage-300'"
                @click="booking.selectSlot(slot)"
              >
                {{ slot.start.slice(0, 5) }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Continuar (sticky) -->
      <div class="mt-6 sticky bottom-4">
        <button
          type="button"
          :disabled="!booking.canGoToStep2"
          class="w-full flex items-center justify-center gap-2 font-semibold px-6 py-3.5 rounded-xl text-sm text-white transition-all disabled:opacity-40 disabled:cursor-not-allowed bg-sage-500 hover:bg-sage-600 shadow-lg"
          @click="booking.goTo(2)"
        >
          {{ content.booking.step1.continueButton }}
          <UIcon name="i-lucide-arrow-right" class="w-4 h-4" />
        </button>
      </div>
    </template>

    <!-- ── PASO 2: Datos del paciente ── -->
    <template v-else-if="booking.step === 2">
      <div class="space-y-5">
        <div class="rounded-2xl border p-5 border-border bg-surface-muted">
          <p class="text-xs font-semibold uppercase tracking-wide mb-3 text-ink-muted">{{ content.booking.step2.summaryTitle }}</p>
          <div class="space-y-2 text-sm">
            <div class="flex gap-2">
              <span class="text-ink-muted">Servicio</span>
              <span class="font-medium text-ink">{{ booking.service?.name }}</span>
            </div>
            <div class="flex gap-2">
              <span class="text-ink-muted">Doctor</span>
              <span class="font-medium text-ink">{{ booking.doctor?.full_name }}</span>
            </div>
            <div class="flex gap-2">
              <span class="text-ink-muted">Fecha</span>
              <span class="font-medium text-ink">
                {{ booking.date }} a las {{ booking.slot?.start.slice(0, 5) }}
              </span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl border p-6 space-y-4 border-border shadow-sm">
          <p class="text-sm font-semibold mb-1 text-ink">{{ content.booking.step2.formTitle }}</p>

          <div>
            <label class="block text-xs font-medium mb-1.5 text-ink-soft">
              {{ content.booking.step2.nameLabel }} <span style="color: #A0522D;">*</span>
            </label>
            <input
              v-model="booking.patientName"
              type="text"
              :placeholder="content.booking.step2.namePlaceholder"
              class="w-full text-sm px-4 py-2.5 rounded-lg border outline-none transition-all border-border-strong bg-white text-ink focus:border-sage-500"
            />
          </div>

          <div>
            <label class="block text-xs font-medium mb-1.5 text-ink-soft">
              {{ content.booking.step2.emailLabel }} <span style="color: #A0522D;">*</span>
            </label>
            <input
              v-model="booking.patientEmail"
              type="email"
              :placeholder="content.booking.step2.emailPlaceholder"
              class="w-full text-sm px-4 py-2.5 rounded-lg border outline-none transition-all border-border-strong bg-white text-ink focus:border-sage-500"
            />
          </div>

          <div>
            <label class="block text-xs font-medium mb-1.5 text-ink-soft">{{ content.booking.step2.phoneLabel }}</label>
            <input
              v-model="booking.patientPhone"
              type="tel"
              :placeholder="content.booking.step2.phonePlaceholder"
              class="w-full text-sm px-4 py-2.5 rounded-lg border outline-none transition-all border-border-strong bg-white text-ink focus:border-sage-500"
            />
          </div>
        </div>

        <p class="text-xs text-ink-muted">
          {{ content.booking.step2.privacyText }}
          <a href="#" class="underline text-sage-500">{{ content.booking.step2.privacyLinkLabel }}</a>
          {{ content.booking.step2.privacyTextSuffix }}
        </p>
      </div>

      <div class="flex gap-3 mt-6">
        <button
          type="button"
          class="flex-1 flex items-center justify-center gap-2 font-medium px-6 py-3.5 rounded-xl text-sm border transition-all border-border-strong text-ink-soft bg-white"
          @click="booking.goTo(1)"
        >
          <UIcon name="i-lucide-arrow-left" class="w-4 h-4" />
          {{ content.booking.step2.backButton }}
        </button>
        <button
          type="button"
          :disabled="!booking.canConfirm || submitting"
          class="flex-1 flex items-center justify-center gap-2 font-medium px-6 py-3.5 rounded-xl text-sm text-white transition-all disabled:opacity-40 disabled:cursor-not-allowed bg-sage-500 hover:bg-sage-600"
          @click="confirm"
        >
          <UIcon v-if="submitting" name="i-lucide-loader-2" class="w-4 h-4 animate-spin" />
          {{ submitting ? content.booking.step2.confirmingButton : content.booking.step2.confirmButton }}
        </button>
      </div>
    </template>

    <!-- ── PASO 3: Éxito ── -->
    <template v-else>
      <div class="bg-white rounded-2xl border p-10 text-center border-border shadow-sm">
        <div class="w-16 h-16 rounded-full mx-auto mb-6 flex items-center justify-center" style="background-color: #E4EDE6;">
          <UIcon name="i-lucide-check" class="w-8 h-8" style="color: #4A7C59;" />
        </div>
        <h2 class="text-2xl font-bold tracking-tight mb-2 text-ink">{{ content.booking.step3.successTitle }}</h2>
        <p class="text-sm mb-6 text-ink-soft">
          {{ content.booking.step3.successMessagePrefix }}
          <strong class="text-ink">{{ booking.patientEmail }}</strong>
        </p>

        <div class="rounded-xl p-5 text-left space-y-3 mb-8 bg-surface-muted">
          <div class="flex justify-between text-sm">
            <span class="text-ink-muted">Servicio</span>
            <span class="font-medium text-ink">{{ booking.service?.name }}</span>
          </div>
          <div class="h-px bg-border" />
          <div class="flex justify-between text-sm">
            <span class="text-ink-muted">Doctor</span>
            <span class="font-medium text-ink">{{ booking.doctor?.full_name }}</span>
          </div>
          <div class="h-px bg-border" />
          <div class="flex justify-between text-sm">
            <span class="text-ink-muted">Fecha y hora</span>
            <span class="font-medium text-ink">{{ booking.date }} · {{ booking.slot?.start.slice(0, 5) }}</span>
          </div>
        </div>

        <button
          type="button"
          class="text-sm font-medium px-6 py-2.5 rounded-xl border transition-all border-border-strong text-ink-soft bg-white"
          @click="booking.reset()"
        >
          {{ content.booking.step3.bookAnotherButton }}
        </button>
      </div>
    </template>
  </div>
</template>
