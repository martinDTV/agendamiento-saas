<script setup lang="ts">
import type { Room, Branch, PaginatedResponse } from '@agendamiento/shared'

definePageMeta({ middleware: ['tenant', 'auth', 'admin-only'] })

const { apiFetch } = useApi()

const rooms    = ref<Room[]>([])
const branches = ref<Branch[]>([])
const loading  = ref(false)
const showForm = ref(false)
const saving   = ref(false)
const editingRoom = ref<Room | null>(null)

const form = reactive({
  name:     '',
  branch:   '',
  capacity: 10,
  is_active: true,
})

async function load() {
  loading.value = true
  try {
    const [r, b] = await Promise.all([
      apiFetch<PaginatedResponse<Room>>('/meetings/rooms/'),
      apiFetch<PaginatedResponse<Branch>>('/catalog/branches/'),
    ])
    rooms.value    = r.results
    branches.value = b.results
  } finally { loading.value = false }
}

function openCreate() {
  editingRoom.value = null
  form.name     = ''
  form.branch   = branches.value[0]?.id ?? ''
  form.capacity = 10
  form.is_active = true
  showForm.value = true
}

function openEdit(room: Room) {
  editingRoom.value = room
  form.name     = room.name
  form.branch   = room.branch
  form.capacity = room.capacity
  form.is_active = room.is_active
  showForm.value = true
}

async function save() {
  saving.value = true
  try {
    if (editingRoom.value) {
      await apiFetch(`/meetings/rooms/${editingRoom.value.id}/`, {
        method: 'PATCH', body: { ...form },
      })
    } else {
      await apiFetch('/meetings/rooms/', { method: 'POST', body: { ...form } })
    }
    showForm.value = false
    await load()
  } finally { saving.value = false }
}

async function toggleActive(room: Room) {
  await apiFetch(`/meetings/rooms/${room.id}/`, {
    method: 'PATCH', body: { is_active: !room.is_active },
  })
  room.is_active = !room.is_active
}

const branchItems = computed(() =>
  branches.value.map(b => ({ label: b.name, value: b.id }))
)

// Group rooms by branch
const byBranch = computed(() => {
  const map = new Map<string, { branch: Branch; rooms: Room[] }>()
  for (const b of branches.value) map.set(b.id, { branch: b, rooms: [] })
  for (const r of rooms.value) {
    if (map.has(r.branch)) map.get(r.branch)!.rooms.push(r)
  }
  return [...map.values()]
})

onMounted(load)
</script>

<template>
  <div class="space-y-6">

    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-slate-800">Salas</h2>
        <p class="text-sm text-slate-400">Gestiona las salas de reunión por clínica</p>
      </div>
      <UButton icon="i-lucide-plus" @click="openCreate">Nueva sala</UButton>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-16">
      <UIcon name="i-lucide-loader-2" class="animate-spin w-6 h-6 text-slate-400" />
    </div>

    <!-- Rooms grouped by branch -->
    <div v-else class="space-y-6">
      <div v-for="{ branch, rooms: bRooms } in byBranch" :key="branch.id">
        <div class="flex items-center gap-2 mb-3">
          <UIcon name="i-lucide-building-2" class="w-4 h-4 text-slate-400" />
          <h3 class="text-sm font-semibold text-slate-600 uppercase tracking-wide">{{ branch.name }}</h3>
          <div class="flex-1 h-px bg-slate-100" />
        </div>

        <div v-if="bRooms.length === 0" class="text-sm text-slate-400 pl-6">
          Sin salas registradas
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <div
            v-for="room in bRooms"
            :key="room.id"
            class="bg-white border rounded-xl p-4 flex items-start gap-3 transition-shadow hover:shadow-sm"
            style="border-color: #E5E7EB;"
            :class="!room.is_active ? 'opacity-50' : ''"
          >
            <div
              class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
              style="background-color: #EEF2EE;"
            >
              <UIcon name="i-lucide-door-open" class="w-5 h-5 text-sage-600" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="font-semibold text-slate-800 text-sm">{{ room.name }}</p>
              <p class="text-xs text-slate-400 mt-0.5">Capacidad: {{ room.capacity }} personas</p>
              <span
                class="inline-block mt-1.5 text-[10px] font-semibold px-1.5 py-0.5 rounded-full"
                :class="room.is_active
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'bg-slate-100 text-slate-500'"
              >
                {{ room.is_active ? 'Activa' : 'Inactiva' }}
              </span>
            </div>
            <div class="flex flex-col gap-1 flex-shrink-0">
              <button
                class="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-50 transition-colors"
                title="Editar"
                @click="openEdit(room)"
              >
                <UIcon name="i-lucide-pencil" class="w-3.5 h-3.5" />
              </button>
              <button
                class="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-50 transition-colors"
                :title="room.is_active ? 'Desactivar' : 'Activar'"
                @click="toggleActive(room)"
              >
                <UIcon :name="room.is_active ? 'i-lucide-eye-off' : 'i-lucide-eye'" class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create / Edit modal -->
    <UModal v-model:open="showForm">
      <template #content>
        <div class="p-6 w-full max-w-md">
          <h3 class="text-base font-semibold text-slate-800 mb-4">
            {{ editingRoom ? 'Editar sala' : 'Nueva sala' }}
          </h3>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Nombre</label>
              <input
                v-model="form.name"
                type="text"
                placeholder="Sala de reuniones A"
                class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2"
                style="border-color: #D1D5DB; focus:ring-color: #5B7C6B;"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Sucursal</label>
              <USelect
                v-model="form.branch"
                :items="branchItems"
                value-attribute="value"
                label-attribute="label"
                class="w-full"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Capacidad (personas)</label>
              <input
                v-model.number="form.capacity"
                type="number"
                min="1"
                max="100"
                class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2"
                style="border-color: #D1D5DB;"
              />
            </div>
          </div>

          <div class="flex justify-end gap-2 mt-6">
            <UButton variant="ghost" color="neutral" @click="showForm = false">Cancelar</UButton>
            <UButton
              :loading="saving"
              :disabled="!form.name || !form.branch"
              @click="save"
            >
              {{ editingRoom ? 'Guardar cambios' : 'Crear sala' }}
            </UButton>
          </div>
        </div>
      </template>
    </UModal>

  </div>
</template>
