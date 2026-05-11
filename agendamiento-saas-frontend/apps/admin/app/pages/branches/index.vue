<script setup lang="ts">
import type { Branch, PaginatedResponse } from '@agendamiento/shared'

definePageMeta({ middleware: ['tenant', 'auth', 'admin-only'] })

const { apiFetch } = useApi()
const toast = useToast()

const data = ref<Branch[]>([])
const loading = ref(false)
const open = ref(false)
const editing = ref<Branch | null>(null)

async function load() {
  loading.value = true
  try {
    const res = await apiFetch<PaginatedResponse<Branch>>('/catalog/branches/')
    data.value = res.results
  }
  finally { loading.value = false }
}

async function remove(row: Branch) {
  await apiFetch(`/catalog/branches/${row.id}/`, { method: 'DELETE' })
  toast.add({ title: 'Sucursal eliminada', color: 'primary' })
  load()
}

function openCreate() { editing.value = null; open.value = true }
function openEdit(row: Branch) { editing.value = row; open.value = true }

onMounted(load)
</script>

<template>
  <div class="space-y-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-900 dark:text-white">Sucursales</h1>
        <p class="text-sm text-slate-400 mt-0.5">{{ data.length }} registradas</p>
      </div>
      <UButton icon="i-lucide-plus" @click="openCreate">Nueva sucursal</UButton>
    </div>

    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
      <div v-if="loading" class="flex justify-center py-16">
        <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl text-violet-500" />
      </div>

      <table v-else class="w-full text-sm">
        <thead class="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-800">
          <tr>
            <th class="text-left px-5 py-3.5 font-semibold text-xs text-slate-500 uppercase tracking-wide">Nombre</th>
            <th class="text-left px-5 py-3.5 font-semibold text-xs text-slate-500 uppercase tracking-wide">Dirección</th>
            <th class="text-left px-5 py-3.5 font-semibold text-xs text-slate-500 uppercase tracking-wide">Teléfono</th>
            <th class="text-left px-5 py-3.5 font-semibold text-xs text-slate-500 uppercase tracking-wide">Estado</th>
            <th class="px-5 py-3.5" />
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
          <tr v-for="row in data" :key="row.id" class="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
            <td class="px-5 py-3.5">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center flex-shrink-0">
                  <UIcon name="i-lucide-building-2" class="w-4 h-4 text-slate-500 dark:text-slate-400" />
                </div>
                <span class="font-medium text-slate-800 dark:text-slate-100">{{ row.name }}</span>
              </div>
            </td>
            <td class="px-5 py-3.5 text-slate-500">{{ row.address || '—' }}</td>
            <td class="px-5 py-3.5 text-slate-500">{{ row.phone || '—' }}</td>
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
                <UButton size="xs" variant="ghost" icon="i-lucide-pencil" @click="openEdit(row)" />
                <UButton size="xs" variant="ghost" color="error" icon="i-lucide-trash-2" @click="remove(row)" />
              </div>
            </td>
          </tr>
          <tr v-if="data.length === 0">
            <td colspan="5" class="text-center py-16">
              <UIcon name="i-lucide-building-x" class="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <p class="text-sm text-slate-400">Sin sucursales registradas</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <BranchModal v-model:open="open" :branch="editing" @saved="load" />
  </div>
</template>
