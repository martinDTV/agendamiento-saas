<script setup lang="ts">
import type { Doctor, Branch, PaginatedResponse } from '@agendamiento/shared'

definePageMeta({ middleware: ['tenant', 'auth', 'admin-only'] })

const { apiFetch } = useApi()
const toast = useToast()

const data = ref<Doctor[]>([])
const branches = ref<Branch[]>([])
const loading = ref(false)
const open = ref(false)
const editing = ref<Doctor | null>(null)

async function load() {
  loading.value = true
  try {
    const [docs, brs] = await Promise.all([
      apiFetch<PaginatedResponse<Doctor>>('/catalog/doctors/'),
      apiFetch<PaginatedResponse<Branch>>('/catalog/branches/')
    ])
    data.value = docs.results
    branches.value = brs.results
  }
  finally { loading.value = false }
}

async function remove(row: Doctor) {
  await apiFetch(`/catalog/doctors/${row.id}/`, { method: 'DELETE' })
  toast.add({ title: 'Doctor eliminado', color: 'primary' })
  load()
}

function openCreate() { editing.value = null; open.value = true }
function openEdit(row: Doctor) { editing.value = row; open.value = true }

onMounted(load)
</script>

<template>
  <div class="space-y-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-900 dark:text-white">Doctores</h1>
        <p class="text-sm text-slate-400 mt-0.5">{{ data.length }} registrados</p>
      </div>
      <UButton icon="i-lucide-plus" @click="openCreate">Nuevo doctor</UButton>
    </div>

    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
      <div v-if="loading" class="flex justify-center py-16">
        <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl text-violet-500" />
      </div>

      <table v-else class="w-full text-sm">
        <thead class="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-800">
          <tr>
            <th class="text-left px-5 py-3.5 font-semibold text-xs text-slate-500 uppercase tracking-wide">Nombre</th>
            <th class="text-left px-5 py-3.5 font-semibold text-xs text-slate-500 uppercase tracking-wide">Email</th>
            <th class="text-left px-5 py-3.5 font-semibold text-xs text-slate-500 uppercase tracking-wide">Especialidad</th>
            <th class="text-left px-5 py-3.5 font-semibold text-xs text-slate-500 uppercase tracking-wide">Sucursal</th>
            <th class="text-left px-5 py-3.5 font-semibold text-xs text-slate-500 uppercase tracking-wide">Estado</th>
            <th class="px-5 py-3.5" />
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
          <tr v-for="row in data" :key="row.id" class="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
            <td class="px-5 py-3.5">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full overflow-hidden bg-violet-100 dark:bg-violet-900/40 flex items-center justify-center flex-shrink-0">
                  <img v-if="row.photo" :src="row.photo" :alt="row.full_name" class="w-full h-full object-cover">
                  <span v-else class="text-xs font-bold text-violet-700 dark:text-violet-300 uppercase">{{ row.full_name[0] }}</span>
                </div>
                <span class="font-medium text-slate-800 dark:text-slate-100">{{ row.full_name }}</span>
              </div>
            </td>
            <td class="px-5 py-3.5 text-slate-500">{{ row.email }}</td>
            <td class="px-5 py-3.5 text-slate-500">{{ row.specialty || '—' }}</td>
            <td class="px-5 py-3.5 text-slate-500">{{ row.branch_name || '—' }}</td>
            <td class="px-5 py-3.5">
              <span
                class="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full"
                :class="row.is_active
                  ? 'bg-emerald-50 text-emerald-600 ring-1 ring-emerald-200'
                  : 'bg-slate-100 text-slate-500 ring-1 ring-slate-200'"
              >
                <span class="w-1.5 h-1.5 rounded-full" :class="row.is_active ? 'bg-emerald-500' : 'bg-slate-400'" />
                {{ row.is_active ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td class="px-5 py-3.5">
              <div class="flex gap-1 justify-end">
                <UButton
                  size="xs"
                  variant="ghost"
                  icon="i-lucide-calendar-clock"
                  :to="`/doctors/${row.id}/schedules`"
                />
                <UButton size="xs" variant="ghost" icon="i-lucide-pencil" @click="openEdit(row)" />
                <UButton size="xs" variant="ghost" color="error" icon="i-lucide-trash-2" @click="remove(row)" />
              </div>
            </td>
          </tr>
          <tr v-if="data.length === 0">
            <td colspan="6" class="text-center py-16">
              <UIcon name="i-lucide-user-x" class="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <p class="text-sm text-slate-400">Sin doctores registrados</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <DoctorModal v-model:open="open" :doctor="editing" :branches="branches" @saved="load" />
  </div>
</template>
