<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const { apiFetch } = useApi()
const toast = useToast()

interface Plan {
  id: number
  name: string
  slug: string
  description: string
  price_monthly: string
  price_yearly: string
  currency: string
  max_doctors: number
  max_appointments_per_month: number
  max_branches: number
  features: string[]
  is_active: boolean
  is_public: boolean
  sort_order: number
}

const plans = ref<Plan[]>([])
const loading = ref(false)
const showModal = ref(false)
const editing = ref<Plan | null>(null)
const saving = ref(false)

const form = reactive({
  name: '', slug: '', description: '',
  price_monthly: 0, price_yearly: 0, currency: 'MXN',
  max_doctors: 1, max_appointments_per_month: 0, max_branches: 1,
  features: '',
  is_active: true, is_public: true, sort_order: 0
})

function resetForm() {
  Object.assign(form, {
    name: '', slug: '', description: '',
    price_monthly: 0, price_yearly: 0, currency: 'MXN',
    max_doctors: 1, max_appointments_per_month: 0, max_branches: 1,
    features: '',
    is_active: true, is_public: true, sort_order: 0
  })
  editing.value = null
}

async function load() {
  loading.value = true
  try {
    const res = await apiFetch<{ results: Plan[] } | Plan[]>('/platform/plans/')
    plans.value = Array.isArray(res) ? res : res.results
  } finally { loading.value = false }
}

function openNew() {
  resetForm()
  showModal.value = true
}

function openEdit(p: Plan) {
  editing.value = p
  Object.assign(form, {
    name: p.name, slug: p.slug, description: p.description,
    price_monthly: Number(p.price_monthly), price_yearly: Number(p.price_yearly),
    currency: p.currency,
    max_doctors: p.max_doctors,
    max_appointments_per_month: p.max_appointments_per_month,
    max_branches: p.max_branches,
    features: p.features.join('\n'),
    is_active: p.is_active, is_public: p.is_public, sort_order: p.sort_order
  })
  showModal.value = true
}

async function save() {
  saving.value = true
  try {
    const body = {
      ...form,
      features: form.features.split('\n').map(s => s.trim()).filter(Boolean)
    }
    if (editing.value) {
      await apiFetch(`/platform/plans/${editing.value.id}/`, { method: 'PATCH', body })
    } else {
      await apiFetch('/platform/plans/', { method: 'POST', body })
    }
    showModal.value = false
    await load()
    toast.add({ title: 'Plan guardado', color: 'success' })
  } catch (e: unknown) {
    const err = e as { response?: { data?: unknown } }
    toast.add({ title: 'Error', description: JSON.stringify(err.response?.data), color: 'error' })
  } finally { saving.value = false }
}

async function remove(p: Plan) {
  if (!confirm(`¿Eliminar el plan "${p.name}"?`)) return
  try {
    await apiFetch(`/platform/plans/${p.id}/`, { method: 'DELETE' })
    await load()
    toast.add({ title: 'Plan eliminado', color: 'success' })
  } catch {
    toast.add({ title: 'No se puede eliminar (probablemente tiene suscripciones)', color: 'error' })
  }
}

const fmt = (n: number) => new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(n)

