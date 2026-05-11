<script setup lang="ts">
definePageMeta({ layout: 'auth', middleware: 'tenant' })

const route = useRoute()
const auth = useAuthStore()

const status = ref<'idle' | 'submitting' | 'success' | 'error'>('idle')
const errorMessage = ref<string | null>(null)
const result = ref<{ tenant_name?: string; role?: string; created?: boolean } | null>(null)

const password = ref('')
const confirmPassword = ref('')

async function acceptInvitation() {
  if (status.value === 'submitting') return
  errorMessage.value = null

  if (password.value && password.value.length < 8) {
    errorMessage.value = 'La contraseña debe tener al menos 8 caracteres.'
    return
  }
  if (password.value && password.value !== confirmPassword.value) {
    errorMessage.value = 'Las contraseñas no coinciden.'
    return
  }

  status.value = 'submitting'
  try {
    const config = useRuntimeConfig()
    const url = `${config.public.apiBase}/accounts/invitations/accept/${route.params.token}/`
    const res = await $fetch<{
      access: string
      refresh: string
      created: boolean
      tenant: { name: string; slug: string }
    }>(url, {
      method: 'POST',
      body: password.value ? { password: password.value } : {}
    })

    auth.setTokens({ access: res.access, refresh: res.refresh })
    auth.mustChangePassword = false
    await auth.fetchMe()
    result.value = {
      tenant_name: res.tenant.name,
      created: res.created
    }
    status.value = 'success'
    setTimeout(() => navigateTo('/'), 1800)
  }
  catch (err: any) {
    errorMessage.value = err?.data?.error
                      ?? err?.response?._data?.error
                      ?? 'No se pudo aceptar la invitación. El enlace puede haber expirado o ser inválido.'
    status.value = 'error'
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-50 px-8">
    <div class="w-full max-w-md">

      <!-- Idle / Form -->
      <div v-if="status === 'idle' || status === 'submitting'" class="bg-white rounded-2xl p-10 border border-slate-200 shadow-sm">
        <div class="w-14 h-14 rounded-full mx-auto mb-5 flex items-center justify-center bg-emerald-100">
          <UIcon name="i-lucide-mail-check" class="w-7 h-7 text-emerald-600" />
        </div>
        <h1 class="text-2xl font-bold text-slate-900 text-center mb-2">Aceptar invitación</h1>
        <p class="text-sm text-slate-500 text-center mb-6 leading-relaxed">
          Definí una contraseña para tu cuenta y aceptá la invitación.
          Si ya tenías cuenta, dejá los campos vacíos y solo se vinculará con esta empresa.
        </p>

        <form class="space-y-4" @submit.prevent="acceptInvitation">
          <UFormField label="Contraseña (opcional si ya tenés cuenta)" hint="Mínimo 8 caracteres">
            <UInput
              v-model="password"
              type="password"
              autocomplete="new-password"
              size="lg"
              class="w-full"
            />
          </UFormField>

          <UFormField label="Confirmar contraseña">
            <UInput
              v-model="confirmPassword"
              type="password"
              autocomplete="new-password"
              size="lg"
              class="w-full"
            />
          </UFormField>

          <p v-if="errorMessage" class="text-sm text-rose-600">{{ errorMessage }}</p>

          <UButton
            type="submit"
            size="lg"
            class="w-full justify-center"
            :loading="status === 'submitting'"
          >
            Aceptar invitación
          </UButton>
        </form>
      </div>

      <!-- Success -->
      <div v-else-if="status === 'success'" class="bg-white rounded-2xl p-10 text-center border border-slate-200 shadow-sm">
        <div class="w-16 h-16 rounded-full mx-auto mb-5 flex items-center justify-center bg-emerald-100">
          <UIcon name="i-lucide-check" class="w-8 h-8 text-emerald-600" />
        </div>
        <h1 class="text-2xl font-bold text-slate-900 mb-2">¡Bienvenido!</h1>
        <p class="text-sm text-slate-600 leading-relaxed">
          Te uniste a <strong>{{ result?.tenant_name }}</strong>.
          Te llevamos al panel…
        </p>
      </div>

      <!-- Error -->
      <div v-else class="bg-white rounded-2xl p-10 text-center border border-slate-200 shadow-sm">
        <div class="w-16 h-16 rounded-full mx-auto mb-5 flex items-center justify-center bg-rose-100">
          <UIcon name="i-lucide-x" class="w-8 h-8 text-rose-600" />
        </div>
        <h1 class="text-2xl font-bold text-slate-900 mb-2">No se pudo aceptar</h1>
        <p class="text-sm text-slate-600 leading-relaxed">{{ errorMessage }}</p>
        <NuxtLink to="/login" class="inline-block mt-6">
          <UButton variant="outline">Ir al login</UButton>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>
