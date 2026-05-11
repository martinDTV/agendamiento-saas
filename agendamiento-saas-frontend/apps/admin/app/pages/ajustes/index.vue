<script setup lang="ts">
import { DEFAULT_CONTENT, type SiteContent } from '@agendamiento/shared'
import ContentEditor from '~/components/settings/ContentEditor.vue'
import LogoInput from '~/components/settings/LogoInput.vue'

definePageMeta({ middleware: ['tenant', 'auth'] })

const { apiFetch } = useApi()
const tenantStore = useTenantStore()
const auth = useAuthStore()
const toast = useToast()

interface TenantSelf {
  id: string
  slug: string
  name: string
  type: string
  plan: string
  settings: Record<string, any>
  created_at: string
}

const data = ref<TenantSelf | null>(null)
const loading = ref(false)
const saving = ref(false)

// Form fields
const name = ref('')
const primaryColor = ref('#2563eb')
const timezone = ref('America/Mexico_City')
const logoUrl = ref('')

const timezoneOptions = [
  { label: 'Ciudad de México (UTC-6)', value: 'America/Mexico_City' },
  { label: 'Hermosillo (UTC-7)', value: 'America/Hermosillo' },
  { label: 'Tijuana (UTC-8)', value: 'America/Tijuana' },
  { label: 'Cancún (UTC-5)', value: 'America/Cancun' },
  { label: 'UTC', value: 'UTC' }
]

interface PlanFromApi {
  id: number
  slug: string
  name: string
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

const plans = ref<PlanFromApi[]>([])
const loadingPlans = ref(false)
const upgradingPlan = ref(false)

const planLabels = computed<Record<string, string>>(() => {
  const map: Record<string, string> = {}
  for (const p of plans.value) map[p.slug] = p.name
  return map
})

function formatPlanPrice(p: PlanFromApi): string {
  const n = Number(p.price_monthly)
  if (!isFinite(n) || n <= 0) return '$0'
  const fmt = new Intl.NumberFormat('es-MX', { style: 'currency', currency: p.currency || 'MXN', maximumFractionDigits: 0 })
  return fmt.format(n)
}

async function loadPlans() {
  loadingPlans.value = true
  try {
    const res = await apiFetch<PlanFromApi[] | { results: PlanFromApi[] }>('/plans/')
    plans.value = Array.isArray(res) ? res : res.results
  } catch {
    plans.value = []
  } finally {
    loadingPlans.value = false
  }
}

// Content (CMS) — fully resolved SiteContent (defaults merged with stored)
const content = ref<SiteContent>(structuredClone(DEFAULT_CONTENT))
const savingContent = ref(false)
const contentOpen = ref(true)

function mergeContent(stored: any): SiteContent {
  const base = structuredClone(DEFAULT_CONTENT) as any
  if (!stored || typeof stored !== 'object') return base
  for (const topKey of Object.keys(base)) {
    if (stored[topKey] && typeof stored[topKey] === 'object') {
      base[topKey] = deepMerge(base[topKey], stored[topKey])
    }
  }
  return base
}

function deepMerge(target: any, source: any): any {
  if (Array.isArray(target)) return Array.isArray(source) ? structuredClone(source) : target
  if (target && typeof target === 'object') {
    const out: any = { ...target }
    if (source && typeof source === 'object') {
      for (const k of Object.keys(source)) {
        out[k] = k in target ? deepMerge(target[k], source[k]) : source[k]
      }
    }
    return out
  }
  return source ?? target
}

async function changePlan(planSlug: string) {
  if (data.value?.plan === planSlug) return
  upgradingPlan.value = true
  try {
    const res = await apiFetch<{ redirect_url: string | null; subscription_id?: string; plan?: string; message?: string }>(
      `/platform/paypal/subscribe/${planSlug}/`,
      { method: 'POST' },
    )
    if (res.redirect_url) {
      // Plan de pago → redirigir al checkout de PayPal. Al volver con
      // ?subscription_id=... el effect de abajo confirma la suscripción.
      toast.add({ title: 'Redirigiendo a PayPal…', color: 'primary' })
      window.location.href = res.redirect_url
      return
    }
    // Plan free — backend ya actualizó. Recargamos.
    toast.add({ title: res.message || `Plan actualizado a ${planLabels.value[planSlug] ?? planSlug}`, color: 'primary' })
    await load()
    await loadPlans()
  }
  catch (e: unknown) {
    const err = e as { response?: { status?: number; data?: { error?: string; detail?: string } } }
    const msg = err.response?.data?.error || err.response?.data?.detail || 'Error al cambiar de plan'
    toast.add({ title: msg, color: 'error' })
  }
  finally {
    upgradingPlan.value = false
  }
}

// Cancelar suscripción activa (solo aplica a planes de pago)
const canceling = ref(false)
async function cancelSubscription() {
  if (!confirm('¿Cancelar tu suscripción actual? Conservarás el acceso hasta el fin del período pagado.')) return
  canceling.value = true
  try {
    await apiFetch('/platform/paypal/cancel/', { method: 'POST', body: { reason: 'Cancelado por el cliente' } })
    toast.add({ title: 'Suscripción cancelada', color: 'primary' })
    await load()
  }
  catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    toast.add({ title: err.response?.data?.error ?? 'Error al cancelar', color: 'error' })
  }
  finally {
    canceling.value = false
  }
}

