<script setup lang="ts">
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'

definePageMeta({ layout: 'auth', middleware: 'tenant' })

const auth = useAuthStore()
const tenant = useTenantStore()
const toast = useToast()

const schema = toTypedSchema(z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(6, 'Mínimo 6 caracteres')
}))

const { handleSubmit, errors, defineField } = useForm({ validationSchema: schema })
const [email, emailAttrs] = defineField('email')
const [password, passwordAttrs] = defineField('password')

const loading = ref(false)
const activationBanner = ref<{ email: string; message: string } | null>(null)

const onSubmit = handleSubmit(async (values) => {
  loading.value = true
  activationBanner.value = null
  try {
    await auth.login(values.email, values.password)
    if (auth.mustChangePassword) {
      await navigateTo('/cambiar-contrasena')
    } else {
      await navigateTo('/')
    }
  }
  catch (err: any) {
    const data = err?.response?.data
    if (data?.code === 'activation_required') {
      activationBanner.value = { email: data.email ?? values.email, message: data.error ?? '' }
    } else {
      toast.add({ title: 'Email o contraseña incorrectos', color: 'error' })
    }
  }
  finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen flex">
    <!-- Left panel — branding -->
    <div class="hidden lg:flex lg:w-1/2 bg-slate-900 flex-col items-center justify-center p-12 relative overflow-hidden">
      <!-- Decorative circles -->
      <div class="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-violet-600/20 blur-3xl" />
      <div class="absolute -bottom-24 -right-24 w-96 h-96 rounded-full bg-violet-800/20 blur-3xl" />

      <div class="relative z-10 text-center">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-violet-600 shadow-2xl shadow-violet-900/60 mb-6">
          <UIcon name="i-lucide-calendar-heart" class="text-white text-3xl" />
        </div>
        <h2 class="text-3xl font-bold text-white mb-3">Agendamiento SaaS</h2>
        <p class="text-slate-400 text-sm leading-relaxed max-w-xs">
          Gestiona citas, doctores y sucursales desde un solo lugar.
        </p>
      </div>
    </div>

    <!-- Right panel — form -->
    <div class="flex-1 flex items-center justify-center bg-slate-50 px-8">
      <div class="w-full max-w-sm">
        <!-- Mobile logo -->
        <div class="lg:hidden text-center mb-8">
          <div class="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-violet-600 mb-4">
            <UIcon name="i-lucide-calendar-heart" class="text-white text-2xl" />
          </div>
        </div>

        <div class="mb-8">
          <h1 class="text-2xl font-bold text-slate-900">
            Bienvenido de vuelta
          </h1>
          <p class="text-sm text-slate-500 mt-1">
            {{ tenant.tenant?.name ?? 'Panel Admin' }} · Inicia sesión para continuar
          </p>
        </div>

        <div
          v-if="activationBanner"
          class="mb-5 p-4 rounded-xl border-l-4 bg-amber-50 border-amber-400"
        >
          <div class="flex items-start gap-3">
            <UIcon name="i-lucide-mail-warning" class="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div class="flex-1">
              <p class="text-sm font-semibold text-amber-900">Cuenta sin activar</p>
              <p class="text-xs text-amber-800 mt-1 leading-relaxed">
                Tu cuenta <strong>{{ activationBanner.email }}</strong> aún no fue activada.
                Revisá el correo y hacé click en el <strong>enlace de activación</strong>.
                Si no lo encontrás, fijate en spam.
              </p>
            </div>
          </div>
        </div>

        <form class="space-y-5" @submit.prevent="onSubmit">
          <UFormField label="Email" :error="errors.email">
            <UInput
              v-model="email"
              v-bind="emailAttrs"
              type="email"
              placeholder="doctor@clinica.com"
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
            class="w-full justify-center"
            :loading="loading"
          >
            Iniciar sesión
          </UButton>
        </form>
      </div>
    </div>
  </div>
</template>
