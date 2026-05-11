<script setup lang="ts">
import type { Service, PaginatedResponse } from '@agendamiento/shared'

definePageMeta({ middleware: ['tenant', 'auth', 'admin-only'] })

const { apiFetch } = useApi()
const toast = useToast()
const data = ref<Service[]>([])
const loading = ref(false)
const open = ref(false)
const editing = ref<Service | null>(null)

async function load() {
  loading.value = true
  try {
    const res = await apiFetch<PaginatedResponse<Service>>('/catalog/services/')
    data.value = res.results
  }
  finally { loading.value = false }
}

async function remove(row: Service) {
  await apiFetch(`/catalog/services/${row.id}/`, { method: 'DELETE' })
  toast.add({ title: 'Servicio eliminado', color: 'primary' })
  load()
}

onMounted(load)
</script>

<template>
  <div class="space-y-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-900 dark:text-white">Servicios</h1>
        <p class="text-sm text-slate-400 mt-0.5">{{ data.length }} registrados</p>
      </div>
      <UButton icon="i-lucide-plus" @click="() => { editing = null; open = true }">Nuevo servicio</UButton>
    </div>

    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
      <div v-if="loading" class="flex justify-center py-16">
        <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl text-violet-500" />
      </div>

      <table v-else class="w-full text-sm">
        <thead class="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-800">
          <tr>
            <th class="text-left px-5 py-3.5 font-semibold text-xs text-slate-500 uppercase tracking-wide">Nombre</th>
            <th class="text-left px-5 py-3.5 font-semibold text-xs text-slate-500 uppercase tracking-wide">Duración</th>
            <th class="text-left px-5 py-3.5 font-semibold text-xs text-slate-500 uppercase tracking-wide">Precio</th>
            <th class="text-left px-5 py-3.5 font-semibold text-xs text-slate-500 uppercase tracking-wide">Estado</th>
            <th class="px-5 py-3.5" />
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
          <tr v-for="row in data" :key="row.id" class="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
            <td class="px-5 py-3.5">
              <div class="flex items-center gap-3">
                <span
                  class="w-3 h-3 rounded-full flex-shrink-0 ring-2 ring-white dark:ring-slate-900"
                  :style="{ backgroundColor: row.color }"
                />
                <span class="font-medium text-slate-800 dark:text-slate-100">{{ row.name }}</span>
              </div>
            </td>
            <td class="px-5 py-3.5 text-slate-500">{{ row.duration }} min</td>
            <td class="px-5 py-3.5 text-slate-500">${{ row.price }} MXN</td>
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
                <UButton size="xs" variant="ghost" icon="i-lucide-pencil" @click="() => { editing = row; open = true }" />
                <UButton size="xs" variant="ghost" color="error" icon="i-lucide-trash-2" @click="remove(row)" />
              </div>
            </td>
          </tr>
          <tr v-if="data.length === 0">
            <td colspan="5" class="text-center py-16">
              <UIcon name="i-lucide-clipboard-x" class="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <p class="text-sm text-slate-400">Sin servicios registrados</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <ServiceModal v-model:open="open" :service="editing" @saved="load" />
  </div>
</template>