// Confirmar después de retorno de PayPal — si la URL trae ?subscription_id= y opcionalmente token=&ba_token=
async function confirmPayPalReturn() {
  const route = useRoute()
  const subId = route.query.subscription_id
  if (!subId || typeof subId !== 'string') return
  try {
    const res = await apiFetch<{ ok: boolean; plan?: string; status?: string; error?: string }>(
      `/platform/paypal/return/?subscription_id=${encodeURIComponent(subId)}`,
    )
    if (res.ok) {
      toast.add({ title: `¡Plan ${res.plan?.toUpperCase()} activado!`, color: 'primary' })
    } else {
      toast.add({ title: res.error ?? 'No se pudo confirmar la suscripción', color: 'error' })
    }
  } catch {
    toast.add({ title: 'Error confirmando la suscripción con PayPal', color: 'error' })
  } finally {
    // Limpia query params
    await navigateTo('/ajustes', { replace: true })
    await load()
  }
}

async function load() {
  loading.value = true
  try {
    data.value = await apiFetch<TenantSelf>('/tenants/me/')
    name.value = data.value.name
    primaryColor.value = data.value.settings?.branding?.primaryColor ?? '#2563eb'
    logoUrl.value = data.value.settings?.branding?.logoUrl ?? ''
    timezone.value = data.value.settings?.timezone ?? 'America/Mexico_City'
    content.value = mergeContent(data.value.settings?.content)
  }
  finally { loading.value = false }
}

async function save() {
  saving.value = true
  try {
    const updated = await apiFetch<TenantSelf>('/tenants/me/', {
      method: 'PATCH',
      body: {
        name: name.value,
        settings: {
          ...data.value?.settings,
          branding: {
            ...(data.value?.settings?.branding ?? {}),
            primaryColor: primaryColor.value,
            logoUrl: logoUrl.value || undefined,
          },
          timezone: timezone.value
        }
      }
    })
    data.value = updated
    tenantStore.setTenant(updated as any)
    applyBrandColor(primaryColor.value)
    toast.add({ title: 'Ajustes guardados', color: 'primary' })
  }
  catch {
    toast.add({ title: 'Error al guardar', color: 'error' })
  }
  finally { saving.value = false }
}

