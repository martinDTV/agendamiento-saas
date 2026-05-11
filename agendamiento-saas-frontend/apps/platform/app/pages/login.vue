<script setup lang="ts">
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'

definePageMeta({ layout: 'auth' })

const auth = usePlatformAuthStore()
const settings = usePlatformSettingsStore()
const toast = useToast()

const schema = toTypedSchema(z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(6, 'Mínimo 6 caracteres')
}))

const { handleSubmit, errors, defineField } = useForm({ validationSchema: schema })
const [email, emailAttrs] = defineField('email')
const [password, passwordAttrs] = defineField('password')
const loading = ref(false)

const onSubmit = handleSubmit(async (values) => {
  loading.value = true
  try {
    await auth.login(values.email, values.password)
    await navigateTo('/')
  } catch (e: unknown) {
    const err = e as { response?: { status?: number; data?: { error?: string } } }
    const msg = err.response?.status === 403
      ? 'No tienes acceso a la plataforma.'
      : err.response?.data?.error ?? 'Credenciales inválidas'
    toast.add({ title: msg, color: 'error' })
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen flex">
    <!-- Left panel — branding -->
    <div class="hidden lg:flex lg:w-1/2 bg-slate-900 flex-col items-center justify-center p-12 relative overflow-hidden">
      <!-- Decorative circles -->
      <div class="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-primary-600/20 blur-3xl" />
      <div class="absolute -bottom-24 -right-24 w-96 h-96 rounded-full bg-primary-800/20 blur-3xl" />

      <div class="relative z-10 text-center">
        <div v-if="settings.settings.logo_url" class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white shadow-2xl shadow-primary-900/60 mb-6 overflow-hidden">
          <img :src="settings.settings.logo_url" alt="logo" class="w-full h-full object-contain" @error="($event.target as HTMLImageElement).style.display = 'none'">
        </div>
        <div v-else class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary-600 shadow-2xl shadow-primary-900/60 mb-6">
          <UIcon name="i-lucide-shield" class="text-white text-3xl" />
        </div>
        <h2 class="text-3xl font-bold text-white mb-3">{{ settings.settings.platform_name }}</h2>
        <p class="text-slate-400 text-sm leading-relaxed max-w-xs">
          Panel de super administrador. Gestiona tenants, planes y configuración global.
        </p>
      </div>
    </div>

    <!-- Right panel — form -->
    <div class="flex-1 flex items-center justify-center bg-slate-50 px-8">
      <div class="w-full max-w-sm">
        <!-- Mobile logo -->
        <div class="lg:hidden text-center mb-8">
          <div class="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary-600 mb-4">
            <UIcon name="i-lucide-shield" class="text-white text-2xl" />
          </div>
        </div>

        <div class="mb-8">
          <h1 class="text-2xl font-bold text-slate-900">
            Bienvenido de vuelta
          </h1>
          <p class="text-sm text-slate-500 mt-1">
            Acceso de super administrador · Inicia sesión para continuar
          </p>
        </div>

        <form class="space-y-5" @submit.prevent="onSubmit">
          <UFormField label="Email" :error="errors.email">
            <UInput
              v-model="email"
              v-bind="emailAttrs"
              type="email"
              placeholder="superadmin@plataforma.com"
              autocomplete="email"
              size="lg"
              class="w-full"
            />
          </UFormField>

          <UFormField label="Contraseña" :error="errors.password">
            <UInput
              v-model="password"
              v-bind="passwordAttrs"
              type="password"
              placeholder="••••••••"
              autocomplete="current-password"
              size="lg"
              class="w-full"
            />
          </UFormField>

          <UButton
            type="submit"
            size="lg"
            class="w-full justify-center bg-primary-600 hover:bg-primary-700"
            :loading="loading"
          >
            Iniciar sesión
          </UButton>
        </form>

        <p class="text-center text-xs text-slate-400 mt-8">
          Solo superusuarios. Los admins de tenants deben usar su panel de tenant.
        </p>
      </div>
    </div>
  </div>
</template>
