<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const { apiFetch } = useApi()
const toast = useToast()

interface Discount {
  id: number
  code: string
  description: string
  discount_type: 'percent' | 'fixed'
  value: string
  applicable_plans: number[]
  applicable_plan_names: string[]
  valid_from: string
  valid_until: string | null
  max_uses: number | null
  times_used: number
  is_active: boolean
}

interface Plan { id: number; name: string }

const discounts = ref<Discount[]>([])
const plans = ref<Plan[]>([])
const loading = ref(false)
const showModal = ref(false)
const editing = ref<Discount | null>(null)
const saving = ref(false)

const form = reactive({
  code: '', description: '',
  discount_type: 'percent' as 'percent' | 'fixed',
  value: 0,
  applicable_plans: [] as number[],
  valid_from: new Date().toISOString().slice(0, 10),
  valid_until: '',
  max_uses: null as number | null,
  is_active: true
})

function resetForm() {
  Object.assign(form, {
    code: '', description: '',
    discount_type: 'percent', value: 0,
    applicable_plans: [],
    valid_from: new Date().toISOString().slice(0, 10),
    valid_until: '', max_uses: null, is_active: true
  })
  editing.value = null
}

async function load() {
  loading.value = true
  try {
    const [d, p] = await Promise.all([
      apiFetch<{ results: Discount[] } | Discount[]>('/platform/discounts/'),
      apiFetch<{ results: Plan[] } | Plan[]>('/platform/plans/')
    ])
    discounts.value = Array.isArray(d) ? d : d.results
    plans.value = Array.isArray(p) ? p : p.results
  } finally { loading.value = false }
}

function openNew() { resetForm(); showModal.value = true }

function openEdit(d: Discount) {
  editing.value = d
  Object.assign(form, {
    code: d.code,
    description: d.description,
    discount_type: d.discount_type,
    value: Number(d.value),
    applicable_plans: [...d.applicable_plans],
    valid_from: d.valid_from,
    valid_until: d.valid_until ?? '',
    max_uses: d.max_uses,
    is_active: d.is_active
  })
  showModal.value = true
}

async function save() {
  saving.value = true
  try {
    const body = {
      ...form,
      valid_until: form.valid_until || null,
      max_uses: form.max_uses || null
    }
    if (editing.value) {
      await apiFetch(`/platform/discounts/${editing.value.id}/`, { method: 'PATCH', body })
    } else {
      await apiFetch('/platform/discounts/', { method: 'POST', body })
    }
    showModal.value = false
    await load()
    toast.add({ title: 'Descuento guardado', color: 'success' })
  } catch (e: unknown) {
    const err = e as { response?: { data?: unknown } }
    toast.add({ title: 'Error', description: JSON.stringify(err.response?.data), color: 'error' })
  } finally { saving.value = false }
}

async function remove(d: Discount) {
  if (!confirm(`¿Eliminar el descuento "${d.code}"?`)) return
  await apiFetch(`/platform/discounts/${d.id}/`, { method: 'DELETE' })
  await load()
  toast.add({ title: 'Eliminado', color: 'success' })
}