onMounted(load)
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Planes</h1>
      <UButton icon="i-lucide-plus" @click="openNew">Nuevo plan</UButton>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl text-primary-500" />
    </div>

    <div v-else-if="plans.length === 0" class="text-center py-16 text-slate-400">
      <UIcon name="i-lucide-package" class="text-4xl mb-2" />
      <p>Aún no hay planes. Crea el primero.</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <UCard
        v-for="p in plans"
        :key="p.id"
        :class="!p.is_active ? 'opacity-60' : ''"
      >
        <template #header>
          <div class="flex items-start justify-between">
            <div>
              <p class="font-bold text-lg text-slate-900">{{ p.name }}</p>
              <p class="text-xs text-slate-400 font-mono">{{ p.slug }}</p>
            </div>
            <div class="flex flex-col gap-1 items-end">
              <UBadge v-if="!p.is_public" color="neutral" variant="soft" size="sm">Privado</UBadge>
              <UBadge v-if="!p.is_active" color="red" variant="soft" size="sm">Inactivo</UBadge>
            </div>
          </div>
        </template>

        <div class="space-y-2">
          <div>
            <p class="text-3xl font-bold text-primary-600">{{ fmt(Number(p.price_monthly)) }}<span class="text-sm font-normal text-slate-500">/mes</span></p>
            <p v-if="Number(p.price_yearly) > 0" class="text-xs text-slate-400">{{ fmt(Number(p.price_yearly)) }}/año</p>
          </div>
          <p v-if="p.description" class="text-sm text-slate-600">{{ p.description }}</p>

          <div class="text-xs text-slate-500 space-y-0.5 pt-2 border-t border-slate-100">
            <p>👥 Doctores: {{ p.max_doctors === 0 ? 'ilimitados' : p.max_doctors }}</p>
            <p>📅 Citas/mes: {{ p.max_appointments_per_month === 0 ? 'ilimitadas' : p.max_appointments_per_month }}</p>
            <p>🏢 Sucursales: {{ p.max_branches === 0 ? 'ilimitadas' : p.max_branches }}</p>
          </div>

          <ul v-if="p.features.length > 0" class="text-xs text-slate-600 space-y-1 pt-2">
            <li v-for="f in p.features" :key="f" class="flex items-center gap-1">
              <UIcon name="i-lucide-check" class="text-green-500" /> {{ f }}
            </li>
          </ul>
        </div>

        <template #footer>
          <div class="flex gap-2">
            <UButton size="sm" variant="ghost" icon="i-lucide-pencil" class="flex-1" @click="openEdit(p)">Editar</UButton>
            <UButton size="sm" variant="ghost" color="error" icon="i-lucide-trash-2" @click="remove(p)" />
          </div>
        </template>
      </UCard>
    </div>

    <!-- Modal -->
    <UModal v-model:open="showModal" :title="editing ? 'Editar plan' : 'Nuevo plan'">
      <template #body>
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <UFormField label="Nombre">
              <UInput v-model="form.name" placeholder="Pro" class="w-full" />
            </UFormField>
            <UFormField label="Slug">
              <UInput v-model="form.slug" placeholder="pro" class="w-full" />
            </UFormField>
          </div>

          <UFormField label="Descripción">
            <UTextarea v-model="form.description" :rows="2" class="w-full" />
          </UFormField>

          <div class="grid grid-cols-3 gap-3">
            <UFormField label="Precio mensual">
              <UInput v-model.number="form.price_monthly" type="number" step="0.01" class="w-full" />
            </UFormField>
            <UFormField label="Precio anual">
              <UInput v-model.number="form.price_yearly" type="number" step="0.01" class="w-full" />
            </UFormField>
            <UFormField label="Moneda">
              <UInput v-model="form.currency" maxlength="3" class="w-full" />
            </UFormField>
          </div>

          <p class="text-xs text-slate-500 -mt-2">0 en los siguientes campos = ilimitado</p>
          <div class="grid grid-cols-3 gap-3">
            <UFormField label="Max. doctores">
              <UInput v-model.number="form.max_doctors" type="number" class="w-full" />
            </UFormField>
            <UFormField label="Max. citas/mes">
              <UInput v-model.number="form.max_appointments_per_month" type="number" class="w-full" />
            </UFormField>
            <UFormField label="Max. sucursales">
              <UInput v-model.number="form.max_branches" type="number" class="w-full" />
            </UFormField>
          </div>

          <UFormField label="Features (una por línea)">
            <UTextarea
              v-model="form.features"
              :rows="4"
              placeholder="Recordatorios por email&#10;Reportes avanzados&#10;Multi-sucursal"
              class="w-full"
            />
          </UFormField>

          <div class="grid grid-cols-3 gap-3">
            <UFormField label="Activo"><USwitch v-model="form.is_active" /></UFormField>
            <UFormField label="Público"><USwitch v-model="form.is_public" /></UFormField>
            <UFormField label="Orden">
              <UInput v-model.number="form.sort_order" type="number" class="w-full" />
            </UFormField>
          </div>
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
