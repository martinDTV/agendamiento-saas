<script setup lang="ts">
import LogoInput from '~/components/settings/LogoInput.vue'

definePageMeta({ middleware: 'auth' })

const { apiFetch } = useApi()
const settingsStore = usePlatformSettingsStore()
const toast = useToast()

interface PlatformSettings {
  primary_color: string
  platform_name: string
  support_email: string
  logo_url: string
  updated_at?: string
}

const form = reactive<PlatformSettings>({
  primary_color: '#6366f1',
  platform_name: 'Plataforma',
  support_email: '',
  logo_url: '',
})

const loading = ref(false)
const saving = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await apiFetch<PlatformSettings>('/platform/settings/')
    form.primary_color = data.primary_color
    form.platform_name = data.platform_name
    form.support_email = data.support_email
    form.logo_url = data.logo_url
  } finally { loading.value = false }
}

async function save() {
  saving.value = true
  try {
    const updated = await apiFetch<PlatformSettings>('/platform/settings/', {
      method: 'PATCH',
      body: { ...form },
    })
    settingsStore.set(updated)
    applyPlatformPrimary(updated.primary_color)
    toast.add({ title: 'Ajustes guardados', color: 'primary' })
  } catch {
    toast.add({ title: 'Error al guardar', color: 'error' })
  } finally {
    saving.value = false
  }
}

async function saveLogo(url: string) {
  try {
    const updated = await apiFetch<PlatformSettings>('/platform/settings/', {
      method: 'PATCH',
      body: { logo_url: url },
    })
    settingsStore.set(updated)
  } catch {
    toast.add({ title: 'Error al guardar el logo', color: 'error' })
  }
}

// ── PayPal sync ──────────────────────────────────────────────────────────────
interface PlanRow {
  id: number
  slug: string
  name: string
  price_monthly: string
  paypal_product_id: string
  paypal_plan_id: string
  is_active: boolean
}

interface SyncResultEntry {
  slug: string
  name: string
  price_monthly: string
  paypal_product_id?: string
  paypal_plan_id?: string
  ok: boolean
  error?: string
}

const plans = ref<PlanRow[]>([])
const syncResults = ref<SyncResultEntry[]>([])
const syncing = ref(false)
const savingProductIds = ref(false)
const force = ref(false)

async function loadPlans() {
  try {
    const res = await apiFetch<PlanRow[] | { results: PlanRow[] }>('/platform/plans/')
    const list = Array.isArray(res) ? res : res.results
    plans.value = list.filter(p => Number(p.price_monthly) > 0)
  } catch {
    plans.value = []
  }
}

async function saveProductIds() {
  savingProductIds.value = true
  try {
    const body: Record<string, string> = {}
    for (const p of plans.value) {
      body[p.slug] = p.paypal_product_id || ''
    }
    await apiFetch('/platform/paypal/set-product-ids/', { method: 'PATCH', body })
    toast.add({ title: 'Product IDs guardados', color: 'primary' })
  } catch {
    toast.add({ title: 'Error al guardar Product IDs', color: 'error' })
  } finally {
    savingProductIds.value = false
  }
}

async function syncPayPalPlans() {
  syncing.value = true
  syncResults.value = []
  try {
    const res = await apiFetch<{ results: SyncResultEntry[] }>('/platform/paypal/sync-plans/', {
      method: 'POST',
      body: { force: force.value },
    })
    syncResults.value = res.results
    const failed = res.results.filter(r => !r.ok).length
    if (failed === 0) {
      toast.add({ title: `${res.results.length} plan(es) sincronizados con PayPal`, color: 'primary' })
    } else {
      toast.add({ title: `${failed} de ${res.results.length} fallaron — revisa el detalle abajo`, color: 'error' })
    }
    await loadPlans()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string; error?: string } } }
    toast.add({ title: err.response?.data?.error ?? 'Error en sync con PayPal', description: err.response?.data?.detail, color: 'error' })
  } finally {
    syncing.value = false
  }
}

