<script setup lang="ts">
definePageMeta({ layout: 'auth', middleware: ['tenant', 'auth'] })

const auth = useAuthStore()
const { apiFetch } = useApi()
const toast = useToast()

const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const errorMsg = ref('')

async function onSubmit() {
  errorMsg.value = ''
  if (newPassword.value.length < 8) {
    errorMsg.value = 'La contraseña debe tener al menos 8 caracteres.'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    errorMsg.value = 'Las contraseñas no coinciden.'
    return
  }
  loading.value = true
  try {
    await apiFetch('/accounts/me/', { method: 'PATCH', body: { password: newPassword.value } })
    auth.mustChangePassword = false
    toast.add({ title: 'Contraseña actualizada', color: 'primary' })
    await navigateTo('/')
  }
  catch {
    errorMsg.value = 'No se pudo guardar la nueva contraseña. Probá de nuevo.'
  }
  finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-50 px-8">
    <div class="w-full max-w-md">
      <div class="bg-white rounded-2xl p-10 border border-slate-200 shadow-sm">
        <div class="w-14 h-14 rounded-full mx-auto mb-5 flex items-center justify-center bg-violet-100">
          <UIcon name="i-lucide-key-round" class="w-7 h-7 text-violet-600" />
        </div>
        <h1 class="text-2xl font-bold text-slate-900 text-center mb-2">Cambia tu contraseña</h1>
        <p class="text-sm text-slate-500 text-center mb-6 leading-relaxed">
          Tu contraseña actual es temporal. Por seguridad, define una nueva antes de continuar.
        </p>

        <form class="space-y-4" @submit.prevent="onSubmit">
          <UFormField label="Nueva contraseña" hint="Mínimo 8 caracteres">
            <UInput
              v-model="newPassword"
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

          <p v-if="errorMsg" class="text-sm text-rose-600">{{ errorMsg }}</p>

          <UButton type="submit" size="lg" class="w-full justify-center" :loading="loading">
            Guardar y entrar
          </UButton>
        </form>
      </div>
    </div>
  </div>
</template>
