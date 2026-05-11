<script setup lang="ts">
const auth = useAuthStore()
const toast = useToast()

const config = useRuntimeConfig()
const fileInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
const removing = ref(false)
const previewUrl = ref<string | null>(null)

const currentUrl = computed(() => previewUrl.value ?? auth.user?.profile_picture_url ?? null)

async function onPick() {
  fileInput.value?.click()
}

async function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  uploading.value = true
  // Mostrar preview inmediato
  const reader = new FileReader()
  reader.onload = ev => { previewUrl.value = ev.target?.result as string }
  reader.readAsDataURL(file)

  try {
    const fd = new FormData()
    fd.append('image', file)
    const { $api } = useNuxtApp()
    const res = await $api.post<{ profile_picture_url: string | null }>(
      `${config.public.apiBase}/accounts/me/profile-picture/`,
      fd
    )
    if (auth.user) {
      auth.user = { ...auth.user, profile_picture_url: res.data.profile_picture_url }
    }
    previewUrl.value = res.data.profile_picture_url
    toast.add({ title: 'Foto de perfil actualizada', color: 'primary' })
  }
  catch {
    toast.add({ title: 'No se pudo subir la foto', color: 'error' })
    previewUrl.value = null
  }
  finally {
    uploading.value = false
    if (input) input.value = ''
  }
}

async function removePicture() {
  if (!currentUrl.value) return
  removing.value = true
  try {
    const { $api } = useNuxtApp()
    await $api.delete(`${config.public.apiBase}/accounts/me/profile-picture/`)
    if (auth.user) {
      auth.user = { ...auth.user, profile_picture_url: null }
    }
    previewUrl.value = null
    toast.add({ title: 'Foto eliminada', color: 'primary' })
  }
  catch {
    toast.add({ title: 'No se pudo eliminar la foto', color: 'error' })
  }
  finally {
    removing.value = false
  }
}

const initials = computed(() => {
  const name = auth.user?.first_name || auth.user?.email || '?'
  return name[0]?.toUpperCase() ?? '?'
})
</script>

<template>
  <UCard>
    <template #header>
      <div class="flex items-center justify-between">
        <p class="font-semibold text-slate-800">Mi perfil</p>
      </div>
    </template>

    <div class="flex items-center gap-5">
      <!-- Avatar preview -->
      <div class="w-20 h-20 rounded-full overflow-hidden bg-violet-100 flex items-center justify-center text-2xl font-bold text-violet-700 ring-2 ring-white shadow-sm flex-shrink-0">
        <img v-if="currentUrl" :src="currentUrl" :alt="auth.user?.first_name ?? ''" class="w-full h-full object-cover">
        <span v-else>{{ initials }}</span>
      </div>

      <!-- Info + actions -->
      <div class="flex-1 min-w-0">
        <p class="font-semibold text-slate-800">{{ auth.user?.first_name }} {{ auth.user?.last_name }}</p>
        <p class="text-sm text-slate-500 truncate">{{ auth.user?.email }}</p>
        <p class="text-xs text-slate-400 mt-1">
          Esta foto se muestra cuando atendés a clientes en el chat de soporte.
        </p>

        <div class="flex items-center gap-2 mt-3">
          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            class="hidden"
            @change="onFileChange"
          >
          <UButton
            size="sm"
            variant="outline"
            icon="i-lucide-upload"
            :loading="uploading"
            @click="onPick"
          >
            {{ currentUrl ? 'Cambiar foto' : 'Subir foto' }}
          </UButton>
          <UButton
            v-if="currentUrl"
            size="sm"
            variant="ghost"
            color="error"
            icon="i-lucide-trash-2"
            :loading="removing"
            @click="removePicture"
          >
            Quitar
          </UButton>
        </div>
      </div>
    </div>
  </UCard>
</template>
