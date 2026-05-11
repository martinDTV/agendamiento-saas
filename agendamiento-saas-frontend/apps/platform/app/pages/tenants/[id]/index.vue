<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const { apiFetch } = useApi()
const route = useRoute()
const toast = useToast()
const id = route.params.id as string

interface TenantPlatform {
  id: string; slug: string; name: string; type: string; plan: string; is_active: boolean; created_at: string
  member_count: number
  subscription: null | {
    id: number; plan: number; plan_name: string; status: string; billing_cycle: string
    started_at: string; current_period_end: string; trial_ends_at: string | null; canceled_at: string | null
    discount: number | null; discount_code: string | null; notes: string
  }
}
interface Plan { id: number; name: string; price_monthly: string; price_yearly: string; currency: string }

const tenant = ref<TenantPlatform | null>(null)
const plans = ref<Plan[]>([])
const loading = ref(true)
const saving = ref(false)
const editing = ref(false)
const showSubscriptionModal = ref(false)
const showDeleteModal = ref(false)
const deleting = ref(false)
const deleteConfirmation = ref('')

const editForm = reactive({ name: '', is_active: true })
const subForm = reactive({
  plan: 0,
  status: 'trial',
  billing_cycle: 'monthly',
  current_period_end: '',
  notes: ''
})

async function load() {
  loading.value = true
  try {
    const [t, p] = await Promise.all([
      apiFetch<TenantPlatform>(`/platform/tenants/${id}/`),
      apiFetch<{ results: Plan[] } | Plan[]>('/platform/plans/')
    ])
    tenant.value = t
    plans.value = Array.isArray(p) ? p : p.results
    editForm.name = t.name
    editForm.is_active = t.is_active

    if (t.subscription) {
      subForm.plan = t.subscription.plan
      subForm.status = t.subscription.status
      subForm.billing_cycle = t.subscription.billing_cycle
      subForm.current_period_end = t.subscription.current_period_end
      subForm.notes = t.subscription.notes
    } else if (plans.value[0]) {
      subForm.plan = plans.value[0].id
      const future = new Date(); future.setMonth(future.getMonth() + 1)
      subForm.current_period_end = future.toISOString().slice(0, 10)
    }
  } finally { loading.value = false }
}

async function saveTenant() {
  saving.value = true
  try {
    tenant.value = await apiFetch<TenantPlatform>(`/platform/tenants/${id}/`, {
      method: 'PATCH', body: editForm
    })
    editing.value = false
    toast.add({ title: 'Tenant actualizado', color: 'primary' })
  } catch {
    toast.add({ title: 'Error al guardar', color: 'error' })
  } finally { saving.value = false }
}

async function saveSubscription() {
  saving.value = true
  try {
    if (tenant.value?.subscription) {
      await apiFetch(`/platform/subscriptions/${tenant.value.subscription.id}/`, {
        method: 'PATCH', body: subForm
      })
    } else {
      await apiFetch('/platform/subscriptions/', {
        method: 'POST', body: { ...subForm, tenant: id }
      })
    }
    showSubscriptionModal.value = false
    await load()
    toast.add({ title: 'Suscripción guardada', color: 'success' })
  } catch (e: unknown) {
    const err = e as { response?: { data?: unknown } }
    toast.add({ title: 'Error al guardar', description: JSON.stringify(err.response?.data), color: 'error' })
  } finally { saving.value = false }
}

const STATUS_COLOR: Record<string, string> = {
  active: 'green', trial: 'blue', past_due: 'yellow', canceled: 'red', suspended: 'neutral'
}

const canDelete = computed(() => tenant.value && deleteConfirmation.value === tenant.value.slug)

