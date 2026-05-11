<script setup lang="ts">
definePageMeta({ layout: 'auth', middleware: 'tenant' })

const route = useRoute()
const { apiFetch } = useApi()

const status = ref<'loading' | 'success' | 'error'>('loading')
const result = ref<{ tenant_name?: string; email?: string; already_active?: boolean } | null>(null)
const errorMessage = ref<string | null>(null)

onMounted(async () => {
  try {
    const res = await apiFetch<{
      activated: boolean
      already_active: boolean
      tenant_slug: string
      tenant_name: string
      email: string
    }>(`/accounts/activate/${route.params.token}/`, { method: 'POST' })
    result.value = res
    status.value = 'success'
  }
  catch (err: any) {
    errorMessage.value = err?.response?.data?.error ?? 'No se pudo activar la cuenta. El enlace puede haber expirado o ser inválido.'
    status.value = 'error'
  }
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-50 px-8">
    <div class="w-full max-w-md">

      <!-- Loading -->
      <div v-if="status === 'loading'" class="bg-white rounded-2xl p-10 text-center border border-slate-200 shadow-sm">
        <UIcon name="i-lucide-loader-2" class="w-10 h-10 mx-auto mb-4 text-violet-500 animate-spin" />
        <p class="text-sm text-slate-600">Activando tu cuenta…</p>
      </div>

      <!-- Success -->
      <div v-else-if="status === 'success'" class="bg-white rounded-2xl p-10 text-center border border-slate-200 shadow-sm">
        <div class="w-16 h-16 rounded-full mx-auto mb-5 flex items-center justify-center bg-emerald-100">
          <UIcon name="i-lucide-check" class="w-8 h-8 text-emerald-600" />
        </div>
        <h1 class="text-2xl font-bold text-slate-900 mb-2">
          {{ result?.already_active ? '¡Tu cuenta ya estaba activa!' : '¡Cuenta activada!' }}
        </h1>
        <p class="text-sm text-slate-600 mb-6 leading-relaxed">
          Bienvenido a <strong class="text-slate-800">{{ result?.tenant_name }}</strong>.<br>
          Ya podés iniciar sesión con <strong>{{ result?.email }}</strong> y la contraseña que recibiste por correo.
        </p>
        <NuxtLink to="/login">
          <UButton size="lg" class="w-full justify-center" icon="i-lucide-log-in">
            Ir a iniciar sesión
          </UButton>
        </NuxtLink>
      </div>

      <!-- Error -->
      <div v-else class="bg-white rounded-2xl p-10 text-center border border-slate-200 shadow-sm">
        <div class="w-16 h-16 rounded-full mx-auto mb-5 flex items-center justify-center bg-rose-100">
          <UIcon name="i-lucide-x" class="w-8 h-8 text-rose-600" />
        </div>
        <h1 class="text-2xl font-bold text-slate-900 mb-2">No se pudo activar</h1>
        <p class="text-sm text-slate-600 mb-6 leading-relaxed">{{ errorMessage }}</p>
        <NuxtLink to="/login">
          <UButton variant="outline" size="lg" class="w-full justify-center">
            Ir al login
          </UButton>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>