function previewColor(hex: string) {
  if (/^#[0-9A-Fa-f]{6}$/.test(hex)) applyPlatformPrimary(hex)
}

watch(() => form.primary_color, (v) => previewColor(v))

onMounted(() => {
  load()
  loadPlans()
})
</script>

<template>
  <div class="space-y-6 max-w-3xl">
    <div>
      <h1 class="text-2xl font-bold text-slate-900">Ajustes de la plataforma</h1>
      <p class="text-sm text-slate-500 mt-1">
        Estas opciones afectan únicamente al panel del super administrador.
        No se mezclan con los ajustes de cada tenant.
      </p>
    </div>

    <div v-if="loading" class="flex justify-center py-16">
      <UIcon name="i-lucide-loader-2" class="animate-spin text-3xl text-primary-500" />
    </div>

    <UCard v-else>
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="i-lucide-palette" class="w-4 h-4 text-slate-500" />
          <p class="font-semibold">Branding</p>
        </div>
      </template>

      <form class="space-y-5" @submit.prevent="save">
        <UFormField label="Nombre de la plataforma">
          <UInput v-model="form.platform_name" placeholder="Plataforma" />
        </UFormField>

        <UFormField label="Color principal" hint="Se aplica a botones, links, badges y elementos primarios del panel.">
          <div class="flex gap-3 items-center">
            <input
              v-model="form.primary_color"
              type="color"
              class="h-9 w-14 rounded cursor-pointer border border-slate-200"
            >
            <UInput v-model="form.primary_color" class="flex-1 font-mono" placeholder="#6366f1" />
            <span
              class="w-8 h-8 rounded-full border border-slate-200 flex-shrink-0"
              :style="{ background: form.primary_color }"
            />
          </div>
        </UFormField>

        <UFormField label="Logo" hint="Reemplaza el icono shield del sidebar y del login. Al subir/limpiar se guarda automáticamente.">
          <LogoInput v-model="form.logo_url" @uploaded="saveLogo" />
        </UFormField>

        <UFormField label="Email de soporte">
          <UInput v-model="form.support_email" type="email" placeholder="soporte@miapp.com" />
        </UFormField>

        <div class="flex items-center justify-between pt-3 border-t border-slate-100">
          <p class="text-xs text-slate-400">
            <UIcon name="i-lucide-info" class="inline w-3 h-3 mr-1" />
            El color del tenant no se ve afectado por este ajuste.
          </p>
          <UButton type="submit" :loading="saving" icon="i-lucide-save">
            Guardar cambios
          </UButton>
        </div>
      </form>
    </UCard>

    <!-- PayPal -->
    <UCard>
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="i-lucide-credit-card" class="w-4 h-4 text-slate-500" />
          <p class="font-semibold">PayPal — Sincronización de planes</p>
        </div>
      </template>
      <div class="space-y-4">
        <div class="rounded-lg bg-slate-50 border border-slate-200 p-4 space-y-2 text-sm">
          <div class="flex items-start gap-2">
            <UIcon name="i-lucide-info" class="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
            <div class="text-slate-700">
              <p class="font-medium mb-1">Cómo funciona</p>
              <p class="text-xs text-slate-500 leading-relaxed">
                Antes de que un tenant pueda suscribirse a un plan de pago, debes crear el Product y el Billing Plan
                correspondiente en PayPal. Este botón hace el trabajo: lee tus planes activos en BD y los sincroniza
                con PayPal usando las credenciales del <code class="font-mono text-[11px]">.env</code>.
              </p>
              <p class="text-xs text-slate-500 mt-2 leading-relaxed">
                Si cambias el precio de un plan después, marca <strong>"forzar"</strong> para regenerar.
                Las suscripciones existentes mantendrán su precio anterior — solo afecta nuevas.
              </p>
            </div>
          </div>
        </div>

        <!-- Manual Product IDs (workaround sandbox) -->
        <div v-if="plans.length > 0" class="border border-amber-200 bg-amber-50 rounded-lg p-4 space-y-3">
          <div class="flex items-start gap-2 text-xs">
            <UIcon name="i-lucide-triangle-alert" class="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <div class="text-amber-900">
              <p class="font-semibold mb-1">Product IDs (opcional, para sandbox con bug)</p>
              <p class="text-amber-800 leading-relaxed">
                Si el sync falla con error <code class="font-mono">/v1/catalog/products → 404</code>,
                crea manualmente los Products en
                <a href="https://www.sandbox.paypal.com/billing/plans" target="_blank" class="underline font-medium">sandbox.paypal.com/billing/plans</a>
                (logueado como tu cuenta business sandbox), copia el ID <code class="font-mono">PROD-XXX</code> de cada uno aquí, guarda,
                y luego corre Sincronizar — esto saltará la creación de Product y solo creará el Billing Plan.
              </p>
            </div>
          </div>

          <div class="space-y-2">
            <div
              v-for="p in plans"
              :key="p.slug"
              class="flex gap-2 items-center text-sm"
            >
              <span class="w-32 font-medium text-slate-700">{{ p.name }}</span>
              <span class="text-xs font-mono text-slate-400 w-20">${{ p.price_monthly }}/mes</span>
              <UInput
                v-model="p.paypal_product_id"
                placeholder="PROD-XXXXXXXX (deja vacío para auto-crear)"
                class="flex-1 font-mono text-xs"
              />
              <UBadge v-if="p.paypal_plan_id" color="primary" variant="soft" size="sm">P-✓</UBadge>
            </div>
          </div>

          <div class="flex justify-end">
            <UButton size="sm" variant="outline" :loading="savingProductIds" icon="i-lucide-save" @click="saveProductIds">
              Guardar Product IDs
            </UButton>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <UCheckbox v-model="force" label="Forzar regeneración (re-crea Products/Plans en PayPal aunque ya existan)" />
        </div>

        <div class="flex justify-end">
          <UButton :loading="syncing" icon="i-lucide-refresh-cw" @click="syncPayPalPlans">
            Sincronizar planes con PayPal
          </UButton>
        </div>

        <div v-if="syncResults.length > 0" class="space-y-1.5 pt-2 border-t border-slate-100">
          <p class="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Resultado</p>
          <div
            v-for="r in syncResults"
            :key="r.slug"
            class="flex items-start gap-2 text-xs p-2 rounded-md"
            :class="r.ok ? 'bg-emerald-50 border border-emerald-200' : 'bg-red-50 border border-red-200'"
          >
            <UIcon
              :name="r.ok ? 'i-lucide-check-circle-2' : 'i-lucide-x-circle'"
              class="w-4 h-4 flex-shrink-0 mt-0.5"
              :class="r.ok ? 'text-emerald-600' : 'text-red-600'"
            />
            <div class="flex-1 min-w-0">
              <p class="font-medium" :class="r.ok ? 'text-emerald-800' : 'text-red-800'">
                {{ r.name }} (${{ r.price_monthly }}/mes)
              </p>
              <p v-if="r.ok" class="font-mono text-[10px] text-slate-500 mt-0.5 break-all">
                product={{ r.paypal_product_id }} · plan={{ r.paypal_plan_id }}
              </p>
              <p v-else class="text-red-700 mt-0.5">{{ r.error }}</p>
            </div>
          </div>
        </div>
      </div>
    </UCard>

    <!-- Live preview card -->
    <UCard>
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="i-lucide-eye" class="w-4 h-4 text-slate-500" />
          <p class="font-semibold">Vista previa</p>
        </div>
      </template>
      <div class="space-y-3">
        <div class="flex flex-wrap gap-2">
          <UButton>Botón solid</UButton>
          <UButton variant="soft">Soft</UButton>
          <UButton variant="outline">Outline</UButton>
          <UButton variant="ghost">Ghost</UButton>
        </div>
        <div class="flex flex-wrap gap-2">
          <UBadge color="primary">Primary</UBadge>
          <UBadge color="primary" variant="soft">Soft</UBadge>
          <UBadge color="primary" variant="outline">Outline</UBadge>
        </div>
        <p class="text-sm text-slate-600">
          Texto con
          <a href="#" class="text-primary-600 hover:text-primary-700 font-medium">link primario</a>
          y un valor destacado: <span class="text-primary-600 font-bold">$2,499 MXN</span>.
        </p>
      </div>
    </UCard>
  </div>
</template>