async function deleteTenant() {
  if (!canDelete.value) return
  deleting.value = true
  try {
    await apiFetch(`/platform/tenants/${id}/`, { method: 'DELETE' })
    toast.add({ title: 'Tenant eliminado', color: 'primary' })
    await navigateTo('/tenants')
  }
  catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    toast.add({ title: err?.response?.data?.detail ?? 'Error al eliminar', color: 'error' })
  }
  finally {
    deleting.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <UButton variant="ghost" size="sm" icon="i-lucide-arrow-left" to="/tenants">Volver</UButton>

    <div v-if="loading" class="flex justify-center py-16">
      <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl text-primary-500" />
    </div>

    <template v-else-if="tenant">
      <!-- Header -->
      <div class="flex items-start justify-between">
        <div>
          <h1 class="text-2xl font-bold text-slate-900">{{ tenant.name }}</h1>
          <p class="text-sm text-slate-400 font-mono mt-1">{{ tenant.slug }}.miapp.com</p>
        </div>
        <div class="flex items-center gap-3">
          <UBadge :color="tenant.is_active ? 'green' : 'red'" variant="soft" size="lg">
            {{ tenant.is_active ? 'Activo' : 'Inactivo' }}
          </UBadge>
          <UButton
            color="error"
            variant="soft"
            icon="i-lucide-trash-2"
            @click="showDeleteModal = true; deleteConfirmation = ''"
          >
            Eliminar
          </UButton>
        </div>
      </div>

      <!-- Info -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <p class="font-semibold text-slate-800">Información del tenant</p>
            <UButton v-if="!editing" size="sm" variant="ghost" icon="i-lucide-pencil" @click="editing = true">Editar</UButton>
          </div>
        </template>

        <div v-if="!editing" class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p class="text-slate-400 text-xs uppercase tracking-wide mb-0.5">Nombre</p>
            <p class="font-medium">{{ tenant.name }}</p>
          </div>
          <div>
            <p class="text-slate-400 text-xs uppercase tracking-wide mb-0.5">Slug</p>
            <p class="font-medium font-mono">{{ tenant.slug }}</p>
          </div>
          <div>
            <p class="text-slate-400 text-xs uppercase tracking-wide mb-0.5">Tipo</p>
            <p class="font-medium capitalize">{{ tenant.type }}</p>
          </div>
          <div>
            <p class="text-slate-400 text-xs uppercase tracking-wide mb-0.5">Miembros</p>
            <p class="font-medium">{{ tenant.member_count }}</p>
          </div>
          <div>
            <p class="text-slate-400 text-xs uppercase tracking-wide mb-0.5">Creado</p>
            <p class="font-medium">{{ new Date(tenant.created_at).toLocaleDateString('es-MX') }}</p>
          </div>
        </div>

        <div v-else class="space-y-4">
          <UFormField label="Nombre">
            <UInput v-model="editForm.name" class="w-full" />
          </UFormField>
          <UFormField label="Slug (subdominio)" hint="No editable — cambiarlo rompería URLs y sesiones activas.">
            <UInput :model-value="tenant.slug" disabled class="w-full font-mono" />
          </UFormField>
          <UFormField label="Activo">
            <USwitch v-model="editForm.is_active" />
          </UFormField>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="editing = false">Cancelar</UButton>
            <UButton :loading="saving" @click="saveTenant">Guardar</UButton>
          </div>
        </div>
      </UCard>

      <!-- Subscription -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <p class="font-semibold text-slate-800">Suscripción</p>
            <UButton size="sm" :icon="tenant.subscription ? 'i-lucide-pencil' : 'i-lucide-plus'" @click="showSubscriptionModal = true">
              {{ tenant.subscription ? 'Modificar' : 'Crear suscripción' }}
            </UButton>
          </div>
        </template>

        <div v-if="!tenant.subscription">
          <div class="grid grid-cols-2 gap-4 text-sm mb-6">
            <div>
              <p class="text-slate-400 text-xs uppercase tracking-wide mb-0.5">Plan actual</p>
              <p class="font-semibold text-emerald-600 capitalize">{{ tenant.plan || 'Free' }}</p>
            </div>
            <div>
              <p class="text-slate-400 text-xs uppercase tracking-wide mb-0.5">Tipo</p>
              <UBadge color="green" variant="soft">Sin suscripción de pago</UBadge>
            </div>
          </div>
          <div class="rounded-xl bg-slate-50 border border-slate-200 p-4 text-sm text-slate-600">
            <UIcon name="i-lucide-info" class="w-4 h-4 inline -mt-0.5 mr-1 text-slate-400" />
            Este tenant está en plan <strong class="capitalize">{{ tenant.plan || 'free' }}</strong> sin
            ciclo de facturación. Para asignar un plan de pago con período y estado de cobro, click "Crear suscripción".
          </div>
        </div>

        <div v-else class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p class="text-slate-400 text-xs uppercase tracking-wide mb-0.5">Plan</p>
            <p class="font-semibold text-primary-600">{{ tenant.subscription.plan_name }}</p>
          </div>
          <div>
            <p class="text-slate-400 text-xs uppercase tracking-wide mb-0.5">Estado</p>
            <UBadge :color="STATUS_COLOR[tenant.subscription.status]" variant="soft">
              {{ tenant.subscription.status }}
            </UBadge>
          </div>
          <div>
            <p class="text-slate-400 text-xs uppercase tracking-wide mb-0.5">Ciclo</p>
            <p class="font-medium capitalize">{{ tenant.subscription.billing_cycle }}</p>
          </div>
          <div>
            <p class="text-slate-400 text-xs uppercase tracking-wide mb-0.5">Próximo cobro</p>
            <p class="font-medium">{{ tenant.subscription.current_period_end }}</p>
          </div>
          <div v-if="tenant.subscription.discount_code">
            <p class="text-slate-400 text-xs uppercase tracking-wide mb-0.5">Descuento</p>
            <p class="font-medium font-mono">{{ tenant.subscription.discount_code }}</p>
          </div>
          <div v-if="tenant.subscription.notes" class="col-span-2">
            <p class="text-slate-400 text-xs uppercase tracking-wide mb-0.5">Notas</p>
            <p class="text-slate-700">{{ tenant.subscription.notes }}</p>
          </div>
        </div>
      </UCard>
    </template>

    <!-- Delete confirmation modal -->
    <UModal v-model:open="showDeleteModal" title="Eliminar tenant">
      <template #content>
        <div class="p-6 space-y-4">
          <div class="flex items-start gap-3 p-4 rounded-xl bg-rose-50 border border-rose-200">
            <UIcon name="i-lucide-triangle-alert" class="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
            <div class="text-sm text-rose-900">
              <p class="font-semibold">Esta acción es irreversible.</p>
              <p class="mt-1 text-rose-800">
                Vas a eliminar permanentemente <strong>{{ tenant?.name }}</strong> y
                <strong>todos sus datos relacionados</strong>: doctores, servicios, citas,
                horarios, miembros, suscripción, etc.
              </p>
            </div>
          </div>

          <UFormField :label="`Para confirmar, escribí el slug del tenant: ${tenant?.slug}`">
            <UInput
              v-model="deleteConfirmation"
              :placeholder="tenant?.slug"
              class="w-full font-mono"
            />
          </UFormField>

          <div class="flex justify-end gap-2 pt-2 border-t" style="border-color: #F3F4F6;">
            <UButton variant="ghost" color="neutral" @click="showDeleteModal = false">
              Cancelar
            </UButton>
            <UButton
              color="error"
              :disabled="!canDelete"
              :loading="deleting"
              icon="i-lucide-trash-2"
              @click="deleteTenant"
            >
              Eliminar permanentemente
            </UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Subscription modal -->
    <UModal v-model:open="showSubscriptionModal" title="Configurar suscripción">
      <template #body>
        <div class="space-y-4">
          <UFormField label="Plan">
            <USelect
              v-model="subForm.plan"
              :items="plans.map(p => ({ label: `${p.name} ($${p.price_monthly}/mes)`, value: p.id }))"
              value-attribute="value"
              label-attribute="label"
              class="w-full"
            />
          </UFormField>
          <UFormField label="Estado">
            <USelect
              v-model="subForm.status"
              :items="[
                { label: 'Trial', value: 'trial' },
                { label: 'Activa', value: 'active' },
                { label: 'Pago vencido', value: 'past_due' },
                { label: 'Cancelada', value: 'canceled' },
                { label: 'Suspendida', value: 'suspended' }
              ]"
              value-attribute="value"
              label-attribute="label"
              class="w-full"
            />
          </UFormField>
          <UFormField label="Ciclo de facturación">
            <USelect
              v-model="subForm.billing_cycle"
              :items="[
                { label: 'Mensual', value: 'monthly' },
                { label: 'Anual', value: 'yearly' }
              ]"
              value-attribute="value"
              label-attribute="label"
              class="w-full"
            />
          </UFormField>
          <UFormField label="Fin del período actual">
            <UInput v-model="subForm.current_period_end" type="date" class="w-full" />
          </UFormField>
          <UFormField label="Notas internas">
            <UTextarea v-model="subForm.notes" :rows="3" class="w-full" />
          </UFormField>
        </div>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2 w-full">
          <UButton variant="ghost" @click="showSubscriptionModal = false">Cancelar</UButton>
          <UButton :loading="saving" @click="saveSubscription">Guardar</UButton>
        </div>
      </template>
    </UModal>
  </div>
</template>