// Auto-save SOLO el logo (sin tocar nombre, color ni timezone) cuando el
// usuario sube o limpia desde el LogoInput. Persiste inmediatamente para que
// no haya que recordar clickear "Guardar cambios".
async function saveLogo(url: string) {
  try {
    const updated = await apiFetch<TenantSelf>('/tenants/me/', {
      method: 'PATCH',
      body: {
        settings: {
          ...data.value?.settings,
          branding: {
            ...(data.value?.settings?.branding ?? {}),
            logoUrl: url || undefined,
          },
        },
      },
    })
    data.value = updated
    tenantStore.setTenant(updated as any)
  }
  catch {
    toast.add({ title: 'Error al guardar el logo', color: 'error' })
  }
}

async function saveContent() {
  savingContent.value = true
  try {
    const updated = await apiFetch<TenantSelf>('/tenants/me/', {
      method: 'PATCH',
      body: {
        settings: {
          ...data.value?.settings,
          content: content.value,
        },
      },
    })
    data.value = updated
    tenantStore.setTenant(updated as any)
    toast.add({ title: 'Contenido del sitio guardado', color: 'primary' })
  }
  catch {
    toast.add({ title: 'Error al guardar el contenido', color: 'error' })
  }
  finally { savingContent.value = false }
}

function resetContent() {
  if (!confirm('¿Restaurar todos los textos del sitio público a los valores por defecto? Esto sobreescribirá tus cambios al guardar.')) return
  content.value = structuredClone(DEFAULT_CONTENT)
  toast.add({ title: 'Restaurado. Recuerda guardar para aplicar.', color: 'info' })
}

// ── Personal profile ─────────────────────────────────────────────────────────
const profile      = reactive({ first_name: '', last_name: '', email: '' })
const savingProfile = ref(false)
const passwordForm  = reactive({ password: '', confirm: '' })
const savingPwd     = ref(false)

async function loadMe() {
  try {
    const me = await apiFetch<{ first_name: string; last_name: string; email: string }>('/accounts/me/')
    profile.first_name = me.first_name ?? ''
    profile.last_name  = me.last_name ?? ''
    profile.email      = me.email ?? ''
  } catch { /* ignore */ }
}

async function saveProfile() {
  savingProfile.value = true
  try {
    const updated = await apiFetch<any>('/accounts/me/', { method: 'PATCH', body: { ...profile } })
    if (auth.user) {
      auth.user.first_name = updated.first_name
      auth.user.last_name  = updated.last_name
      auth.user.email      = updated.email
    }
    toast.add({ title: 'Perfil actualizado', color: 'primary' })
  } catch { toast.add({ title: 'Error al guardar perfil', color: 'error' }) }
  finally { savingProfile.value = false }
}

async function savePassword() {
  if (passwordForm.password !== passwordForm.confirm) {
    toast.add({ title: 'Las contraseñas no coinciden', color: 'error' })
    return
  }
  if (passwordForm.password.length < 8) {
    toast.add({ title: 'Mínimo 8 caracteres', color: 'error' })
    return
  }
  savingPwd.value = true
  try {
    await apiFetch('/accounts/me/', { method: 'PATCH', body: { password: passwordForm.password } })
    passwordForm.password = ''
    passwordForm.confirm  = ''
    toast.add({ title: 'Contraseña actualizada', color: 'primary' })
  } catch { toast.add({ title: 'Error al cambiar contraseña', color: 'error' }) }
  finally { savingPwd.value = false }
}

onMounted(() => {
  load()
  loadMe()
  loadPlans()
  confirmPayPalReturn()
})
</script>