onMounted(load)
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Descuentos</h1>
      <UButton icon="i-lucide-plus" @click="openNew">Nuevo descuento</UButton>
    </div>

    <UCard :ui="{ body: 'p-0' }">
      <div v-if="loading" class="flex justify-center py-12">
        <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl text-primary-500" />
      </div>

      <table v-else class="w-full text-sm">
        <thead class="bg-slate-50">
          <tr>
            <th class="text-left px-4 py-3 font-medium text-slate-600">Código</th>
            <th class="text-left px-4 py-3 font-medium text-slate-600">Tipo</th>
            <th class="text-right px-4 py-3 font-medium text-slate-600">Valor</th>
            <th class="text-left px-4 py-3 font-medium text-slate-600">Vigencia</th>
            <th class="text-right px-4 py-3 font-medium text-slate-600">Usos</th>
            <th class="text-left px-4 py-3 font-medium text-slate-600">Activo</th>
            <th class="px-4 py-3" />
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="d in discounts" :key="d.id" class="hover:bg-slate-50">
            <td class="px-4 py-3">
              <p class="font-mono font-bold text-primary-600">{{ d.code }}</p>
              <p v-if="d.description" class="text-xs text-slate-400">{{ d.description }}</p>
            </td>
            <td class="px-4 py-3 text-slate-700">{{ d.discount_type === 'percent' ? 'Porcentaje' : 'Monto fijo' }}</td>
            <td class="px-4 py-3 text-right font-mono font-semibold">
              {{ d.value }}{{ d.discount_type === 'percent' ? '%' : ' MXN' }}
            </td>
            <td class="px-4 py-3 text-xs text-slate-700">
              {{ d.valid_from }}<br>
              <span class="text-slate-400">→ {{ d.valid_until ?? 'sin fin' }}</span>
            </td>
            <td class="px-4 py-3 text-right">
              {{ d.times_used }}{{ d.max_uses ? `/${d.max_uses}` : '' }}
            </td>
            <td class="px-4 py-3">
              <UBadge :color="d.is_active ? 'green' : 'red'" variant="soft" size="sm">
                {{ d.is_active ? 'Sí' : 'No' }}
              </UBadge>
            </td>
            <td class="px-4 py-3">
              <div class="flex gap-1 justify-end">
                <UButton variant="ghost" icon="i-lucide-pencil" size="sm" @click="openEdit(d)" />
                <UButton variant="ghost" color="error" icon="i-lucide-trash-2" size="sm" @click="remove(d)" />
              </div>
            </td>
          </tr>
          <tr v-if="discounts.length === 0">
            <td colspan="7" class="text-center py-12 text-slate-400">No hay descuentos creados</td>
          </tr>
        </tbody>
      </table>
    </UCard>

    <UModal v-model:open="showModal" :title="editing ? 'Editar descuento' : 'Nuevo descuento'">
      <template #body>
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <UFormField label="Código">
              <UInput v-model="form.code" placeholder="WELCOME20" class="w-full font-mono uppercase" />
            </UFormField>
            <UFormField label="Tipo">
              <USelect
                v-model="form.discount_type"
                :items="[
                  { label: 'Porcentaje', value: 'percent' },
                  { label: 'Monto fijo', value: 'fixed' }
                ]"
                value-attribute="value"
                label-attribute="label"
                class="w-full"
              />
            </UFormField>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <UFormField :label="form.discount_type === 'percent' ? 'Porcentaje' : 'Monto MXN'">
              <UInput v-model.number="form.value" type="number" step="0.01" class="w-full" />
            </UFormField>
            <UFormField label="Usos máximos (vacío = ilimitado)">
              <UInput v-model.number="form.max_uses" type="number" class="w-full" />
            </UFormField>
          </div>

          <UFormField label="Descripción">
            <UInput v-model="form.description" class="w-full" />
          </UFormField>

          <div class="grid grid-cols-2 gap-3">
            <UFormField label="Válido desde">
              <UInput v-model="form.valid_from" type="date" class="w-full" />
            </UFormField>
            <UFormField label="Válido hasta (opcional)">
              <UInput v-model="form.valid_until" type="date" class="w-full" />
            </UFormField>
          </div>

          <UFormField label="Planes aplicables (vacío = todos)">
            <div class="flex flex-wrap gap-2 p-2 border border-slate-200 rounded-lg">
              <label
                v-for="p in plans"
                :key="p.id"
                class="flex items-center gap-1 text-sm cursor-pointer"
              >
                <UCheckbox
                  :model-value="form.applicable_plans.includes(p.id)"
                  @update:model-value="(v) => {
                    if (v) form.applicable_plans.push(p.id)
                    else form.applicable_plans = form.applicable_plans.filter(x => x !== p.id)
                  }"
                />
                {{ p.name }}
              </label>
            </div>
          </UFormField>

          <UFormField label="Activo">
            <USwitch v-model="form.is_active" />
          </UFormField>
        </div>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2 w-full">
          <UButton variant="ghost" @click="showModal = false">Cancelar</UButton>
          <UButton :loading="saving" @click="save">Guardar</UButton>
        </div>
      </template>
    </UModal>
  </div>
</template>