<template>
  <div class="space-y-6 max-w-4xl">
    <h1 class="text-2xl font-bold">Ajustes</h1>

    <div v-if="loading" class="flex justify-center py-16">
      <UIcon name="i-lucide-loader-2" class="animate-spin text-3xl text-sage-500" />
    </div>

      <!-- Profile picture -->
      <ProfilePictureCard />

      <!-- Personal profile -->
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-user-round" class="w-4 h-4 text-slate-500" />
            <p class="font-semibold">Información personal</p>
          </div>
        </template>
        <div class="space-y-4 max-w-2xl">
          <div class="grid grid-cols-2 gap-3">
            <UFormField label="Nombre">
              <UInput v-model="profile.first_name" />
            </UFormField>
            <UFormField label="Apellido">
              <UInput v-model="profile.last_name" />
            </UFormField>
          </div>
          <UFormField label="Correo electrónico">
            <UInput v-model="profile.email" type="email" />
          </UFormField>
          <div class="flex justify-end">
            <UButton :loading="savingProfile" @click="saveProfile">Guardar perfil</UButton>
          </div>
        </div>
      </UCard>

      <!-- Password -->
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-key-round" class="w-4 h-4 text-slate-500" />
            <p class="font-semibold">Contraseña</p>
          </div>
        </template>
        <div class="space-y-4 max-w-2xl">
          <div class="grid grid-cols-2 gap-3">
            <UFormField label="Nueva contraseña">
              <UInput v-model="passwordForm.password" type="password" autocomplete="new-password" />
            </UFormField>
            <UFormField label="Confirmar">
              <UInput v-model="passwordForm.confirm" type="password" autocomplete="new-password" />
            </UFormField>
          </div>
          <div class="flex justify-end">
            <UButton :loading="savingPwd" :disabled="!passwordForm.password" @click="savePassword">
              Cambiar contraseña
            </UButton>
          </div>
        </div>
      </UCard>

    <template v-if="data">
      <!-- Account info (read-only) -->
      <UCard>
        <template #header>
          <p class="font-semibold">Cuenta</p>
        </template>
        <div class="grid grid-cols-2 gap-4 text-sm max-w-2xl">
          <div>
            <p class="text-gray-500">Identificador (slug)</p>
            <p class="font-mono font-medium">{{ data.slug }}</p>
          </div>
          <div>
            <p class="text-gray-500">Plan</p>
            <UBadge color="primary" variant="soft">{{ planLabels[data.plan] ?? data.plan }}</UBadge>
          </div>
          <div>
            <p class="text-gray-500">Tipo</p>
            <p class="capitalize">{{ data.type === 'solo' ? 'Doctor independiente' : 'Clínica' }}</p>
          </div>
          <div>
            <p class="text-gray-500">Miembro desde</p>
            <p>{{ new Date(data.created_at).toLocaleDateString('es-MX', { year: 'numeric', month: 'long', day: 'numeric' }) }}</p>
          </div>
        </div>
      </UCard>

      <!-- Plan upgrade -->
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-rocket" class="w-4 h-4 text-slate-500" />
            <p class="font-semibold">Plan y facturación</p>
          </div>
        </template>
        <div v-if="loadingPlans" class="flex justify-center py-8">
          <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl text-sage-500" />
        </div>
        <div v-else-if="plans.length === 0" class="text-center py-6 text-sm text-slate-500">
          No hay planes disponibles. Contacta a tu administrador.
        </div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          <div
            v-for="plan in plans"
            :key="plan.slug"
            class="border rounded-xl p-4 transition-all flex flex-col"
            :class="data.plan === plan.slug
              ? 'border-sage-500 bg-sage-50 ring-2 ring-sage-500/30'
              : 'border-slate-200 hover:border-sage-300'"
          >
            <div class="flex items-baseline justify-between mb-1">
              <p class="font-bold text-slate-800">{{ plan.name }}</p>
              <span v-if="data.plan === plan.slug" class="text-[10px] font-bold text-sage-700 bg-sage-100 px-1.5 py-0.5 rounded">
                ACTUAL
              </span>
            </div>
            <p class="text-xl font-bold text-sage-700">{{ formatPlanPrice(plan) }}<span class="text-xs font-normal text-slate-400">/mes</span></p>
            <p v-if="plan.description" class="text-xs text-slate-500 mt-1 line-clamp-2">{{ plan.description }}</p>
            <ul class="mt-3 space-y-1 text-xs text-slate-600 flex-1 min-h-[110px]">
              <li v-for="f in plan.features" :key="f" class="flex items-start gap-1.5">
                <UIcon name="i-lucide-check" class="w-3.5 h-3.5 text-sage-600 flex-shrink-0 mt-0.5" />
                {{ f }}
              </li>
            </ul>
            <UButton
              size="sm"
              block
              class="mt-3"
              :variant="data.plan === plan.slug ? 'soft' : 'solid'"
              :disabled="data.plan === plan.slug || upgradingPlan"
              :loading="upgradingPlan"
              @click="changePlan(plan.slug)"
            >
              <template v-if="data.plan === plan.slug">Plan actual</template>
              <template v-else-if="Number(plan.price_monthly) === 0">Cambiar a este plan</template>
              <template v-else>
                <UIcon name="i-lucide-credit-card" class="w-3.5 h-3.5" /> Pagar con PayPal
              </template>
            </UButton>
          </div>
        </div>

        <!-- Cancelar suscripción (solo si hay subscription PayPal activa) -->
        <div v-if="data.subscription?.paypal_subscription_id" class="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-sm">
          <div>
            <p class="font-medium text-slate-700">Suscripción PayPal activa</p>
            <p class="text-xs text-slate-500 font-mono">{{ data.subscription.paypal_subscription_id }}</p>
          </div>
          <UButton size="sm" variant="ghost" color="error" :loading="canceling" icon="i-lucide-x-circle" @click="cancelSubscription">
            Cancelar suscripción
          </UButton>
        </div>
      </UCard>

      <!-- Editable settings -->
      <UCard>
        <template #header>
          <p class="font-semibold">General</p>
        </template>
        <form class="space-y-5 max-w-2xl" @submit.prevent="save">
          <UFormField label="Nombre del consultorio / clínica">
            <UInput v-model="name" placeholder="Mi clínica" />
          </UFormField>

          <UFormField label="Zona horaria">
            <USelect v-model="timezone" :options="timezoneOptions" value-key="value" label-key="label" />
          </UFormField>

          <UFormField label="Color principal (branding)">
            <div class="flex gap-3 items-center">
              <input
                v-model="primaryColor"
                type="color"
                class="h-9 w-14 rounded cursor-pointer border border-gray-200"
              />
              <UInput v-model="primaryColor" class="flex-1 font-mono" placeholder="#2563eb" />
              <span
                class="w-8 h-8 rounded-full border border-gray-200 flex-shrink-0"
                :style="{ background: primaryColor }"
              />
            </div>
          </UFormField>

          <UFormField label="Logo" hint="Reemplaza el icono del header y footer del sitio público. Al subir/limpiar se guarda automáticamente.">
            <LogoInput v-model="logoUrl" @uploaded="saveLogo" />
          </UFormField>

          <div class="flex justify-end">
            <UButton type="submit" :loading="saving">Guardar cambios</UButton>
          </div>
        </form>
      </UCard>

      <!-- Site content (CMS) -->
      <UCard>
        <template #header>
          <button
            type="button"
            class="w-full flex items-center justify-between gap-2"
            @click="contentOpen = !contentOpen"
          >
            <div class="flex items-center gap-2">
              <UIcon name="i-lucide-file-text" class="w-4 h-4 text-slate-500" />
              <p class="font-semibold">Contenido del sitio público</p>
            </div>
            <UIcon
              :name="contentOpen ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
              class="w-4 h-4 text-slate-400"
            />
          </button>
        </template>
        <div v-show="contentOpen" class="space-y-4">
          <p class="text-sm text-slate-500">
            Edita los textos e iconos que ven tus pacientes en el sitio público
            (<code class="text-xs">{{ data.slug }}.miapp.com</code>). Los cambios se aplican al guardar.
          </p>

          <ContentEditor v-model="content" />

          <div class="flex items-center justify-between pt-3 border-t border-slate-100">
            <UButton variant="ghost" size="sm" icon="i-lucide-rotate-ccw" @click="resetContent">
              Restaurar por defecto
            </UButton>
            <UButton :loading="savingContent" icon="i-lucide-save" @click="saveContent">
              Guardar contenido
            </UButton>
          </div>
        </div>
      </UCard>
    </template>
  </div>
</template>
